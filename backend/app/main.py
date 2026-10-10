import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routes import (
    changes_router,
    tests_router,
    pipeline_router,
    review_router,
    audit_router
)

app = FastAPI(
    title="Agentic QE - Test Impact & Prioritization Engine",
    description="Enterprise Quality Engineering platform for automated API change analysis, regression test impact discovery, and deterministic prioritization.",
    version="1.0.0"
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(changes_router)
app.include_router(tests_router)
app.include_router(pipeline_router)
app.include_router(review_router)
app.include_router(audit_router)

# Mount static frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Agentic QE Backend",
        "version": "1.0.0",
        "execution_mode": "Local Deterministic Mode Active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
