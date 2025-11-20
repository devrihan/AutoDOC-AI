# ocean-back/routers/export_document.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from auth import verify_token
from supabase_client import supabase_client
from services.document_service import document_service
import io

router = APIRouter()

@router.post("/export-document")
def export_document(payload: dict, user = Depends(verify_token)):
    project_id = payload.get("projectId")
    if not project_id:
        raise HTTPException(status_code=400, detail="projectId is required")

    sb = supabase_client()
    
    # FIX: Authenticate with Supabase so RLS allows us to find the project
    sb.postgrest.auth(user["token"])

    # Now this query will find the project belonging to the user
    try:
        project_res = sb.table("projects").select("*").eq("id", project_id).single().execute()
    except Exception:
        # Handle case where project really doesn't exist or belongs to another user
        raise HTTPException(status_code=404, detail="Project not found")

    project = project_res.data

    # Security check (redundant with RLS but good practice)
    if project["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Fetch sections
    sections_res = sb.table("sections").select("*").eq("project_id", project_id).order("order_index").execute()
    sections = sections_res.data or []

    try:
        if project["document_type"] == "word":
            file_bytes = document_service.generate_word(project["title"], sections)
            filename = f"{project['title']}.docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            file_bytes = document_service.generate_powerpoint(project["title"], sections)
            filename = f"{project['title']}.pptx"
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        return StreamingResponse(
            io.BytesIO(file_bytes), 
            media_type=mime, 
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"Export Error: {str(e)}") # Debug logging
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")