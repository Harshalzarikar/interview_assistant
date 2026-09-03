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
load_dotenv(Path(__file__).parent / ".env")

from contextlib import asynccontextmanager
import asyncio
from livekit.agents import WorkerOptions, JobExecutorType
from livekit.agents.worker import AgentServer
from agent import entrypoint

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
        "http://localhost:3000",
        "https://artizence-frontend.onrender.com",
        "https://interview-assistant-795o.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Interviewer Catalog ────────────────────────────────────────────────────────
INTERVIEWERS = [
    {
        "id": "priya",
        "name": "Priya",
        "role": "AI Engineer",
        "type": "Coding",
        "tags": ["Python", "ML", "System Design"],
        "duration": "7 min",
        "language": "Indian English",
        "company": "Anthropic",
        "is_new": True,
    },
    {
        "id": "sneha",
        "name": "Sneha",
        "role": "Product Manager",
        "type": "Case Study",
        "tags": ["Strategy", "Analytics", "Product Sense"],
        "duration": "7 min",
        "language": "Indian English",
        "company": "Mistral",
        "is_new": True,
    },
    {
        "id": "arjun",
        "name": "Arjun",
        "role": "Sales Executive",
        "type": "Roleplay",
        "tags": ["Cold Call", "Outreach", "Negotiation"],
        "duration": "7 min",
        "language": "Indian English",
        "company": "Groq",
        "is_new": True,
    },
    {
        "id": "kavya",
        "name": "Kavya",
        "role": "HR Business Partner",
        "type": "Conversational",
        "tags": ["Relations", "Workforce", "Culture"],
        "duration": "7 min",
        "language": "Indian English",
        "company": "Unilever",
        "is_new": False,
    },
    {
        "id": "rohan",
        "name": "Rohan",
        "role": "Backend Engineer",
        "type": "Coding",
        "tags": ["Node.js", "Django", "Databases"],
        "duration": "7 min",
        "language": "US English",
        "company": "Meesho",
        "is_new": False,
    },
    {
        "id": "meera",
        "name": "Meera",
        "role": "Data Scientist",
        "type": "Case Study",
        "tags": ["Statistics", "SQL", "Python"],
        "duration": "7 min",
        "language": "Indian English",
        "company": "Ola",
        "is_new": False,
    },
]

# ── System Prompts per Interviewer ─────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "priya": """You are Priya, a senior AI Engineer interviewer at a top tech company. 
You conduct technical coding interviews focused on Python, machine learning, and system design.
Start by warmly introducing yourself, then ask about the candidate's background.
Ask thoughtful technical questions, dive deep on ML concepts, Python coding patterns, and system design.
Be encouraging but rigorous. Give hints when candidates are stuck.
Keep responses concise and conversational - this is a voice interview.
After about 7 minutes, wrap up with constructive feedback.""",

    "sneha": """You are Sneha, a Product Manager interviewer specializing in case study interviews.
You assess product thinking, analytical skills, and strategic reasoning.
Start with a warm introduction and ask about the candidate's PM experience.
Present realistic product scenarios - metrics analysis, feature prioritization, go-to-market strategy.
Ask follow-up questions to understand their thinking process.
Keep responses concise for voice - no bullet points or markdown.
After 7 minutes, provide balanced feedback.""",

    "arjun": """You are Arjun, a Sales Director conducting a roleplay sales interview.
You test cold calling ability, objection handling, and deal closing skills.
Start by briefing the candidate on the roleplay scenario, then jump into character as a skeptical prospect.
Challenge their pitch, raise common objections like price, timing, competition.
Evaluate their energy, adaptability, and persuasion techniques.
Stay in character during the roleplay, then debrief at the end.
Keep all responses natural and conversational for voice.""",

    "kavya": """You are Kavya, an HR Business Partner conducting a behavioral interview.
You assess culture fit, leadership potential, and interpersonal skills.
Use the STAR method framework - ask about Situation, Task, Action, Result.
Topics: conflict resolution, leadership moments, failure/learning, collaboration.
Be warm, empathetic, and build rapport while professionally evaluating.
Keep responses concise and natural for voice conversation.
After 7 minutes, thank them and provide encouragement.""",

    "rohan": """You are Rohan, a Senior Backend Engineer conducting a technical interview.
You focus on Node.js, Django, databases, APIs, and system design.
Ask about past projects, dive into architecture decisions, and test problem-solving.
Include questions on REST APIs, database optimization, caching, microservices.
Be technically precise but approachable. Encourage thinking aloud.
Keep responses brief and conversational for voice format.
Wrap up with technical feedback after 7 minutes.""",

    "meera": """You are Meera, a Data Science lead conducting a technical interview.
You assess statistics, machine learning, SQL, and analytical thinking.
Ask about past data projects, statistical methods they've used, and business impact.
Include questions on A/B testing, model evaluation, feature engineering, SQL.
Be curious and collaborative - explore their reasoning process.
Keep responses concise for voice. No code unless they bring it up.
End with constructive feedback after 7 minutes.""",
}

# ── Pydantic Models ────────────────────────────────────────────────────────────
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


# ── Routes ─────────────────────────────────────────────────────────────────────
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
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    API_KEY = os.getenv("LIVEKIT_API_KEY")
    API_SECRET = os.getenv("LIVEKIT_API_SECRET")

    if not all([LIVEKIT_URL, API_KEY, API_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env",
        )

    # Find interviewer
    interviewer = next(
        (i for i in INTERVIEWERS if i["id"] == req.interviewer_id), None
    )
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    # Create unique room with language embedded
    room_name = f"interview-{req.language}-{req.interviewer_id}-{uuid.uuid4().hex[:8]}"

    # Build LiveKit token
    token = (
        AccessToken(API_KEY, API_SECRET)
        .with_identity(req.candidate_email or req.candidate_name)
        .with_name(req.candidate_name)
        .with_metadata(json.dumps({
            "job_title": req.job_title,
            "job_description": req.job_description
        }))
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .with_ttl(datetime.timedelta(hours=1))  # 1 hour TTL
        .to_jwt()
    )

    return TokenResponse(
        token=token,
        room_name=room_name,
        livekit_url=LIVEKIT_URL,
        interviewer=interviewer,
    )


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
    
    return {"prompt": full_prompt, "interviewer_id": interviewer_id}


@app.post("/api/analyze-interview")
async def analyze_interview(req: AnalyzeInterviewRequest):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    formatted_transcript = ""
    for msg in req.transcript:
        role = msg.get("speakerName", "Unknown")
        text = msg.get("text", "")
        formatted_transcript += f"{role}: {text}\n"

    prompt = f"""You are an expert HR and Technical Interview Assessor.
Analyze the following interview transcript between {req.candidate_name} and the AI Interviewer.
Provide a concise JSON response with the following keys:
- "strengths": List of 3 strong points demonstrated by the candidate (strings).
- "weaknesses": List of 3 areas of improvement (strings).
- "feedback": A short paragraph summarizing overall performance.
- "score": A score out of 10 (number).

Output STRICTLY valid JSON only, without any markdown formatting.

Transcript:
{formatted_transcript}
"""
    try:
        import httpx
        import json
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "qwen/qwen3.6-27b",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                },
                timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()
            analysis_text = data["choices"][0]["message"]["content"]
            return json.loads(analysis_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
