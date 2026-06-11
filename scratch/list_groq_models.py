import os
from groq import Groq

# Load env variables from .env
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

client = Groq()
try:
    models = client.models.list()
    for model in models.data:
        print(model.id)
except Exception as e:
    print(str(e))
