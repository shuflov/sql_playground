# config.py
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()  # Loads your .env file

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "ai_provider": "groq",          # default to groq since you have the key
    "gemini_api_key": os.getenv("GEMINI_API_KEY"),
    "groq_api_key": os.getenv("GROQ_API_KEY")
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                user_config = json.load(f)
                config.update(user_config)  # override with saved values
        except:
            pass  # corrupt → keep defaults from .env
    
    # Ensure keys are strings or None
    config["gemini_api_key"] = config.get("gemini_api_key") or None
    config["groq_api_key"] = config.get("groq_api_key") or None
    
    return config

def save_config(config):
    # Only save provider + keys if changed via UI later
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)