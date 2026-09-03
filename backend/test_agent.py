import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.env')

from livekit.plugins import deepgram, groq, cartesia
from livekit.agents.voice import AgentSession

async def main():
    stt_model = deepgram.STT(model="nova-2", language="en")
    tts_model = deepgram.TTS(model="aura-asteria-en")
    llm = groq.LLM(model="openai/gpt-oss-20b")
    
    print("Initializing AgentSession...")
    session = AgentSession(
        stt=stt_model,
        llm=llm,
        tts=tts_model,
    )
    print("AgentSession initialized!")

if __name__ == "__main__":
    asyncio.run(main())
