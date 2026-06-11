import os
from google import genai

# Load env variables from .env
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

client = genai.Client()
try:
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents="Hello, write a short sentence.",
    )
    print("SUCCESS!")
    print(response.text)
except Exception as e:
    print("ERROR OCCURRED:")
    print(str(e))
