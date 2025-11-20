# ocean-back/routers/generate_outline.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from services.ai_service import ai_service
import json

router = APIRouter()

class OutlineRequest(BaseModel):
    topic: str
    documentType: str

@router.post("/generate-outline")
async def generate_outline(request: OutlineRequest, user = Depends(verify_token)):
    system_prompt = f"""You are an expert content strategist. Create a detailed outline for a {request.documentType} document.

Format: Return a JSON array of section objects with 'title' and 'description' fields.
Example: [{{"title": "Introduction", "description": "Overview of the topic"}}]

Requirements:
- {5 if request.documentType == 'powerpoint' else 8} sections
- Clear, descriptive titles
- Brief descriptions
- Logical flow"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Topic: {request.topic}"}
    ]

    result = await ai_service.generate_completion(messages)
    if result.get("status") != 200:
        raise HTTPException(status_code=result.get("status", 500), detail=result.get("error", "AI generation failed"))

    try:
        outline = json.loads(result["content"])
        # Ensure list of objects with title
        final = []
        for item in outline:
            if isinstance(item, dict) and item.get("title"):
                final.append({"title": item["title"], "description": item.get("description", "")})
            elif isinstance(item, str):
                final.append({"title": item, "description": ""})
        return {"outline": final}
    except Exception:
        # if parsing fails, fallback to splitting by newlines
        text = result["content"]
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        outline = [{"title": l, "description": ""} for l in lines[:8]]
        return {"outline": outline}
