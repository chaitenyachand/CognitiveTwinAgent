from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from agora_token_builder import RtcTokenBuilder
from datetime import datetime, timedelta
import os
from config import AGORA_APP_ID, AGORA_APP_CERTIFICATE

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/generate_token")
def generate_token(channel_name: str = Query(...), uid: int = Query(0)):
    expiration_time_in_seconds = 3600
    current_timestamp = int(datetime.timestamp(datetime.utcnow()))
    privilege_expired_ts = current_timestamp + expiration_time_in_seconds

    token = RtcTokenBuilder.buildTokenWithUid(
        AGORA_APP_ID, AGORA_APP_CERTIFICATE, channel_name, uid, 1, privilege_expired_ts
    )
    return {"token": token, "appId": AGORA_APP_ID, "uid": uid, "channel": channel_name}
