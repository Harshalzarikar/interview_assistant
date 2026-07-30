import asyncio
import os
import httpx

async def fetch_system_prompt(interviewer_id: str, candidate_name: str = "Candidate", language: str = "en") -> str:
    """Fetch the interviewer's system prompt from the API."""
    api_url = os.getenv("API_URL", "https://interview-assistant-795o.onrender.com").rstrip("/")
    print(f"Attempting to fetch prompt for '{interviewer_id}' from {api_url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{api_url}/api/interviewer/{interviewer_id}/prompt",
                params={"candidate_name": candidate_name, "language": language},
                timeout=15.0,
            )
            resp.raise_for_status()
            print("Successfully fetched custom prompt.")
            return resp.json()["prompt"]
    except Exception as e:
        print(f"Could not fetch prompt for {interviewer_id}: {type(e).__name__} - {e}")

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

async def main():
    print("=== Testing Successful API Call ===")
    prompt = await fetch_system_prompt("priya", "Harshal", "en")
    print(f"\nPROMPT PREVIEW:\n{prompt[:150]}...\n")
    
    print("=== Testing Successful API Call (Hindi) ===")
    prompt = await fetch_system_prompt("sneha", "Harshal", "hi")
    print(f"\nPROMPT PREVIEW:\n{prompt[:150]}...\n")
    
    print("=== Testing Fallback (Simulated API Failure) ===")
    os.environ["API_URL"] = "http://localhost:9999"  # Force a connection error
    prompt = await fetch_system_prompt("arjun", "Harshal", "en")
    print(f"\nPROMPT PREVIEW:\n{prompt[:150]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
