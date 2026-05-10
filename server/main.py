from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from src.routes.chat import chat
from src.routes.auth import auth
import src.database.models 

load_dotenv()

api = FastAPI()
api.include_router(chat)
api.include_router(auth)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
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
        pass
