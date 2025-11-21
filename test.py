import os
from dotenv import load_dotenv

load_dotenv()
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:20] if os.getenv("OPENAI_API_KEY") else "NOT SET")
print("OPENAI_CHAT_MODEL:", os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"))