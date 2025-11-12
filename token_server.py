# token_server.py
import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv()

APP_ID = os.getenv("AGORA_APP_ID")
APP_CERT = os.getenv("AGORA_APP_CERT")  # required to generate tokens
TOKEN_EXPIRE_SECONDS = int(os.getenv("TOKEN_EXPIRE_SECONDS", 3600))

app = FastAPI(title="Cognitive Twin - Agora Token Server")


# NOTE: Install a token builder package. Common options:
# pip install agora-token-builder
# The import below matches many token builder examples; if your package differs, adjust.
try:
    from agora_token_builder import RtcTokenBuilder  # pip package: agora-token-builder
    TOKEN_BUILDER_AVAILABLE = True
except Exception:
    TOKEN_BUILDER_AVAILABLE = False


class TokenResponse(BaseModel):
    app_id: str
    token: Optional[str]
    expires_at: Optional[int]
    channel: str
    uid: str


@app.get("/token", response_model=TokenResponse)
def get_agora_token(channel: str, uid: str = "0"):
    """
    Generate an Agora RTC token for joining a channel.
    If APP_CERT is not set or token builder not available, returns token=None (dev mode).
    """
    if not APP_ID:
        raise HTTPException(status_code=500, detail="AGORA_APP_ID not set in environment")

    token = None
    expires_at = None

    if APP_CERT and TOKEN_BUILDER_AVAILABLE:
        try:
            role = 1  # publisher
            ts = int(time.time()) + TOKEN_EXPIRE_SECONDS
            token = RtcTokenBuilder.buildTokenWithUid(APP_ID, APP_CERT, channel, int(uid or 0), role, ts)
            expires_at = ts
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")
    else:
        # Dev mode: return no token (client can join without token if your Agora project allows it)
        token = None
        expires_at = None

    return TokenResponse(app_id=APP_ID, token=token, expires_at=expires_at, channel=channel, uid=str(uid))


class ProcessTranscriptPayload(BaseModel):
    user_id: Optional[int]
    session_id: Optional[int]
    topic: str
    transcript: str
    persona: Optional[str] = "empathetic"
    partial: Optional[bool] = False


@app.post("/process_transcript")
def process_transcript(payload: ProcessTranscriptPayload):
    """
    Receives a full STT transcript (a turn) and returns AI reply & structured metadata.
    Delegates to agentic_ai.process_stt().
    """
    try:
        import agentic_ai
        result = agentic_ai.process_stt(
            user_id=payload.user_id,
            session_id=payload.session_id,
            topic=payload.topic,
            transcript=payload.transcript,
            persona=payload.persona,
            partial=payload.partial
        )
        return {"ai_reply": result.get("ai_reply"), "metadata": result.get("metadata", {}), "structured": result.get("structured", {})}
    except Exception as e:
        return {"error": str(e)}


class PartialPayload(BaseModel):
    user_id: Optional[int]
    session_id: Optional[int]
    topic: Optional[str]
    partial_transcript: str
    timestamp: Optional[float]


@app.post("/log_partial")
def log_partial(payload: PartialPayload):
    """
    Store partial transcripts for analytics (non-blocking).
    """
    try:
        import database_utils as db
        db.log_partial_transcript(payload.user_id, payload.session_id, payload.topic, payload.partial_transcript, payload.timestamp)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("token_server:app", host="0.0.0.0", port=int(os.getenv("TOKEN_SERVER_PORT", 8000)), reload=True)
