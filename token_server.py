# token_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import time
import uvicorn
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("AGORA_APP_ID")
APP_CERT = os.getenv("AGORA_APP_CERT")  # optional for token generation
TOKEN_EXPIRE_SECONDS = 3600

app = FastAPI(title="Cognitive Twin Token Server")


class TokenResponse(BaseModel):
    app_id: str
    token: Optional[str]
    channel: str
    uid: str
    expires_at: Optional[int]


@app.get("/token", response_model=TokenResponse)
def get_agora_token(channel: str, uid: str = "0"):
    """
    Generate an Agora RTC token for the given channel and uid.
    Requires AGORA_APP_ID and AGORA_APP_CERT in env for production tokens.
    For dev, if APP_CERT not set, token is returned as null (insecure).
    """
    if not APP_ID:
        raise HTTPException(500, "AGORA_APP_ID not set in environment")

    expires_at = None
    token = None

    # Try to generate token if APP_CERT present
    try:
        if APP_CERT:
            # Use agora token builder (you must pip install agora-token-builder or similar)
            # from agora_token_builder import RtcTokenBuilder  # if available
            # role = 1  # publisher
            # ts = int(time.time()) + TOKEN_EXPIRE_SECONDS
            # token = RtcTokenBuilder.buildTokenWithUid(APP_ID, APP_CERT, channel, int(uid), role, ts)
            # expires_at = int(time.time()) + TOKEN_EXPIRE_SECONDS

            # If the above library is not available, return a hint to the client.
            token = "PLEASE_INSTALL_AGORA_TOKEN_BUILDER_AND_REGENERATE"  # placeholder
            expires_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
        else:
            # No APP_CERT -> return only app_id (useful for dev with client-side join without token)
            token = None
            expires_at = None
    except Exception as e:
        raise HTTPException(500, f"Token generation failed: {e}")

    return TokenResponse(app_id=APP_ID, token=token, channel=channel, uid=uid, expires_at=expires_at)


# Payload from frontend when it has a transcript to process
class TranscriptPayload(BaseModel):
    user_id: Optional[int]
    session_id: Optional[int]
    topic: str
    transcript: str
    persona: Optional[str] = "empathetic"


@app.post("/process_transcript")
def process_transcript(payload: TranscriptPayload):
    """
    Receives the user's transcribed speech (STT) and returns an AI reply.
    Delegates to agentic_ai.process_stt() which should return a dict {ai_reply, metadata}
    """
    try:
        # Import agentic_ai dynamically so token_server stays lightweight
        import agentic_ai
        # Ensure agentic_ai is ready to be used in server context
        result = agentic_ai.process_stt(
            user_id=payload.user_id,
            session_id=payload.session_id,
            topic=payload.topic,
            transcript=payload.transcript,
            persona=payload.persona
        )
        return {"ai_reply": result.get("ai_reply"), "metadata": result.get("metadata", {})}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("token_server:app", host="0.0.0.0", port=8000, reload=True)
