from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase_client import supabase_client
from auth import verify_token
from typing import Optional

router = APIRouter()

class AddSectionsPayload(BaseModel):
    sections: list

class UpdateSectionPayload(BaseModel):
    section_id: str
    content: Optional[str] = None
    image_url: Optional[str] = None

@router.post("/sections/add")
def add_sections(payload: AddSectionsPayload, user = Depends(verify_token)):
    sb = supabase_client()
    sb.postgrest.auth(user["token"])
    
    sections = payload.sections
    res = sb.table("sections").insert(sections).execute()
    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to add sections")
    return {"status": "success"}


@router.post("/sections/update")
def update_section(payload: UpdateSectionPayload, user = Depends(verify_token)):
    sb = supabase_client()
    sb.postgrest.auth(user["token"]) 

    data = {}
    if payload.content is not None:
        data["content"] = payload.content
    if payload.image_url is not None:
        data["image_url"] = payload.image_url

    if not data:
        return {"status": "no changes"}
    
    res = sb.table("sections").update(data).eq("id", payload.section_id).execute()

    if getattr(res, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to update section")
    
    return {"status": "updated"}