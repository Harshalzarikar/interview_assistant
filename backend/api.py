"""
AI Interview Platform - FastAPI Backend
Handles LiveKit token generation and session management.
"""

import os
import uuid
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import datetime
import json
from livekit.api import AccessToken, VideoGrants

# Always load .env from the same directory as this file
load_dotenv(Path(__file__).parent / ".env", override=True)

from contextlib import asynccontextmanager
import asyncio
from livekit.agents import WorkerOptions, JobExecutorType
from livekit.agents.worker import AgentServer
from agent import entrypoint
from mock_interview_store import complete_session, create_session, get_session, update_session

_agent_server = None
_worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent_server, _worker_task
    try:
        # Start LiveKit Agent inside the FastAPI process to save RAM on 512MB limit!
        worker_opts = WorkerOptions(
            entrypoint_fnc=entrypoint,
            job_executor_type=JobExecutorType.THREAD,
            num_idle_processes=0,
            load_threshold=1.0,
        )
        _agent_server = AgentServer.from_server_options(worker_opts)
        _worker_task = asyncio.create_task(_agent_server.run())
        print("LiveKit Agent Worker started in FastAPI process!")
    except Exception as e:
        print(f"Failed to start LiveKit worker: {e}")

    yield

    if _agent_server:
        await _agent_server.aclose()
    if _worker_task:
        _worker_task.cancel()

app = FastAPI(title="AI Interview Platform", version="1.0.0", lifespan=lifespan)

# CORS - allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://artizence-frontend.onrender.com",
        "https://interview-assistant-795o.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Interviewer Catalog ----------------------------------------------------
INTERVIEWERS = [
    {
        "id": "alex",
        "name": "Alex",
        "role": "Technical Lead",
        "type": "Coding",
        "tags": ["Software Engineering", "System Design", "Algorithms"],
        "duration": "10 min",
        "language": "US English",
        "company": "OpenAI",
        "is_new": True,
    },
    {
        "id": "harry",
        "name": "Harry",
        "role": "HR Business Partner",
        "type": "Conversational",
        "tags": ["Behavioral", "Culture Fit", "Leadership"],
        "duration": "10 min",
        "language": "British English",
        "company": "Google",
        "is_new": True,
    },
]

# -- System Prompts per Interviewer -----------------------------------------
SYSTEM_PROMPTS = {
    "alex": """You are Alex, a Technical Lead and Senior Software Engineer conducting a coding interview.
You focus on software engineering fundamentals, algorithms, and system design.
Start by warmly introducing yourself, then ask about the candidate's technical background.
Ask thoughtful technical questions and dive deep into architecture and problem-solving.
Be encouraging but rigorous. Give hints when candidates are stuck.
Keep responses concise and conversational - this is a voice interview.
After about 10 minutes, wrap up with constructive feedback.""",

    "harry": """You are Harry, an HR Business Partner conducting a behavioral and culture fit interview.
You assess leadership potential, teamwork, and interpersonal skills.
Start with a warm, friendly introduction and ask about their career journey.
Use the STAR method framework - ask about Situation, Task, Action, Result.
Topics: conflict resolution, learning from failure, and team collaboration.
Be warm, empathetic, and build rapport while professionally evaluating.
Keep responses concise and natural for a voice conversation.
After 10 minutes, thank them and provide encouragement.""",
}

# -- Pydantic Models ---------------------------------------------------------
class StartInterviewRequest(BaseModel):
    interviewer_id: str
    candidate_name: str
    candidate_email: str
    job_title: str = ""
    job_description: str = ""
    language: str = "en"


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str
    interviewer: dict


class AnalyzeInterviewRequest(BaseModel):
    transcript: list
    interviewer_id: str
    candidate_name: str


class CreateMockInterviewRequest(BaseModel):
    interviewer_id: str
    candidate_name: str
    candidate_email: str
    job_title: str = ""
    job_description: str = ""
    language: str = "en"


class CompleteMockInterviewRequest(BaseModel):
    transcript: list


class CreateMockInterviewRoomRequest(BaseModel):
    job_title: str
    job_description: str


class MockInterviewRoomResponse(BaseModel):
    room_id: str
    mock_interview_room_url: str
    status: str
    interviewer: dict


def _get_livekit_credentials():
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not all([livekit_url, api_key, api_secret]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env",
        )
    return livekit_url, api_key, api_secret


def _build_livekit_session(req: StartInterviewRequest):
    livekit_url, api_key, api_secret = _get_livekit_credentials()
    interviewer = next((i for i in INTERVIEWERS if i["id"] == req.interviewer_id), None)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    room_name = f"interview-{req.language}-{req.interviewer_id}-{uuid.uuid4().hex[:8]}"
    token = (
        AccessToken(api_key, api_secret)
        .with_identity(req.candidate_email or req.candidate_name)
        .with_name(req.candidate_name)
        .with_metadata(
            json.dumps(
                {
                    "job_title": req.job_title,
                    "job_description": req.job_description,
                }
            )
        )
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .with_ttl(datetime.timedelta(hours=1))
        .to_jwt()
    )
    return livekit_url, room_name, token, interviewer


def _public_session_view(record: dict) -> dict:
    """Strip LiveKit token from API responses."""
    return {
        "session_id": record["session_id"],
        "status": record["status"],
        "created_at": record.get("created_at"),
        "completed_at": record.get("completed_at"),
        "candidate_name": record.get("candidate_name"),
        "candidate_email": record.get("candidate_email"),
        "job_title": record.get("job_title"),
        "job_description": record.get("job_description"),
        "language": record.get("language"),
        "interviewer_id": record.get("interviewer_id"),
        "interviewer": record.get("interviewer"),
        "room_name": record.get("room_name"),
        "interview_link": record.get("interview_link"),
        "transcript": record.get("transcript") or [],
        "analysis": record.get("analysis"),
    }


# -- Routes -------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "AI Interview Platform API", "status": "running"}


@app.get("/api/interviewers")
async def get_interviewers():
    """Return the list of available AI interviewers."""
    return {"interviewers": INTERVIEWERS}


@app.post("/api/start-interview", response_model=TokenResponse)
async def start_interview(req: StartInterviewRequest):
    """Generate a LiveKit token and start an interview session."""
    livekit_url, room_name, token, interviewer = _build_livekit_session(req)
    return TokenResponse(
        token=token,
        room_name=room_name,
        livekit_url=livekit_url,
        interviewer=interviewer,
    )


@app.post("/api/mock-interviews")
async def create_mock_interview(req: CreateMockInterviewRequest):
    """Create a shareable mock interview link (for Postman / integrations)."""
    start_req = StartInterviewRequest(**req.model_dump())
    livekit_url, room_name, token, interviewer = _build_livekit_session(start_req)

    session_id = uuid.uuid4().hex
    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    interview_link = f"{frontend_base}/join/{session_id}"

    record = create_session(
        session_id,
        {
            "candidate_name": req.candidate_name,
            "candidate_email": req.candidate_email,
            "job_title": req.job_title,
            "job_description": req.job_description,
            "language": req.language,
            "interviewer_id": req.interviewer_id,
            "interviewer": interviewer,
            "room_name": room_name,
            "livekit_url": livekit_url,
            "token": token,
            "interview_link": interview_link,
        },
    )
    return _public_session_view(record)


@app.post("/api/mock-interview-rooms", response_model=MockInterviewRoomResponse)
async def create_mock_interview_room(req: CreateMockInterviewRoomRequest):
    """Create a mock interview room link from a job title and description."""
    start_req = StartInterviewRequest(
        interviewer_id="alex",
        candidate_name="Candidate",
        candidate_email="",
        job_title=req.job_title,
        job_description=req.job_description,
    )
    livekit_url, room_name, token, interviewer = _build_livekit_session(start_req)

    room_id = uuid.uuid4().hex
    frontend_base = (
        os.getenv("INTERVIEW_AGENT_FRONTEND_URL")
        or os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    ).rstrip("/")
    mock_interview_room_url = f"{frontend_base}/room/{room_id}"

    record = create_session(
        room_id,
        {
            "candidate_name": "Candidate",
            "candidate_email": "",
            "job_title": req.job_title,
            "job_description": req.job_description,
            "language": "en",
            "interviewer_id": "alex",
            "interviewer": interviewer,
            "room_name": room_name,
            "livekit_url": livekit_url,
            "token": token,
            "interview_link": mock_interview_room_url,
        },
    )
    return MockInterviewRoomResponse(
        room_id=record["session_id"],
        mock_interview_room_url=mock_interview_room_url,
        status=record["status"],
        interviewer=interviewer,
    )


@app.get("/api/mock-interviews/{session_id}")
async def get_mock_interview(session_id: str):
    """Return mock interview details: transcript and analysis when available."""
    record = get_session(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Mock interview not found")
    return _public_session_view(record)


@app.get("/api/mock-interviews/{session_id}/join")
async def join_mock_interview(session_id: str):
    """Return LiveKit credentials for the candidate join page."""
    record = get_session(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Mock interview not found")
    if record.get("status") == "completed":
        raise HTTPException(status_code=400, detail="This interview is already completed")

    update_session(session_id, status="in_progress")
    return {
        "session_id": session_id,
        "token": record["token"],
        "room_name": record["room_name"],
        "livekit_url": record["livekit_url"],
        "interviewer": record["interviewer"],
        "candidate_name": record.get("candidate_name"),
    }


@app.post("/api/mock-interviews/{session_id}/complete")
async def complete_mock_interview(session_id: str, req: CompleteMockInterviewRequest):
    """Save transcript, run analysis, and mark the mock interview completed."""
    record = get_session(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Mock interview not found")

    analysis = await analyze_interview(
        AnalyzeInterviewRequest(
            transcript=req.transcript,
            interviewer_id=record["interviewer_id"],
            candidate_name=record.get("candidate_name") or "Candidate",
        )
    )
    updated = complete_session(session_id, req.transcript, analysis)
    return _public_session_view(updated)


@app.get("/api/interviewer/{interviewer_id}/prompt")
async def get_system_prompt(interviewer_id: str, candidate_name: str = "Candidate", job_title: str = "", job_description: str = "", language: str = "en"):
    """Return the system prompt for an interviewer (used by agent)."""
    base_prompt = SYSTEM_PROMPTS.get(interviewer_id)
    if not base_prompt:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    full_prompt = f"{base_prompt}\n\nThe candidate's name is {candidate_name}. Please greet them by name."

    if job_title:
        full_prompt += f"\nYou are interviewing them for the role of: {job_title}."
    if job_description:
        full_prompt += f"\nHere is the job description and core requirements to focus on:\n{job_description}"

    if language == "hi":
        full_prompt += " IMPORTANT: Conduct the entire interview in Hindi. Speak naturally and clearly in Hindi."

    full_prompt += "\nIMPORTANT: Do not use any emojis, asterisks, markdown formatting, or special characters. Speak in plain conversational text."

    # Tightened pacing / clarification rules. The agent-side code also enforces
    # a hard MIN_INTERVIEW_SECONDS guard - this prompt defers to that rather
    # than trying to self-regulate duration, which small/fast LLMs are
    # unreliable at doing from prose instructions alone.
    full_prompt += (
        "\nCRITICAL RULES:"
        "\n1. Ask exactly ONE question at a time, then WAIT silently for the candidate to finish speaking."
        "\n2. If the candidate's answer seems cut off, incomplete, or doesn't make sense, "
        "ask them to clarify or continue - do NOT repeat the exact same question verbatim, "
        "and do NOT move on as if they gave a full answer."
        "\n3. Conduct at least 6-8 distinct question exchanges before wrapping up. "
        "Do not end the interview after only 2-3 exchanges even if answers are short."
        "\n4. Never end the interview yourself. You will be told explicitly when it is time to close. "
        "Until then, always ask a follow-up or a new question."
        "\n5. If an answer is vague or very short, ask a specific follow-up probing for more detail "
        "instead of moving to feedback or ending the conversation."
    )

    return {"prompt": full_prompt, "interviewer_id": interviewer_id}


ANALYSIS_MODEL = os.getenv("INTERVIEW_LLM_MODEL", "openai/gpt-oss-120b")

# Keys the frontend report expects. Used to fill in anything the model omits.
ANALYSIS_FIELDS = [
    "score",
    "readiness",
    "summary",
    "dimensions",
    "strengths",
    "weaknesses",
    "feedback",
    "recommendations",
    "question_breakdown",
]


def _fill_analysis_defaults(analysis: dict) -> dict:
    """Return the analysis with every expected key present so the UI never breaks."""
    result = {}
    for field in ANALYSIS_FIELDS:
        value = analysis.get(field)
        if value is None:
            value = [] if field in ("dimensions", "strengths", "weaknesses", "recommendations", "question_breakdown") else ""
        result[field] = value
    return result


@app.post("/api/analyze-interview")
async def analyze_interview(req: AnalyzeInterviewRequest):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    formatted_transcript = ""
    for msg in req.transcript:
        role = msg.get("speakerName", "Unknown")
        text = msg.get("text", "")
        formatted_transcript += f"{role}: {text}\n"

    prompt = f"""You are an expert HR and technical interview assessor.
Analyze the interview transcript between {req.candidate_name} and the AI interviewer.

Return STRICTLY valid JSON (no markdown, no extra text) with EXACTLY these keys:
- "score": overall score out of 10 (number).
- "readiness": one of "Interview-ready", "Nearly ready", "Needs practice".
- "summary": 2-3 sentence overview of the candidate's performance.
- "dimensions": array of exactly 5 objects, each {{"name", "score", "comment"}}, using these names in this order: "Communication", "Technical Depth", "Problem Solving", "Clarity", "Confidence". Each score is out of 10.
- "strengths": array of 3-5 specific strengths (strings).
- "weaknesses": array of 3-5 specific areas to improve (strings).
- "feedback": one paragraph of overall feedback.
- "recommendations": array of 3-5 concrete, actionable next steps.
- "question_breakdown": array with one object per main question asked, each {{"question", "rating", "comment"}} where rating is "strong", "ok", or "weak".

Rules:
- Base every point ONLY on what is in the transcript. Do not invent details.
- Be specific and refer to what the candidate actually said.

Transcript:
{formatted_transcript}
"""
    try:
        import httpx
        import json
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_api_key}"},
                json={
                    # NOTE: verify this model is still available on your account -
                    # see https://console.groq.com/docs/models
                    "model": ANALYSIS_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                    "max_tokens": 2000,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            analysis_text = data["choices"][0]["message"]["content"]
            analysis = json.loads(analysis_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

    return _fill_analysis_defaults(analysis)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)