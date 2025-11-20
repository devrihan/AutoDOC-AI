# ocean-back/routers/feedback.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase_client
from auth import verify_token

router = APIRouter()

class FeedbackPayload(BaseModel):
    section_id: str
    is_liked: bool | None = None
    comment: str | None = None

@router.post("/feedback")
def add_feedback(payload: FeedbackPayload, user = Depends(verify_token)):
    sb = supabase_client()
    data = {
        "section_id": payload.section_id,
        "is_liked": payload.is_liked,
        "comment": payload.comment,
    }
    res = sb.table("feedback").insert(data).execute()
    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    return {"status": "ok"}
