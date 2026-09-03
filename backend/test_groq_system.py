import os, requests
from dotenv import load_dotenv
load_dotenv('.env')

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def test_model(model):
    res = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
        json={
            'model': model,
            'messages': [{'role': 'system', 'content': 'You are an AI.'}, {'role': 'system', 'content': 'Say hello.'}]
        }
    )
    print(f"Model: {model}")
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}\n")

test_model("qwen/qwen3.6-27b")
test_model("groq/compound-mini")
test_model("groq/compound")
test_model("allam-2-7b")
