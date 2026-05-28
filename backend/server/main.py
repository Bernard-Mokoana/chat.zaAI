import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from src.routes.chat import chat
from src.routes.auth import auth

load_dotenv()

api = FastAPI()
api.include_router(chat)
api.include_router(auth)

allowed_origins = [
    origin.strip()
    for origin in os.environ.get(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001'
).split(',')
]
api.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@api.get("/test")
async def root():
    return {"message": "API is Online"}

if __name__ == "__main__":
    if os.environ.get('APP_ENV') == "development":
        uvicorn.run("main:api", host="0.0.0.0", port=3500, reload=True)
    else:
        uvicorn.run("main:api", host="0.0.0.0", port=3500, reload=False)
        
