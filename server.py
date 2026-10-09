"""FastAPI Backend Server for Euclid.
Deployable to Hetzner, Render, Docker, or bare metal.
"""

import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
CONTENT_PATH = BASE_DIR / "content" / "lessons.json"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(
    title="Euclid API",
    description="Backend API and static server for Euclid's algorithm visualizer",
    version="1.0.0",
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Root health check for load balancers (Hetzner, Render, etc.)."""
    return {"status": "ok", "service": "euclid"}


@app.get("/api/lessons")
def get_lessons():
    """Serve structured Algorithm E explanations and pedagogical notes."""
    if not CONTENT_PATH.exists():
        raise HTTPException(status_code=404, detail="Lesson data not found")
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# Serve built frontend in production
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        dist_path = FRONTEND_DIST.resolve()
        file_path = (dist_path / full_path).resolve()
        if not file_path.is_relative_to(dist_path):
            raise HTTPException(status_code=404, detail="Not found")
        if not file_path.is_file():
            file_path = (dist_path / "index.html").resolve()
        if not file_path.is_relative_to(dist_path) or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
