# ocean-back/routers/generate_content.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from services.ai_service import ai_service

router = APIRouter()

class ContentRequest(BaseModel):
    sectionTitle: str
    topic: str
    documentType: str

@router.post("/generate-content")
async def generate_content(request: ContentRequest, user = Depends(verify_token)):
    if request.documentType.lower() == "word":
        system_prompt = f"""Generate detailed content for: {request.sectionTitle}
Requirements:
- 3–4 paragraphs
- Clear, logical flow
- Formal and professional tone
- Relevant to the topic: {request.topic}
"""
    else:
        system_prompt = f"""Generate slide content for: {request.sectionTitle}
Format:
- Title at top
- 4–6 bullet points
- Each point max 12–15 words
- Topic: {request.topic}
- Keep it clean and presentation-ready
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate content for section titled: {request.sectionTitle}"}
    ]
    result = await ai_service.generate_completion(messages)
    if result.get("status") != 200:
        raise HTTPException(status_code=result.get("status", 500), detail=result.get("error", "AI content generation failed"))
    return {"content": result["content"]}
