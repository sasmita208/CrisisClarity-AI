'''from fastapi import FastAPI
from app.routers import verify_link, verify_text  # 👈 add verify_text

app = FastAPI(title="CrisisClarity AI Backend")

# Include routers
app.include_router(verify_link.router)
app.include_router(verify_text.router)  # 👈 mount text verification API

@app.get("/")
def root():
    return {"message": "CrisisClarity AI backend running!"}

'''
'''
# app/main.py

from fastapi import FastAPI
from app.routers import verify_link, verify_text, factcard

app = FastAPI(title="CrisisClarity AI Backend")

# Routers
app.include_router(verify_link.router)
app.include_router(verify_text.router)
app.include_router(factcard.router)

@app.get("/")
def root():
    return {"message": "CrisisClarity AI backend running!"}
'''
# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import verify_link, verify_text, factcard

app = FastAPI(title="CrisisClarity AI Backend")

# Enable CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(verify_link.router)
app.include_router(verify_text.router)
app.include_router(factcard.router)

@app.get("/")
def root():
    return {"message": "CrisisClarity AI backend running!"}
