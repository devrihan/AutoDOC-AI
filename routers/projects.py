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
    
    # FIX: Authenticate with the user's token so RLS allows reading their projects
    sb.postgrest.auth(user["token"])

    response = sb.table("projects").select("*").eq("user_id", user["user_id"]).order("updated_at", desc=True).execute()
    
    # response.status_code check
    if getattr(response, "status_code", None) not in (200, 201, 0, None):
        # For older clients status_code may be None; handle gracefully
        pass
    return {"projects": response.data or []}

# ... imports ...

@router.post("/projects/create")
def create_project(payload: CreateProjectPayload, user = Depends(verify_token)):
    sb = supabase_client()
    
    # FIX: Authenticate the Supabase client with the user's token
    sb.postgrest.auth(user["token"]) 

    project_data = {
        "title": payload.title,
        "document_type": payload.document_type,
        "topic": payload.topic,
        "status": "draft",
        "user_id": user["user_id"],
    }
    
    # Now this insert will pass the RLS check because auth.uid() will match user_id
    result = sb.table("projects").insert(project_data).execute()
    
    if getattr(result, "status_code", None) not in (200, 201, None, 0):
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    # Handle response data structure variation
    project = (result.data[0] if isinstance(result.data, list) and len(result.data) > 0 else result.data)
    
    return {"project": project}

# ... (keep existing imports and functions) ...

@router.get("/projects/{project_id}")
def get_project(project_id: str, user = Depends(verify_token)):
    sb = supabase_client()
    
    # 1. Authenticate with Supabase (Critical for RLS)
    sb.postgrest.auth(user["token"])

    # 2. Fetch Project + Sections using a Join
    # We select all project fields (*), and nest the sections (*) inside
    res = sb.table("projects").select("*, sections(*)").eq("id", project_id).single().execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = res.data

    # 3. Sort sections by order_index (Database joins don't always guarantee order)
    if project.get("sections"):
        project["sections"].sort(key=lambda x: x.get("order_index", 0))

    # 4. Fetch Feedback for these sections
    # We extract all section IDs to perform a bulk fetch
    section_ids = [s["id"] for s in project.get("sections", [])]
    feedback_data = []
    
    if section_ids:
        fb_res = sb.table("feedback").select("*").in_("section_id", section_ids).execute()
        feedback_data = fb_res.data if fb_res.data else []

    # 5. Return the structure expected by ProjectEditor.tsx
    return {
        "project": project,
        "feedback": feedback_data
    }