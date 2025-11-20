# ocean-back/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    generate_outline,
    generate_content,
    refine_content,
    export_document,
    projects,
    feedback,
    sections,
    refinements
)

app = FastAPI(title="DocuMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(generate_outline.router, prefix="/api")
app.include_router(generate_content.router, prefix="/api")
app.include_router(refine_content.router, prefix="/api")
app.include_router(export_document.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(sections.router, prefix="/api")
app.include_router(refinements.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
