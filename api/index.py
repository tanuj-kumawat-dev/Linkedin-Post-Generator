from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
import os
from .agent import run_post_generation_agent

app = FastAPI(title="LinkedIn Post Generator API")

# Enable CORS for local testing/cross-origin deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerationRequest(BaseModel):
    topic: str = Field(..., description="Main topic for the posts")
    tone: str = Field("Thought Leader", description="Tone of voice")
    audience: str = Field("General Professionals", description="Target audience")
    length: str = Field("medium", description="Length constraint: short, medium, long")
    cta: Optional[str] = Field("", description="Optional Call-To-Action instruction")
    examples: Optional[str] = Field("", description="Optional text example to mimic")
    language: str = Field("English", description="Target language")
    count: int = Field(3, ge=1, le=5, description="Number of posts to generate (1 to 5)")

@app.get("/api/health")
def health_check():
    """Simple 200 OK health check endpoint required by the specifications."""
    return {"status": "ok", "message": "API is online and functioning."}

@app.post("/api/generate")
def generate_posts(req: GenerationRequest):
    """Generates LinkedIn post drafts utilizing a multi-stage agentic workflow."""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")
        
    result = run_post_generation_agent(
        topic=req.topic,
        tone=req.tone,
        audience=req.audience,
        length=req.length,
        cta=req.cta,
        examples=req.examples,
        language=req.language,
        count=req.count
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Generation failed."))
        
    return result

# Mount the static frontend directory for local development (serves /public contents at root)
public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="public")

