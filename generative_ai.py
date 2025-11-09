
# generative_ai.py
import openai
import json
import os
import sys # <-- IMPORTED SYS


# --- Robust Import Logic ---
# Add the project's root directory (where app.py is) to the Python path
# This ensures that all module imports (utils, auth, etc.) work reliably
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from config import OPENAI_API_KEY
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_json_response(prompt):
    """Helper function to get a JSON response from the AI."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Use a model that's good at JSON
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant. You must output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error getting JSON response from AI: {e}")
        return None

def generate_summary(text):
    """Generates a detailed summary of the given text."""
    prompt = f"""
    Please provide a detailed, well-structured summary of the following text.
    The summary should be suitable for a student trying to learn this topic from scratch.
    Use markdown for formatting, including headings, subheadings, and bullet points.
    
    Text:
    {text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Error: Could not generate summary."

def generate_mindmap_markdown(text):
    """Generate mindmap markdown using OpenAI."""
    try:
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            print(f"Warning: Text was truncated to {max_chars} characters.")

        prompt = f"""
Create a hierarchical markdown mindmap from the following text. 
Use proper markdown heading syntax (# for main topics, ## for subtopics, ### for details).
Focus on the main concepts and their relationships.

Format the output exactly like this example:
# Main Topic
## Subtopic 1
### Detail 1
- Key point 1
### Detail 2
## Subtopic 2
### Detail 3

Text to analyze: {text}

Respond only with the markdown mindmap, no additional explanation.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        markdown = response.choices[0].message.content
        return markdown.strip()
    except Exception as e:
        print(f"Error generating mindmap: {str(e)}")
        return None

def generate_flashcards(text):
    """Generates a list of flashcards (keyword -> definition)."""
    prompt = f"""
    Generate a list of 10-15 key flashcards from the following text.
    Return a JSON object with a single key "flashcards", which is a list of objects.
    Each object should have two keys: "keyword" and "definition".

    Example format:
    {{
        "flashcards": [
            {{"keyword": "Python", "definition": "A high-level programming language."}},
            {{"keyword": "Variable", "definition": "A storage location with a symbolic name."}}
        ]
    }}
    
    Text:
    {text}
    """
    return get_json_response(prompt)

# --- NEW FUNCTION ---
def generate_formula_sheet(text):
    """Generates a markdown-formatted sheet of key formulas and definitions."""
    prompt = f"""
    Analyze the following text and extract all key formulas, equations, and important definitions.
    Format them clearly using Markdown. Use headings for categories, lists for definitions, 
    and code blocks or LaTeX-style $$...$$ for formulas.
    
    Example:
    
    ## Key Definitions
    * **Topic A**: The definition of topic A.
    * **Topic B**: The definition of topic B.
    
    ## Important Formulas
    **Ohm's Law**
    $$V = IR$$
    
    If no specific formulas are found, list the key concepts and principles.
    
    Text:
    {text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts key formulas and definitions."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating formula sheet: {e}")
        return "Error: Could not generate formula sheet."

# --- MODIFIED FUNCTION ---
def generate_quiz(text, num_questions=5):
    """Generates a dynamic quiz with mixed question types."""
    
    # Simple logic to determine length based on parameter or text
    text_length = len(text)
    
    # Use the provided num_questions, but adjust based on text length if needed
    if text_length < 1000 and num_questions > 5:
        num_questions = 5  # Cap at 5 for short text
    elif text_length > 10000 and num_questions < 10:
        num_questions = min(num_questions, 15)  # Allow up to 15 for long text
    
    # Determine mix (simple ratio)
    num_mcq = int(num_questions * 0.6)
    num_tf = int(num_questions * 0.2)
    num_short = num_questions - num_mcq - num_tf
    
    prompt = f"""
    Analyze the following text and generate a quiz with {num_questions} questions.
    The quiz should be a mix of:
    - {num_mcq} Multiple Choice Questions (MCQ)
    - {num_tf} True/False Questions (T/F)
    - {num_short} Short Answer Questions (Short)
    
    Return a JSON object with a single key "quiz", which is a list of question objects.
    
    Each question object MUST have the following keys:
    1. "type": A string, either "MCQ", "T/F", or "Short".
    2. "question": The question text.
    3. "topic": A 1-3 word topic for this specific question (e.g., "Data Types").
    
    For "MCQ" type:
    - "options": A list of 4 strings (e.g., ["A. Option 1", "B. Option 2", ...]).
    - "answer": The string of the correct option letter (e.g., "A").
    
    For "T/F" type:
    - "options": Must be ["True", "False"].
    - "answer": The correct string, either "True" or "False".
    
    For "Short" type:
    - "answer_keywords": A list of 1-3 keywords that must be in the user's answer
      for it to be considered correct (e.g., ["Ohm's Law", "Voltage"]).
      
    Example format:
    {{
        "quiz": [
            {{
                "type": "MCQ",
                "question": "What is Python?",
                "topic": "Python Basics",
                "options": ["A. A snake", "B. A programming language", "C. A car", "D. A fruit"],
                "answer": "B"
            }},
            {{
                "type": "T/F",
                "question": "Python is a compiled language.",
                "topic": "Python Basics",
                "options": ["True", "False"],
                "answer": "False"
            }},
            {{
                "type": "Short",
                "question": "What law describes the relationship V=IR?",
                "topic": "Physics",
                "answer_keywords": ["Ohm", "Ohm's Law"]
            }}
        ]
    }}
    
    Text:
    {text}
    """
    return get_json_response(prompt)

# --- MODIFIED FUNCTION ---
def answer_question(context, question, style="normal"):
    """Answers a user's question based on context and style."""
    
    style_prompt = ""
    if style == "simple":
        style_prompt = "Explain your answer in very simple terms, like I'm 10 years old."
    elif style == "detailed":
        style_prompt = "Provide an in-depth, expert-level explanation."

    if context:
        # RAG-based answer
        prompt = f"""
        You are a helpful tutor. Using only the context provided, answer the user's question.
        {style_prompt}
        If the answer is not in the context, say "I'm sorry, that information is not in the provided topic."

        Context:
        {context}
        
        Question:
        {question}
        """
        system_message = "You are a helpful tutor answering questions based on context."
    else:
        # General chatbot answer
        prompt = f"{question}\n\n{style_prompt}"
        system_message = "You are a helpful and friendly AI assistant. Answer the user's question directly."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error answering question: {e}")
        return "Error: Could not process your question."
