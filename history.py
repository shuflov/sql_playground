# history.py
import json
from datetime import datetime

HISTORY_FILE = "history.json"
MAX_HISTORY = 100  # Keep last 100 queries

current_history = []

def load_history():
    """Load history from JSON file"""
    global current_history
    try:
        with open(HISTORY_FILE, "r") as f:
            current_history = json.load(f)
    except FileNotFoundError:
        current_history = []
    except json.JSONDecodeError:
        current_history = []
    return current_history

def save_history():
    """Save history to JSON file"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(current_history, f, indent=4)

def add_history_entry(query, result_type, result_info):
    """
    Add a new history entry
    query: SQL query text
    result_type: 'success' or 'error'
    result_info: e.g., '150 rows' or error message
    """
    global current_history
    
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "result_type": result_type,
        "result_info": result_info
    }
    
    # Add to beginning (most recent first)
    current_history.insert(0, entry)
    
    # Limit to MAX_HISTORY
    if len(current_history) > MAX_HISTORY:
        current_history = current_history[:MAX_HISTORY]
    
    save_history()

def clear_history():
    """Clear all history"""
    global current_history
    current_history = []
    save_history()

def delete_history_entry(index):
    """Delete a specific history entry by index"""
    global current_history
    if 0 <= index < len(current_history):
        current_history.pop(index)
        save_history()
        return True
    return False

def get_history():
    """Get all history entries"""
    return current_history[:]