# agentic_ai.py
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from config import OPENAI_API_KEY
import generative_ai # Import this

# --- NEW HELPER FUNCTION ---
def generate_focused_review_materials(original_context, weak_topics):
    """
    Generates summary, flashcards, and mindmap for a list of weak topics.
    This is a helper function that doesn't require an agent.
    """
    topics_str = ", ".join(weak_topics)
    
    # Generate a focused re-learning module
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
        # Use the new, focused summary to generate flashcards
        focused_flashcards = generative_ai.generate_flashcards(focused_summary) 
    
    with st.spinner(f"Generating new mind map for {topics_str}..."):
        # Use the new, focused summary to generate the mindmap
        focused_mindmap = generative_ai.generate_mindmap_markdown(focused_summary)

    return {
        "summary": focused_summary,
        "flashcards": focused_flashcards,
        "mindmap": focused_mindmap
    }
# --- END NEW FUNCTION ---


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
    
    # --- MODIFIED ---
    # Call the new helper function and store the materials
    st.session_state.focused_review = generate_focused_review_materials(original_context, weak_topics)
    # --- END MODIFIED ---
    
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

# --- Agent Setup ---

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
                "weak_topics": str(weak_topics), # Pass as string for robustness
                "original_context": original_context
            })
            return result['output']
        except Exception as e:
            print(f"Error running agent: {e}")
            return "Error: Could not analyze results."