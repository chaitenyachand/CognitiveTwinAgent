import streamlit as st
import streamlit.components.v1 as components
from config import AGORA_APP_ID, AGORA_TEMP_TOKEN, AGORA_CHANNEL

def start_voice_conversation():
    st.markdown("### 🎙️ Cognitive Twin Voice Assistant")
    st.markdown("Talk to your AI Twin in real time — ask questions, revise concepts, or get instant help!")

    agora_html = f"""
    <html>
      <head>
        <script src="https://download.agora.io/sdk/release/AgoraRTC_N.js"></script>
        <script>
          const APP_ID = "{AGORA_APP_ID}";
          const TOKEN = "{AGORA_TEMP_TOKEN}";
          const CHANNEL = "{AGORA_CHANNEL}";
          const UID = Math.floor(Math.random() * 10000);

          async function startCall() {{
            const client = AgoraRTC.createClient({{ mode: "rtc", codec: "vp8" }});
            await client.join(APP_ID, CHANNEL, TOKEN, UID);
            const localTracks = await AgoraRTC.createMicrophoneAndCameraTracks();

            // Display local audio
            const localAudioContainer = document.createElement("div");
            document.body.append(localAudioContainer);
            localTracks[0].play();
            await client.publish(localTracks);
          }}

          startCall();
        </script>
      </head>
      <body>
        <div id="agora-container" style="width:100%; height:150px; background:#111827; color:white; display:flex; align-items:center; justify-content:center;">
          <p>🎧 Listening... Speak now to your Cognitive Twin!</p>
        </div>
      </body>
    </html>
    """
    components.html(agora_html, height=200)
