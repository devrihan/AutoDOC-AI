# ocean-back/routers/refinements.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase_client
from auth import verify_token

router = APIRouter()

class RefinementPayload(BaseModel):
    section_id: str
    prompt: str
    result: str

@router.post("/refinements/create")
def add_refinement(payload: RefinementPayload, user = Depends(verify_token)):
    sb = supabase_client()
    
    # FIX: Authenticate with Supabase using the user's token
    # This is required to pass the RLS policy "Users can insert refinements to own sections"
    sb.postgrest.auth(user["token"]) 

    data = {
        "section_id": payload.section_id,
        "prompt": payload.prompt,
        "result": payload.result,
    }
    res = sb.table("refinements").insert(data).execute()
    
    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to save refinement")
    return {"status": "ok"}