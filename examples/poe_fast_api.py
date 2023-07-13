from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import poe

# Initiate FastAPI
app = FastAPI()

# These tokens are just placeholders for the purpose of this example.
# In a production environment, you should store these values in environment variables or a secure secrets storage.
# Import os and use os.getenv('YOUR_ENV_VAR') to get the environment variables.
API_TOKEN = "your-token"
POE_TOKEN = "your-token"

# CORS middleware settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Model for message
class Message(BaseModel):
    message: str

# Simple auth check
async def auth_check(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return credentials

@app.post("/message")
async def send_message(message: Message, token: HTTPAuthorizationCredentials = Depends(auth_check)):
    # Send the message using poe and collect the response
    client = poe.Client(POE_TOKEN)
    response = []
    for chunk in client.send_message("a2", message.message, with_chat_break=True):
        response.append(chunk["text_new"])

    return {"response": response}
# install requirements ( FastAPI and uvicorn ) using : pip install -r requirements.txt
# run using: uvicorn filename:app --reload