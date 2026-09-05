"""
AI Interview Agent - LiveKit Agent Worker (v1.5.x API)
Connects as an AI participant in the interview room.
Uses: Deepgram STT → Groq LLM → Cartesia TTS
"""

import asyncio
import logging
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv(Path(__file__).parent / ".env")

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "agent.log"),
        logging.StreamHandler()
    ]
)

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    JobExecutorType,
    cli,
    AgentSession,
)
from livekit.agents.voice import Agent
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import deepgram, groq, cartesia

logger = logging.getLogger("interview-agent")


async def fetch_system_prompt(interviewer_id: str, candidate_name: str = "Candidate", job_title: str = "", job_description: str = "", language: str = "en") -> str:
    """Fetch the interviewer's system prompt from the API."""
    api_url = os.getenv("API_URL", "https://interview-assistant-795o.onrender.com").rstrip("/")
    logger.info(f"Attempting to fetch prompt for '{interviewer_id}' from {api_url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{api_url}/api/interviewer/{interviewer_id}/prompt",
                params={"candidate_name": candidate_name, "job_title": job_title, "job_description": job_description, "language": language},
                timeout=15.0,
            )
            resp.raise_for_status()
            logger.info("Successfully fetched custom prompt.")
            return resp.json()["prompt"]
    except Exception as e:
        logger.error(f"Could not fetch prompt for {interviewer_id}: {type(e).__name__} - {e}")

    # Fallback generic prompt
    lang_instruction = "IMPORTANT: Conduct the entire interview in Hindi. Speak naturally and clearly in Hindi." if language == "hi" else ""
    return (
        f"You are a professional AI interviewer named {interviewer_id.capitalize()}. Conduct a warm, engaging interview. "
        f"The candidate's name is {candidate_name}. "
        f"Start with a brief introduction, ask relevant questions for the role, "
        "listen carefully to answers, and ask thoughtful follow-ups. "
        "Keep your responses concise and conversational - this is a voice interview. "
        f"After about 7 minutes, provide brief constructive feedback and close the interview. {lang_instruction}"
    )


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint - runs when a candidate joins the interview room."""

    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Extract candidate name and job metadata from remote participants (v1.5 API uses remote_participants)
    candidate_name = "Candidate"
    job_title = ""
    job_description = ""
    for participant in ctx.room.remote_participants.values():
        candidate_name = participant.name or participant.identity
        if participant.metadata:
            try:
                meta = json.loads(participant.metadata)
                job_title = meta.get("job_title", "")
                job_description = meta.get("job_description", "")
            except:
                pass
        break

    # If room is empty, wait for first participant to join
    if candidate_name == "Candidate":
        try:
            participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=30)
            candidate_name = participant.name or participant.identity
            if participant.metadata:
                try:
                    meta = json.loads(participant.metadata)
                    job_title = meta.get("job_title", "")
                    job_description = meta.get("job_description", "")
                except:
                    pass
        except asyncio.TimeoutError:
            logger.warning("No participant joined within 30s, using default name")

    logger.info(f"Candidate name: {candidate_name}, Job: {job_title}")

    # Extract language and interviewer ID from room name (format: interview-{language}-{id}-{uuid})
    parts = ctx.room.name.split("-")
    language = parts[1] if len(parts) >= 4 else "en"
    interviewer_id = parts[2] if len(parts) >= 4 else "priya"

    # Fetch personalized system prompt
    system_prompt = await fetch_system_prompt(interviewer_id, candidate_name, job_title, job_description, language)

    # Configure STT and TTS based on language
    if language == "hi":
        stt_model = deepgram.STT(model="nova-2", language="hi")
        # Ensure CARTESIA_API_KEY is in .env or environment variables
        tts_model = cartesia.TTS(model="sonic-multilingual", voice="a0e99841-438c-4a64-b3a0-ea1481cb31e0") # A natural-sounding voice
    else:
        stt_model = deepgram.STT(model="nova-2", language="en")
        
        # Select male voice based on interviewer ID
        if interviewer_id == "alex":
            voice = "aura-orion-en" # US Male
        elif interviewer_id == "harry":
            voice = "aura-arcas-en" # Deep US Male
        else:
            voice = "aura-orion-en"
            
        tts_model = deepgram.TTS(model=voice)

    # Build the AgentSession with STT, LLM, TTS (v1.5.x API)
    session = AgentSession(
        stt=stt_model,
        llm=groq.LLM(model="openai/gpt-oss-20b"),
        tts=tts_model,
    )

    # Build a ChatContext with a dummy user message to satisfy Groq models
    initial_ctx = ChatContext()
    initial_ctx.add_message(role="user", content="Hi, I am ready for the interview!")

    # Create Agent with instructions and the initial context
    agent = Agent(instructions=system_prompt, chat_ctx=initial_ctx)

    # Start the session in the room (agent is first positional arg, room is keyword-only)
    await session.start(agent, room=ctx.room)

    # Greet the candidate
    greeting = f"Greet {candidate_name} warmly by name, introduce yourself"
    if job_title:
        greeting += f", and mention you will be interviewing them for the {job_title} role today."
    else:
        greeting += ", and ask how they are doing today to kick off the interview."
        
    await session.generate_reply(
        instructions=greeting
    )

    # Keep alive for the duration of the interview (10 minutes max)
    await asyncio.sleep(60 * 10)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            job_executor_type=JobExecutorType.THREAD,
            num_idle_processes=0,
            load_threshold=1.0,
        )
    )
