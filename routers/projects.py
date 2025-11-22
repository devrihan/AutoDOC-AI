from fastapi import APIRouter, Depends, HTTPException
from supabase_client import supabase_client
from auth import verify_token
from pydantic import BaseModel

router = APIRouter()

class CreateProjectPayload(BaseModel):
    title: str
    document_type: str
    topic: str
    ppt_template: str = "default"

@router.get("/projects")
def get_projects(user = Depends(verify_token)):
    sb = supabase_client()
    
    sb.postgrest.auth(user["token"])

    response = sb.table("projects").select("*").eq("user_id", user["user_id"]).order("updated_at", desc=True).execute()
    
    if getattr(response, "status_code", None) not in (200, 201, 0, None):
        pass
    return {"projects": response.data or []}


@router.post("/projects/create")
def create_project(payload: CreateProjectPayload, user = Depends(verify_token)):
    sb = supabase_client()
    
    sb.postgrest.auth(user["token"]) 

    project_data = {
        "title": payload.title,
        "document_type": payload.document_type,
        "topic": payload.topic,
        "status": "draft",
        "user_id": user["user_id"],
        "ppt_template": payload.ppt_template
    }
    
    result = sb.table("projects").insert(project_data).execute()
    
    if getattr(result, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    project = (result.data[0] if isinstance(result.data, list) and len(result.data) > 0 else result.data)
    
    return {"project": project}


@router.get("/projects/{project_id}")
def get_project(project_id: str, user = Depends(verify_token)):
    sb = supabase_client()
    
    sb.postgrest.auth(user["token"])

    res = sb.table("projects").select("*, sections(*)").eq("id", project_id).single().execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = res.data

    if project.get("sections"):
        project["sections"].sort(key=lambda x: x.get("order_index", 0))

    section_ids = [s["id"] for s in project.get("sections", [])]
    feedback_data = []
    
    if section_ids:
        fb_res = sb.table("feedback").select("*").in_("section_id", section_ids).execute()
        feedback_data = fb_res.data if fb_res.data else []

    return {
        "project": project,
        "feedback": feedback_data
    }

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, user = Depends(verify_token)):
    sb = supabase_client()
    
    sb.postgrest.auth(user["token"])

    res = sb.table("projects").delete().eq("id", project_id).execute()
    
    if getattr(res, "status_code", None) not in (200, 204, None, 0):
         raise HTTPException(status_code=500, detail="Failed to delete project")

    return {"status": "deleted", "id": project_id}