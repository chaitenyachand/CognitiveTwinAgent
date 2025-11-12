# agentic_ai.py
import os
import sys
import json
import time
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from config import OPENAI_API_KEY
import generative_ai  # Import this

# --- Robust Import Logic ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# =============================== EXISTING FUNCTIONALITY =============================== #

def generate_focused_review_materials(original_context, weak_topics):
    """
    Generates summary, flashcards, and mindmap for a list of weak topics.
    This is a helper function that doesn't require an agent.
    """
    topics_str = ", ".join(weak_topics)
    prompt = f"""
    The student is struggling with these specific topics: {topics_str}.
    Using the original text provided below, generate a new, focused summary
    that specifically explains these weak topics in detail.

    Original Text:
    {original_context}
    """

    with st.spinner(f"Generating new summary for {topics_str}..."):
        focused_summary = generative_ai.generate_summary(prompt)

    with st.spinner(f"Generating new flashcards for {topics_str}..."):
        focused_flashcards = generative_ai.generate_flashcards(focused_summary)

    with st.spinner(f"Generating new mind map for {topics_str}..."):
        focused_mindmap = generative_ai.generate_mindmap_markdown(focused_summary)

    return {
        "summary": focused_summary,
        "flashcards": focused_flashcards,
        "mindmap": focused_mindmap
    }


@tool
def review_weak_topics(weak_topics, original_context):
    """
    Use this tool when a student's score is below 70.
    This tool generates a focused review module for the weak topics.
    """
    topics_str = ", ".join(weak_topics)
    st.session_state.agent_recommendation = {
        "type": "review",
        "topics": topics_str
    }

    st.session_state.focused_review = generate_focused_review_materials(original_context, weak_topics)

    return f"Generated a focused review module for: {topics_str}. Advise the student to study this new material and retake the quiz."


@tool
def start_new_topic(username):
    """
    Use this tool when a student's score is 70 or above.
    This tool congratulates the student and encourages them to start a new topic.
    """
    st.session_state.agent_recommendation = {
        "type": "new_topic",
        "message": f"Excellent work, {username}! You've mastered this topic. You're ready to start a new learning journey."
    }
    return f"Congratulated {username} and advised them to start a new topic."


def get_agent_executor():
    """Initializes the LangChain agent with tools and prompt."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
    tools = [review_weak_topics, start_new_topic]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are the 'Cognitive Twin Agent', a personalized learning assistant.
        Your job is to decide the student's next step based on their quiz performance.

        You have two rules:
        1. If the score is below 70, you MUST use the 'review_weak_topics' tool.
        2. If the score is 70 or above, you MUST use the 'start_new_topic' tool.

        You must call one, and only one, of the provided tools.
        """),
        ("user", """
        Student Name: {username}
        Quiz Score: {score}
        Weak Topics: {weak_topics}
        Original Context: {original_context}
        """),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor


def run_agent_analysis(username, score, weak_topics, original_context):
    """Runs the agent and returns its recommendation."""
    if 'agent_executor' not in st.session_state:
        st.session_state.agent_executor = get_agent_executor()

    executor = st.session_state.agent_executor

    with st.spinner("🧠 Cognitive Twin is analyzing your performance..."):
        try:
            result = executor.invoke({
                "username": username,
                "score": score,
                "weak_topics": str(weak_topics),
                "original_context": original_context
            })
            return result['output']
        except Exception as e:
            print(f"Error running agent: {e}")
            return "Error: Could not analyze results."

# =============================== AGORA CONVERSATIONAL AI =============================== #

# --- Helper: Call OpenAI directly ---
def _call_openai(system_prompt, user_prompt, temperature=0.7, max_tokens=250):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=temperature, api_key=OPENAI_API_KEY)
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    response = llm.invoke(messages)
    return response.content.strip()


# --- Step 1: Analyze student’s answer ---
def analyze_answer(user_text, expected_concept):
    """Analyzes user voice response and detects misconceptions."""
    system_prompt = """
    You are an expert learning evaluator.
    Compare the student's short spoken answer to the expected concept.
    Return JSON with:
    - grade: 'correct', 'partial', or 'incorrect'
    - confidence: 0.0–1.0
    - misconceptions: list of short tags
    - feedback: a one-sentence human-friendly explanation.
    """
    user_prompt = f"""
    Student said: "{user_text}"
    Expected concept: "{expected_concept}"

    Return ONLY JSON.
    Example:
    {{
        "grade": "partial",
        "confidence": 0.6,
        "misconceptions": ["router_vs_modem_confusion"],
        "feedback": "You're close! A router connects multiple networks, not just to the internet."
    }}
    """
    try:
        raw = _call_openai(system_prompt, user_prompt, temperature=0.3)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end]) if start != -1 else {}
    except Exception:
        return {
            "grade": "partial",
            "confidence": 0.5,
            "misconceptions": [],
            "feedback": "Good try — let's explore that more deeply!"
        }


# --- Step 2: Generate Socratic response ---
def socratic_response(user_text, context):
    """
    Main conversational AI loop used by Agora Conversational AI.
    Adapts response dynamically based on user's last message.
    """
    topic = context.get("topic", "General Learning")
    concept = context.get("current_concept", topic)
    persona = context.get("persona", "neutral")

    analysis = analyze_answer(user_text, concept)
    grade = analysis.get("grade", "partial")
    confidence = float(analysis.get("confidence", 0.5))
    feedback = analysis.get("feedback", "")
    misconceptions = analysis.get("misconceptions", [])

    # --- Decide next conversational step ---
    if grade == "correct" and confidence > 0.75:
        action = "advance"
        prompt = f"""
        The student understood {concept} correctly.
        Now ask one question that moves the discussion forward to a deeper idea
        in {topic}. Keep it conversational and concise.
        """
    elif grade == "incorrect":
        action = "explain"
        prompt = f"""
        The student misunderstood {concept}.
        Briefly explain the correct idea in 2 sentences and then ask a simple follow-up question.
        """
    else:
        action = "clarify"
        prompt = f"""
        The student's answer was partially correct.
        Provide an encouraging correction and ask one guiding question.
        """

    system_prompt = "You are a kind, Socratic AI tutor engaging a student in natural voice conversation."
    ai_text = _call_openai(system_prompt, prompt, temperature=0.8, max_tokens=150)

    # --- Optionally add persona tone ---
    ai_text = get_persona_response(persona, ai_text)

    # --- Package metadata for DB logging ---
    metadata = {
        "grade": grade,
        "confidence": confidence,
        "misconceptions": misconceptions,
        "feedback": feedback,
        "action": action,
        "timestamp": time.time()
    }

    return {
        "reply_text": ai_text,
        "action": action,
        "metadata": metadata
    }


# --- Step 3: Persona Tuning ---
def get_persona_response(persona, message):
    """
    Modulates AI tone/personality before sending it to Agora TTS.
    """
    persona_styles = {
        "empathetic": lambda m: f"{m} (spoken softly, reassuring tone)",
        "encouraging": lambda m: f"{m} You’re doing great — keep it up!",
        "authoritative": lambda m: f"{m} Focus carefully on this part, it’s key to mastering the topic.",
        "neutral": lambda m: m
    }
    return persona_styles.get(persona, persona_styles["neutral"])(message)


# --- Step 4: Get Agora Conversational Agent (for integration) ---
def get_agora_conversational_agent():
    """
    Returns a callable that integrates with Agora's STT/TTS loop.
    Use this in your voice_twin.py for real-time interaction.
    """
    def handle_user_input(user_text, context):
        """
        Simulates one round-trip in Agora conversation.
        (Agora STT provides user_text; this function returns ai_text + metadata)
        """
        result = socratic_response(user_text, context)
        return {
            "ai_reply": result["reply_text"],
            "metadata": result["metadata"]
        }

    return handle_user_input


# --- existing code kept above unchanged ---
# Add this new function for realtime transcript processing.

def process_stt(user_id, session_id, topic, transcript, persona="empathetic"):
    """
    Handle one STT turn coming from the client.
    - transcript: user's spoken text (string)
    - persona: emotional tone for responses

    Returns: { "ai_reply": str, "metadata": { ... } }
    """

    # 1) Build context the agent expects
    context = {
        "user_id": user_id,
        "session_id": session_id,
        "topic": topic,
        "persona": persona,
        "transcript": transcript,
        "timestamp": time.time()
    }

    # 2) Use your generative_ai or existing agent tool to create a response.
    # Keep behavior consistent with your existing agent: Socratic, ask-one-question, grade etc.
    try:
        # Prefer a direct "socratic" function if you already have one:
        # ai_reply = agentic_socratic_reply(transcript, topic, persona)
        # Else fallback to generative_ai with a prompt

        prompt = f"""
        You are a Socratic tutor (persona: {persona}) teaching the topic: {topic}.
        The student's latest spoken response: "{transcript}"
        Your goal:
          1) Assess the answer for understanding and misconceptions.
          2) Provide ONE concise feedback sentence + ONE follow-up Socratic question.
          3) Keep style empathetic and short.
        Return only a JSON with keys: {{ "reply": "...", "analysis": "..." }}
        """

        # generative_ai.generate_chat_response is a recommended helper (you may have it)
        try:
            # If you have a helper that returns structured json, use it
            out = generative_ai.generate_chat_response(prompt)
            if isinstance(out, dict) and "reply" in out:
                ai_reply = out["reply"]
                metadata = {"analysis": out.get("analysis", "")}
            else:
                # fallback: treat out as raw text
                ai_reply = out if isinstance(out, str) else str(out)
                metadata = {}
        except Exception:
            # fallback simple call
            ai_reply = generative_ai.simple_reply(prompt)
            metadata = {}

        # 3) Optionally record conversational turn in DB
        try:
            import database_utils as db
            db.log_conversation(
                user_id=user_id,
                session_id=session_id,
                topic=topic,
                user_text=transcript,
                ai_text=ai_reply,
                metadata=metadata
            )
        except Exception:
            # logging failure should not block response
            pass

        return {"ai_reply": ai_reply, "metadata": metadata}
    except Exception as e:
        return {"ai_reply": "Sorry, I couldn't process that right now.", "metadata": {"error": str(e)}}

# Append to agentic_ai.py (keep your existing functions unchanged above)

import time
import json
import database_utils as db
import generative_ai

def _build_socratic_prompt(topic, transcript, recent_turns, persona="empathetic"):
    """
    Construct a concise, focused prompt for the LLM that asks it to:
     - assess student's correctness
     - return one concise feedback sentence
     - return exactly one Socratic follow-up question
     - provide a short analysis and suggested next objective
     - return JSON only
    """
    recent = ""
    if recent_turns:
        recent_lines = []
        for t in recent_turns:
            role = t.get('role')
            text = t.get('text')
            recent_lines.append(f"{role.upper()}: {text}")
        recent = "\n\nRecent turns:\n" + "\n".join(recent_lines)

    prompt = f"""
You are "Cognitive Twin", a Socratic tutor with persona "{persona}" teaching topic: {topic}.

Student's latest spoken answer: "{transcript}"

{recent}

Your task:
1) Assess the student's answer briefly.
2) Provide ONE concise feedback sentence (correct/partial/wrong + why).
3) Ask ONE single Socratic question to lead the student towards the next objective.
4) Provide a short analysis explaining what misconception (if any) was present.
5) Suggest a next learning objective (a short phrase).

Return a VALID JSON object only (no additional text) with these keys:
{{ "type": <one of 'question'|'explain'|'review'>,
  "ai_reply": "<voice-friendly text the tutor should speak>",
  "analysis": "<short analysis>",
  "next_objective": "<short phrase>" }}
Make ai_reply short (1-2 sentences) and the Socratic question must be included within ai_reply.
"""

    return prompt


def process_stt(user_id, session_id, topic, transcript, persona="empathetic", partial=False):
    """
    Handle one STT turn from the frontend (may be partial or final).
    Returns structured dict: { ai_reply, metadata, structured }
    - structured: {type, next_objective, ai_reply, analysis}
    """
    try:
        # 1) store partial transcripts if flagged (non-blocking)
        if partial:
            try:
                db.log_partial_transcript(user_id, session_id, topic, transcript, time.time())
            except Exception:
                pass  # don't fail on logging

        # 2) fetch recent conversation for short-term memory
        recent = []
        if session_id:
            try:
                recent = db.get_recent_conversation(session_id, limit=8)
            except Exception:
                recent = []

        # 3) Build the Socratic prompt
        prompt = _build_socratic_prompt(topic, transcript, recent, persona=persona)

        # 4) Call generative_ai for structured JSON reply
        structured = None
        ai_reply = "Sorry, I couldn't respond right now."
        metadata = {}
        try:
            # Prefer a structured response helper - implement this in generative_ai for reliability
            if hasattr(generative_ai, "generate_chat_response_structured"):
                structured = generative_ai.generate_chat_response_structured(prompt)
            elif hasattr(generative_ai, "generate_chat_response"):
                # second-choice: returns JSON string or dict
                out = generative_ai.generate_chat_response(prompt)
                if isinstance(out, dict):
                    structured = out
                else:
                    # attempt to parse JSON
                    try:
                        structured = json.loads(out)
                    except Exception:
                        structured = None
            else:
                # fallback: use a generic call (you must implement generative_ai.simple_chat)
                out = generative_ai.simple_chat(prompt)
                try:
                    structured = json.loads(out)
                except Exception:
                    structured = None
        except Exception as e:
            # fallback minimal reply
            structured = None
            metadata['call_error'] = str(e)

        # 5) Normalize structured result
        if structured and isinstance(structured, dict):
            ai_reply = structured.get("ai_reply") or structured.get("reply") or ""
            metadata['analysis'] = structured.get("analysis", structured.get("analysis", ""))
        else:
            # if we didn't get structured JSON, ask the LLM to summarize in plain text
            if isinstance(structured, str):
                ai_reply = structured
            else:
                ai_reply = "Thanks — can you say a little more about that?"
            metadata['note'] = "Unstructured response from generative_ai"

        # 6) Log the user turn and assistant reply into DB
        try:
            if session_id:
                db.log_conversation(session_id, "user", transcript, {"partial": partial})
                db.log_conversation(session_id, "assistant", ai_reply, metadata)
        except Exception:
            pass

        # 7) Return structured payload
        return {
            "ai_reply": ai_reply,
            "metadata": metadata,
            "structured": structured or {
                "type": "question",
                "next_objective": (structured.get("next_objective") if isinstance(structured, dict) else ""),
                "ai_reply": ai_reply,
                "analysis": metadata.get('analysis', '')
            }
        }
    except Exception as e:
        return {"ai_reply": "Sorry, something went wrong processing that turn.", "metadata": {"error": str(e)}, "structured": {}}
