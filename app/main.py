from fastapi import FastAPI
from app.routers import verify_link, verify_text  # 👈 add verify_text

app = FastAPI(title="CrisisClarity AI Backend")

# Include routers
app.include_router(verify_link.router)
app.include_router(verify_text.router)  # 👈 mount text verification API

@app.get("/")
def root():
    return {"message": "CrisisClarity AI backend running!"}

