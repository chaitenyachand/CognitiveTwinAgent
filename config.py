# config.py

import os
import sys
import json
from dotenv import load_dotenv

# --- Robust Import Logic ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Load environment variables ---
load_dotenv()

# === Database Configuration ===
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# === OpenAI API Configuration ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")

# === Agora Conversational AI Configuration ===
AGORA_APP_ID = os.getenv("AGORA_APP_ID")
AGORA_APP_CERTIFICATE = os.getenv("AGORA_APP_CERTIFICATE")
AGORA_CHANNEL = os.getenv("AGORA_CHANNEL", "cognitive_twin_voice")

if not AGORA_APP_ID or not AGORA_APP_CERTIFICATE:
    raise ValueError("Agora configuration missing. Please add AGORA_APP_ID and AGORA_APP_CERTIFICATE in your .env file.")

# === Validation for Database ===
if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("Database configuration is missing. Please set it in your .env file.")

