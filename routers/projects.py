# ocean-back/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase_client
from auth import verify_token
from pydantic import BaseModel

router = APIRouter()

class CreateProjectPayload(BaseModel):
    title: str
    document_type: str
    topic: str

@router.get("/projects")
def get_projects(user = Depends(verify_token)):
    sb = supabase_client()
    response = sb.table("projects").select("*").eq("user_id", user["user_id"]).order("updated_at", desc=True).execute()
    # response.status_code check
    if getattr(response, "status_code", None) not in (200, 201, 0, None):
        # For older clients status_code may be None; handle gracefully
        pass
    return {"projects": response.data or []}

@router.post("/projects/create")
def create_project(payload: CreateProjectPayload, user = Depends(verify_token)):
    sb = supabase_client()
    project_data = {
        "title": payload.title,
        "document_type": payload.document_type,
        "topic": payload.topic,
        "status": "draft",
        "user_id": user["user_id"],
    }
    result = sb.table("projects").insert(project_data).execute()
    if getattr(result, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to create project")
    project = (result.data[0] if isinstance(result.data, list) else result.data)
    return {"project": project}
