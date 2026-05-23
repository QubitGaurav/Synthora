from fastapi import FastAPI
from routes.researchRoutes import router

app = FastAPI(title="OpenAI Research Agent")
app.include_router(router)
