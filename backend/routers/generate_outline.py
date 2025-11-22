from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from services.ai_service import ai_service
import json
import re

router = APIRouter()

class OutlineRequest(BaseModel):
    topic: str
    documentType: str

@router.post("/generate-outline")
async def generate_outline(request: OutlineRequest, user = Depends(verify_token)):
    system_prompt = f"""You are an expert content strategist. Create a detailed outline for a {request.documentType} document.

Format: Return ONLY a JSON array of section objects with 'title' and 'description' fields.
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

    content = result["content"]
    final_outline = []

    try:
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            for item in data:
                if isinstance(item, dict) and item.get("title"):
                    final_outline.append({
                        "title": item["title"], 
                        "description": item.get("description", "")
                    })
    except Exception as e:
        print(f"JSON Parse failed, switching to fallback: {e}")

    if not final_outline:
        titles = re.findall(r'"title":\s*"([^"]+)"', content)
        descriptions = re.findall(r'"description":\s*"([^"]+)"', content)
        
        for i, title in enumerate(titles):
            desc = descriptions[i] if i < len(descriptions) else ""
            final_outline.append({"title": title, "description": desc})

    if not final_outline:
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        for l in lines:
            if l in ['[', ']', '{', '}', '},', '],']:
                continue
            clean_l = l.strip('"').strip(',').strip()
            if clean_l:
                final_outline.append({"title": clean_l, "description": ""})

    if not final_outline:
        final_outline = [{"title": "Introduction", "description": "Please regenerate outline."}]

    return {"outline": final_outline[:10]}