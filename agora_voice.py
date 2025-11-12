# agora_voice.py
import streamlit as st
import streamlit.components.v1 as components
from config import AGORA_APP_ID, AGORA_APP_CERTIFICATE, AGORA_CHANNEL
import time, hmac, base64, hashlib

# === Token Generator ===
def generate_agora_token(channel_name, uid, expire_seconds=3600):
    current_ts = int(time.time())
    expire_ts = current_ts + expire_seconds
    msg = f"{AGORA_APP_ID}{channel_name}{uid}{expire_ts}".encode("utf-8")
    signature = hmac.new(AGORA_APP_CERTIFICATE.encode("utf-8"), msg, hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")

# === Streamlit Voice Chat Interface ===
def start_voice_chat():
    st.title("🎙️ Cognitive Twin Voice Assistant")
    st.info("Talk to your AI Twin in real time! Ask questions, discuss concepts, and get spoken feedback instantly.")

    uid = 12345  # could map to st.session_state.user_id
    token = generate_agora_token(AGORA_CHANNEL, uid)

    agora_html = f"""
    <html>
    <head>
      <script src="https://download.agora.io/sdk/release/AgoraRTC_N.js"></script>
      <script>
        const APP_ID = "{AGORA_APP_ID}";
        const TOKEN = "{token}";
        const CHANNEL = "{AGORA_CHANNEL}";
        const UID = {uid};

        async function startAgoraSession() {{
          const client = AgoraRTC.createClient({{ mode: "rtc", codec: "vp8" }});
          await client.join(APP_ID, CHANNEL, TOKEN, UID);
          const localTracks = await AgoraRTC.createMicrophoneAndCameraTracks();
          const localContainer = document.createElement("div");
          localContainer.id = `user-${{UID}}`;
          document.body.append(localContainer);
          localTracks[1].play(localContainer);
          await client.publish(localTracks);
        }}
        startAgoraSession();
      </script>
    </head>
    <body style="background-color:#111827;color:white;text-align:center;padding:30px;">
      <h3>🎧 Connected to Agora Voice Channel: {AGORA_CHANNEL}</h3>
      <p>Speak freely — your Cognitive Twin is listening...</p>
      <div id="agora-container" style="height:250px;"></div>
    </body>
    </html>
    """
    components.html(agora_html, height=400)

