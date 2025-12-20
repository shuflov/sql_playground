# snippets.py
import json
from tkinter import messagebox

SNIPPETS_FILE = "snippets.json"

# The full list of snippets — this will be loaded and updated
current_snippets = []

def load_snippets():
    global current_snippets
    try:
        with open(SNIPPETS_FILE, "r") as f:
            current_snippets = json.load(f)
    except FileNotFoundError:
        current_snippets = []
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Corrupted snippets file. Starting fresh.")
        current_snippets = []
    return current_snippets

def save_snippets():
    with open(SNIPPETS_FILE, "w") as f:
        json.dump(current_snippets, f, indent=4)

# These functions now only work with data — GUI is handled outside
def get_filtered_snippets(search_term=""):
    search_term = search_term.lower()
    if not search_term:
        return current_snippets[:]
    return [s for s in current_snippets if search_term in s["name"].lower()]

def add_snippet(name, sql):
    global current_snippets
    current_snippets.append({"name": name, "sql": sql})
    save_snippets()

def edit_snippet(old_name, new_name, new_sql):
    global current_snippets
    for snippet in current_snippets:
        if snippet["name"] == old_name:
            snippet["name"] = new_name
            snippet["sql"] = new_sql
            save_snippets()
            return True
    return False

def delete_snippet(name):
    global current_snippets
    current_snippets = [s for s in current_snippets if s["name"] != name]
    save_snippets()

def save_current_as_snippet(name, current_sql):
    global current_snippets
    for i, snippet in enumerate(current_snippets):
        if snippet["name"] == name:
            current_snippets[i]["sql"] = current_sql
            save_snippets()
            return True
    # New snippet
    current_snippets.append({"name": name, "sql": current_sql})
    save_snippets()
    return True

def move_snippet_up(index):
    if index <= 0 or index >= len(current_snippets):
        return None
    current_snippets[index], current_snippets[index - 1] = current_snippets[index - 1], current_snippets[index]
    save_snippets()
    return index - 1

def move_snippet_down(index):
    if index < 0 or index >= len(current_snippets) - 1:
        return None
    current_snippets[index], current_snippets[index + 1] = current_snippets[index + 1], current_snippets[index]
    save_snippets()
    return index + 1