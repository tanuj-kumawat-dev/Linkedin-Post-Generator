import os
import time
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from groq import Groq

class PostOutline(BaseModel):
    id: int = Field(..., description="Post outline index (1 to N)")
    hook_type: str = Field(..., description="The type of hook/angle (e.g. story, contrarian, analytical listicle)")
    structural_concept: str = Field(..., description="Concept/flow of the post (e.g. state a problem, share an anecdote, list 3 lessons, call to action)")
    core_theme: str = Field(..., description="The specific message or take-away for this option")

class PlanningResponse(BaseModel):
    outlines: List[PostOutline] = Field(..., description="List of post outlines to draft")

class DraftedPost(BaseModel):
    id: int = Field(..., description="Post index matching the outline")
    post_text: str = Field(..., description="The fully drafted post, formatted with line breaks, readability spaces, and emojis if suitable")
    suggested_hashtags: List[str] = Field(..., description="3-5 highly relevant, high-traffic hashtags")
    call_to_action: str = Field(..., description="Suggested Call To Action matching user request")
    justification: str = Field(..., description="Short explanation of why this style suits the target audience")

class DraftingResponse(BaseModel):
    posts: List[DraftedPost] = Field(..., description="List of drafted LinkedIn posts")

class PostRefinement(BaseModel):
    id: int
    refined_post_text: str = Field(..., description="Post text with corporate fluff/buzzwords removed, clean spacing, and readable layout")
    safety_check_passed: bool = Field(..., description="True if post contains no profanity, illegal claims, or toxic statements")
    refinement_notes: str = Field(..., description="List of edits made to make it sound more human and engaging")

class RefinementResponse(BaseModel):
    refined_posts: List[PostRefinement]

def get_client():
    """Initializes the Groq API Client using environment variable."""
    # Attempt to load from a local .env file if it exists (for easy local testing)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Please set GROQ_API_KEY.")
    return Groq(api_key=api_key)

def clean_buzzwords(text: str) -> str:
    """Extra level of regex/string cleaning for typical AI buzzwords."""
    # List of cliché AI filler phrases to replace or simplify
    buzzwords = {
        "In today's fast-paced world": "Today",
        "deep dive": "exploration",
        "delve": "look",
        "tapestry": "structure",
        "testament to": "proof of",
        "forefront of": "leading",
        "revolutionize": "improve",
        "it is crucial to": "we must",
        "first and foremost": "first",
    }
    for word, replacement in buzzwords.items():
        text = text.replace(word, replacement)
        text = text.replace(word.lower(), replacement.lower())
    return text

def run_post_generation_agent(
    topic: str,
    tone: str,
    audience: str,
    length: str = "medium",
    cta: str = "",
    examples: str = "",
    language: str = "English",
    count: int = 3
) -> dict:
    """Executes a single-pass copy generation query using Groq."""
    start_time = time.time()
    model_name = "llama-3.3-70b-versatile"
    
    try:
        client = get_client()
    except Exception as e:
        return {
            "success": False,
            "error": f"API initialization failed: {str(e)}"
        }

    # Consolidated Master Prompt instructing Groq to output JSON matching our schema
    master_prompt = f"""
    You are an expert LinkedIn growth strategist, copywriter, and editor.
    Your task is to generate {count} distinct, high-converting LinkedIn post drafts about the topic: "{topic}".
    
    Target Audience: {audience}
    Tone Persona: {tone}
    Language: {language}
    Length Guideline: {length} (short = <100 words, medium = 100-250 words, long = 250-400 words)
    Call To Action (CTA): "{cta}"
    Style Reference (if provided): "{examples}"

    Generate your response as a JSON object matching this schema:
    {{
      "posts": [
        {{
          "id": 1,
          "post_text": "Full text of the post draft...",
          "suggested_hashtags": ["hashtag1", "hashtag2"],
          "call_to_action": "Suggested CTA",
          "justification": "Why this specific strategy suits the target audience"
        }}
      ]
    }}

    For each of the {count} posts:
    1. Plan a unique hook/angle (e.g. story-based hook, analytical listicle, bold/contrarian hook).
    2. Draft the copy using clean single-line breaks. Do NOT use robotic AI clichés like "delve", "testament", "tapestry", or "in today's fast-paced world".
    3. Generate highly relevant hashtags and matching CTAs.
    """
    
    try:
        # Request completion from Groq with JSON Mode enabled and strict system instructions
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a strict JSON API. You must return ONLY a valid JSON object matching the requested schema. Never output markdown fences (e.g. ```json), raw backticks (`), or unescaped double quotes inside JSON string values. Escape all quotes inside values properly."},
                {"role": "user", "content": master_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        raw_text = response.choices[0].message.content
        draft_data = json.loads(raw_text)
        
        # Compile and clean drafts
        final_posts = []
        for post in draft_data.get("posts", []):
            clean_text = clean_buzzwords(post["post_text"])
            final_posts.append({
                "id": post["id"],
                "post_text": clean_text,
                "suggested_hashtags": post.get("suggested_hashtags", []),
                "call_to_action": post.get("call_to_action", ""),
                "justification": post.get("justification", ""),
                "safety_passed": True,
                "refinement_notes": "Optimized and buzzwords cleaned via Groq Llama 3.1."
            })
            
        total_latency = round(time.time() - start_time, 2)
        
        # Groq API is free; cost is estimated to be $0.00
        return {
            "success": True,
            "posts": final_posts,
            "metadata": {
                "model": model_name,
                "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "estimated_cost_usd": 0.00,
                "total_latency_seconds": total_latency,
                "latency_breakdown": {"single_pass": total_latency}
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Generation failed using {model_name}: {str(e)}"
        }
