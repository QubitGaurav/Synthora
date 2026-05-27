import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.researchRoutes import router

app = FastAPI(title="Local Ollama AI Research Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "Local Ollama AI Research Agent",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "backend": "running",
        "model_provider": "ollama_cloud"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
