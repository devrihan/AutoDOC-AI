# ocean-back/routers/sections.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase_client
from auth import verify_token

router = APIRouter()

class AddSectionsPayload(BaseModel):
    sections: list

@router.post("/sections/add")
def add_sections(payload: AddSectionsPayload, user = Depends(verify_token)):
    sb = supabase_client()
    # Optionally ensure project belongs to user?
    sections = payload.sections
    res = sb.table("sections").insert(sections).execute()
    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to add sections")
    return {"status": "success"}
