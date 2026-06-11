import os
import time
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from google.genai import types

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
    """Initializes the Gemini API Client using environment variable."""
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

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing. Please set GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)


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
    """
    Executes a multi-turn agent flow:
    1. Plan distinct angles for the target post count.
    2. Draft each option incorporating user constraints.
    3. Review drafts, apply buzzword-scrubbing & safety checks, and format the output.
    """
    start_time = time.time()
    
    # Initialize variables for token tracking
    total_input_tokens = 0
    total_output_tokens = 0
    latency_breakdown = {}
    
    try:
        client = get_client()
    except Exception as e:
        return {
            "success": False,
            "error": f"API initialization failed: {str(e)}"
        }

    # Model choice with robust fallback
    model_name = "gemini-2.5-flash"
    fallback_model_name = "gemini-2.0-flash"
    
    # Step 1: PLANNING
    step1_start = time.time()
    plan_prompt = f"""
    You are an expert LinkedIn growth strategist.
    The user wants to generate {count} posts about the topic: "{topic}".
    Target Audience: {audience}
    Tone Persona: {tone}
    Reference Examples (if any): "{examples}"

    Create {count} distinct hooks/strategies for these posts. Ensure they are highly differentiated:
    - One should focus on a story-driven approach (e.g. personal experience, case study format).
    - One should be highly educational/structured (e.g. listicle, framework breakdown).
    - One should be contrarian, bold, or query-based to drive discussion.
    """
    
    try:
        try:
            plan_response = client.models.generate_content(
                model=model_name,
                contents=plan_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PlanningResponse,
                    temperature=0.7
                )
            )
        except Exception as primary_error:
            # Fallback if primary model is overloaded (e.g. 503)
            print(f"Primary model {model_name} failed: {str(primary_error)}. Retrying with fallback {fallback_model_name}...")
            model_name = fallback_model_name
            plan_response = client.models.generate_content(
                model=model_name,
                contents=plan_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PlanningResponse,
                    temperature=0.7
                )
            )
        
        # Parse planning
        plan_data = json.loads(plan_response.text)
        latency_breakdown["planning"] = round(time.time() - step1_start, 2)
        if plan_response.usage_metadata:
            total_input_tokens += plan_response.usage_metadata.prompt_token_count
            total_output_tokens += plan_response.usage_metadata.candidates_token_count
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Planning step failed (tried fallback {model_name}): {str(e)}"
        }


    # Step 2: DRAFTING
    step2_start = time.time()
    drafting_prompt = f"""
    You are an expert copywriter. Take these planned outlines and write high-converting LinkedIn post drafts.
    
    Topic: "{topic}"
    Target Audience: {audience}
    Tone Persona: {tone}
    Language: {language}
    Length Guideline: {length} (short = <100 words, medium = 100-250 words, long = 250-400 words)
    Call To Action (CTA) requirement: "{cta}"
    
    Outlines planned:
    {json.dumps(plan_data["outlines"], indent=2)}
    
    Draft each post. Follow these LinkedIn-specific guidelines:
    - Open with a compelling 1-2 line hook.
    - Use clear, single-line spacing between paragraphs to prevent text walls.
    - Write in a professional yet conversational voice.
    - Keep bullet points readable.
    - Do not use weird markdown fonts (like bolding Unicode text); standard text only.
    """
    
    try:
        draft_response = client.models.generate_content(
            model=model_name,
            contents=drafting_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DraftingResponse,
                temperature=0.8
            )
        )
        draft_data = json.loads(draft_response.text)
        latency_breakdown["drafting"] = round(time.time() - step2_start, 2)
        if draft_response.usage_metadata:
            total_input_tokens += draft_response.usage_metadata.prompt_token_count
            total_output_tokens += draft_response.usage_metadata.candidates_token_count
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Drafting step failed: {str(e)}"
        }

    # Step 3: GUARDRAILS & REFINEMENT
    step3_start = time.time()
    refinement_prompt = f"""
    You are an editor. Perform a quality guardrail review on the following drafts.
    
    Drafts:
    {json.dumps(draft_data["posts"], indent=2)}
    
    Tasks:
    1. Filter and block any profanity, illegal claims, or hate speech (set safety_check_passed=false if failed).
    2. Remove cliché, robotic AI transition phrases and overused buzzwords (e.g. "In today's fast-paced world", "delve", "testament").
    3. Ensure clean formatting (clean line breaks, logical hook structure).
    """
    
    try:
        refine_response = client.models.generate_content(
            model=model_name,
            contents=refinement_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RefinementResponse,
                temperature=0.3
            )
        )
        refine_data = json.loads(refine_response.text)
        latency_breakdown["refinement"] = round(time.time() - step3_start, 2)
        if refine_response.usage_metadata:
            total_input_tokens += refine_response.usage_metadata.prompt_token_count
            total_output_tokens += refine_response.usage_metadata.candidates_token_count
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Guardrails / refinement step failed: {str(e)}"
        }

    # Compile the final outputs
    final_posts = []
    refined_map = {item["id"]: item for item in refine_data["refined_posts"]}
    
    for post in draft_data["posts"]:
        p_id = post["id"]
        ref = refined_map.get(p_id, {})
        
        # Apply secondary string-based cleaning for extra robustness
        clean_text = clean_buzzwords(ref.get("refined_post_text", post["post_text"]))
        
        final_posts.append({
            "id": p_id,
            "original_draft": post["post_text"],
            "post_text": clean_text,
            "suggested_hashtags": post["suggested_hashtags"],
            "call_to_action": post["call_to_action"],
            "justification": post["justification"],
            "safety_passed": ref.get("safety_check_passed", True),
            "refinement_notes": ref.get("refinement_notes", "Cleaned buzzwords and formatted for reading.")
        })
        
    total_latency = round(time.time() - start_time, 2)
    
    # Calculate costs (Gemini 2.5 Flash prices: $0.075/1M input, $0.30/1M output tokens)
    input_cost = (total_input_tokens / 1_000_000) * 0.075
    output_cost = (total_output_tokens / 1_000_000) * 0.30
    total_cost = round(input_cost + output_cost, 6)

    return {
        "success": True,
        "posts": final_posts,
        "metadata": {
            "model": model_name,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "estimated_cost_usd": total_cost,
            "total_latency_seconds": total_latency,
            "latency_breakdown": latency_breakdown
        }
    }
