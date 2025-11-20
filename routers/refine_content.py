# ocean-back/routers/refine_content.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from services.ai_service import ai_service

router = APIRouter()

class RefineRequest(BaseModel):
    currentContent: str
    prompt: str
    documentType: str

@router.post("/refine-content")
async def refine_content(request: RefineRequest, user = Depends(verify_token)):
    system_prompt = f"""You are a professional content editor for {request.documentType} documents.

Current content:
{request.currentContent}

User request: {request.prompt}

Provide the refined version maintaining the original structure and style."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.prompt}
    ]
    result = await ai_service.generate_completion(messages)
    if result.get("status") != 200:
        raise HTTPException(status_code=result.get("status", 500), detail=result.get("error", "Content refinement failed"))
    return {"content": result["content"]}
