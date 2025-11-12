# voice_twin.py
import streamlit as st
import os
import json
from gtts import gTTS
from pathlib import Path
from agentic_ai import socratic_response
import database_utils as db
from datetime import datetime

# Ensure folder for TTS
TTS_DIR = Path("tts_cache")
TTS_DIR.mkdir(exist_ok=True)

def _text_to_speech(text: str, filename: str = None) -> str:
    """
    Simple TTS using gTTS. Saves an mp3 and returns path.
    """
    if not filename:
        filename = f"tts_{int(datetime.now().timestamp())}.mp3"
    file_path = TTS_DIR / filename
    try:
        tts = gTTS(text=text, lang="en")
        tts.save(str(file_path))
        return str(file_path)
    except Exception as e:
        # If gTTS fails, return empty and avoid crashing
        st.error(f"TTS failed: {e}")
        return ""

def run_voice_twin():
    st.title("🎤 Voice Tutor — Conversational Mode (Simulated STT/TTS)")
    st.markdown(
        "This is the voice-first experience *simulated* in text. "
        "Type your responses in the box to emulate STT. AI replies are played as audio (gTTS)."
    )

    # Initialize conversation context in session_state if absent
    if "voice_context" not in st.session_state:
        st.session_state.voice_context = {
            "topic": None,
            "current_concept": None,
            "desired_objective": None,
            "conversation": []  # list of {role, text, ts}
        }

    # If topic missing, ask initial prompt
    if not st.session_state.voice_context.get("topic"):
        st.info("AI: Welcome — what subject would you like to master today?")
        initial_topic = st.text_input("Say (type) the topic you want to learn:", key="initial_topic")
        if st.button("Start Session"):
            if not initial_topic:
                st.error("Please type a topic to start.")
            else:
                # set up context and generate an opening question
                st.session_state.voice_context["topic"] = initial_topic
                st.session_state.voice_context["current_concept"] = initial_topic.split()[0]  # naive seed
                st.session_state.voice_context["desired_objective"] = f"Fundamentals of {initial_topic}"
                # Save conversation entry
                st.session_state.voice_context["conversation"].append(
                    {"role": "system", "text": f"Session started on topic: {initial_topic}", "ts": datetime.now().isoformat()}
                )
                st.experimental_rerun()

    else:
        ctx = st.session_state.voice_context

        # Display conversation
        for msg in ctx["conversation"][-10:]:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['text']}")
            else:
                st.markdown(f"**AI:** {msg['text']}")

        # Input area to simulate STT
        user_input = st.text_input("Your response (type to simulate your speech):", key="voice_sim_input")
        submit = st.button("Send")

        if submit and user_input:
            # Append user message
            ctx["conversation"].append({"role": "user", "text": user_input, "ts": datetime.now().isoformat()})
            # Build minimal context for agent
            agent_ctx = {
                "topic": ctx.get("topic"),
                "current_concept": ctx.get("current_concept"),
                "desired_objective": ctx.get("desired_objective"),
                "conversation": ctx.get("conversation")
            }
            with st.spinner("Thinking..."):
                result = socratic_response(user_input, agent_ctx)

            reply_text = result["reply_text"]
            # Append AI message to conversation
            ctx["conversation"].append({"role": "assistant", "text": reply_text, "ts": datetime.now().isoformat()})

            # Persist to DB: a minimal conversational log & knowledge update
            try:
                user_id = st.session_state.get("user_id")
                if user_id:
                    db.log_conversation(user_id, ctx["topic"], user_input, reply_text, result["metadata"])
            except Exception as e:
                # non-fatal
                st.warning(f"DB log failed: {e}")

            # TTS playback with gTTS
            audio_path = _text_to_speech(reply_text)
            if audio_path:
                st.audio(audio_path)

            # optionally update current_concept/next steps based on metadata
            # (for now we keep same concept; later we may update based on result['action'])
            st.experimental_rerun()
