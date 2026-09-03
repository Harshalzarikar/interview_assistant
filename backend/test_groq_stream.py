import asyncio
from dotenv import load_dotenv
load_dotenv('.env')

from livekit.plugins import groq
from livekit.agents.llm import ChatContext, ChatMessage

async def main():
    llm = groq.LLM(model="openai/gpt-oss-20b")
    ctx = ChatContext()
    ctx.messages().append(ChatMessage(role="user", content=["Hello!"]))
    
    print("Testing stream...")
    try:
        stream = llm.chat(chat_ctx=ctx)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end='', flush=True)
        print("\nDone!")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
