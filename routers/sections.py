# ocean-back/routers/sections.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase_client
from auth import verify_token

router = APIRouter()

class AddSectionsPayload(BaseModel):
    sections: list

class UpdateSectionPayload(BaseModel):
    section_id: str
    content: str

@router.post("/sections/add")
def add_sections(payload: AddSectionsPayload, user = Depends(verify_token)):
    sb = supabase_client()
    sb.postgrest.auth(user["token"]) # Auth fix
    
    sections = payload.sections
    res = sb.table("sections").insert(sections).execute()
    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to add sections")
    return {"status": "success"}

@router.post("/sections/update")
def update_section(payload: UpdateSectionPayload, user = Depends(verify_token)):
    sb = supabase_client()
    sb.postgrest.auth(user["token"]) # Auth fix

    # Update the specific section's content
    data = {"content": payload.content}
    
    # The RLS policy "Users can update sections of own projects" will protect this
    res = sb.table("sections").update(data).eq("id", payload.section_id).execute()

    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to update section")
    
    return {"status": "updated"}