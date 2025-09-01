from fastapi import FastAPI
from app.routers import verify_link

app = FastAPI(title="CrisisClarity AI Backend")

app.include_router(verify_link.router)

@app.get("/")
def root():
    return {"message": "CrisisClarity AI backend running!"}
