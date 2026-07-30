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

load_dotenv(Path(__file__).parent / ".env")

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    AgentSession,
)
from livekit.agents.voice import Agent
from livekit.plugins import deepgram, groq, cartesia

logger = logging.getLogger("interview-agent")


async def fetch_system_prompt(interviewer_id: str, candidate_name: str = "Candidate", language: str = "en") -> str:
    """Fetch the interviewer's system prompt from the API."""
    api_url = os.getenv("API_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{api_url}/api/interviewer/{interviewer_id}/prompt",
                params={"candidate_name": candidate_name, "language": language},
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json()["prompt"]
    except Exception as e:
        logger.warning(f"Could not fetch prompt for {interviewer_id}: {e}")

    # Fallback generic prompt
    return (
        f"You are a professional AI interviewer. Conduct a warm, engaging interview. "
        f"The candidate's name is {candidate_name}. "
        "Start with a brief introduction, ask relevant questions for the role, "
        "listen carefully to answers, and ask thoughtful follow-ups. "
        "Keep your responses concise and conversational - this is a voice interview. "
        "After about 7 minutes, provide brief constructive feedback and close the interview."
    )


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint - runs when a candidate joins the interview room."""

    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Extract candidate name from remote participants (v1.5 API uses remote_participants)
    candidate_name = "Candidate"
    for participant in ctx.room.remote_participants.values():
        candidate_name = participant.name or participant.identity
        break

    # If room is empty, wait for first participant to join
    if candidate_name == "Candidate":
        try:
            participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=30)
            candidate_name = participant.name or participant.identity
        except asyncio.TimeoutError:
            logger.warning("No participant joined within 30s, using default name")

    logger.info(f"Candidate name: {candidate_name}")

    # Extract language and interviewer ID from room name (format: interview-{language}-{id}-{uuid})
    parts = ctx.room.name.split("-")
    language = parts[1] if len(parts) >= 4 else "en"
    interviewer_id = parts[2] if len(parts) >= 4 else "priya"

    # Fetch personalized system prompt
    system_prompt = await fetch_system_prompt(interviewer_id, candidate_name, language)

    # Configure STT and TTS based on language
    if language == "hi":
        stt_model = deepgram.STT(model="nova-2", language="hi")
        # Ensure CARTESIA_API_KEY is in .env or environment variables
        tts_model = cartesia.TTS(model="sonic-multilingual", voice="a0e99841-438c-4a64-b3a0-ea1481cb31e0") # A natural-sounding voice
    else:
        stt_model = deepgram.STT(model="nova-2", language="en")
        tts_model = deepgram.TTS(model="aura-asteria-en")

    # Build the AgentSession with STT, LLM, TTS (v1.5.x API)
    session = AgentSession(
        stt=stt_model,
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=tts_model,
    )

    # Create Agent with instructions
    agent = Agent(instructions=system_prompt)

    # Start the session in the room (agent is first positional arg, room is keyword-only)
    await session.start(agent, room=ctx.room)

    # Greet the candidate
    await session.generate_reply(
        instructions=f"Greet {candidate_name} warmly by name, introduce yourself, and ask how they are doing today to kick off the interview."
    )

    # Keep alive for the duration of the interview (10 minutes max)
    await asyncio.sleep(60 * 10)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
