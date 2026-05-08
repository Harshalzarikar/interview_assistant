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
from livekit.api import AccessToken, VideoGrants

# Always load .env from the same directory as this file
load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="AI Interview Platform", version="1.0.0")

# CORS - allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
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


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str
    interviewer: dict


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

    # Create unique room
    room_name = f"interview-{req.interviewer_id}-{uuid.uuid4().hex[:8]}"

    # Build LiveKit token
    token = (
        AccessToken(API_KEY, API_SECRET)
        .with_identity(req.candidate_email or req.candidate_name)
        .with_name(req.candidate_name)
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
async def get_system_prompt(interviewer_id: str, candidate_name: str = "Candidate"):
    """Return the system prompt for an interviewer (used by agent)."""
    base_prompt = SYSTEM_PROMPTS.get(interviewer_id)
    if not base_prompt:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    
    # Inject candidate name into the prompt
    full_prompt = f"{base_prompt}\n\nThe candidate's name is {candidate_name}. Please greet them by name."
    
    return {"prompt": full_prompt, "interviewer_id": interviewer_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
