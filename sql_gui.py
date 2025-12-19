import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

from database import execute_query
from snippets import (
    load_snippets,
    get_filtered_snippets,
    add_snippet,
    edit_snippet,
    delete_snippet,
    save_current_as_snippet
)

# ------------------- GUI Helper Functions -------------------
def refresh_snippet_list():
    search_term = search_entry.get()
    filtered = get_filtered_snippets(search_term)
    
    snippet_listbox.delete(0, tk.END)
    for snippet in filtered:
        snippet_listbox.insert(tk.END, snippet["name"])

def filter_snippets(event=None):
    refresh_snippet_list()

def load_selected_snippet(event=None):
    selected = snippet_listbox.curselection()
    if not selected:
        return
    name = snippet_listbox.get(selected[0])
    for snippet in get_filtered_snippets(search_entry.get()):
        if snippet["name"] == name:
            query_text.delete("1.0", tk.END)
            query_text.insert(tk.END, snippet["sql"])
            return

def add_snippet_gui():
    name = simpledialog.askstring("Add Snippet", "Enter snippet name:")
    if not name:
        return
    sql = simpledialog.askstring("Add Snippet", "Enter SQL code:", parent=root)
    if sql is None:
        return
    add_snippet(name, sql)
    refresh_snippet_list()

def edit_snippet_gui():
    selected = snippet_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a snippet to edit.")
        return
    old_name = snippet_listbox.get(selected[0])
    snippets = get_filtered_snippets(search_entry.get())
    for s in snippets:
        if s["name"] == old_name:
            new_name = simpledialog.askstring("Edit Snippet", "New name:", initialvalue=s["name"])
            if not new_name:
                return
            new_sql = simpledialog.askstring("Edit Snippet", "New SQL:", initialvalue=s["sql"])
            if new_sql is not None:
                edit_snippet(old_name, new_name, new_sql)
                refresh_snippet_list()
            return

def delete_snippet_gui():
    selected = snippet_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a snippet to delete.")
        return
    name = snippet_listbox.get(selected[0])
    if messagebox.askyesno("Delete", f"Delete snippet '{name}'?"):
        delete_snippet(name)
        refresh_snippet_list()

def save_current_as_snippet_gui():
    current_sql = query_text.get("1.0", tk.END).strip()
    if not current_sql:
        messagebox.showwarning("Warning", "Query input is empty — nothing to save!")
        return

    name = simpledialog.askstring("Save Snippet", "Enter snippet name:", parent=root)
    if not name:
        return

    # Check for overwrite
    all_snippets = load_snippets()
    overwritten = any(s["name"] == name for s in all_snippets)
    if overwritten and not messagebox.askyesno("Overwrite?", f"A snippet named '{name}' already exists. Overwrite it?"):
        return

    save_current_as_snippet(name, current_sql)
    refresh_snippet_list()
    messagebox.showinfo("Success", f"Snippet '{name}' saved!" + (" (overwritten)" if overwritten else ""))

def clear_all():
    query_text.delete("1.0", tk.END)
    output_text.config(state=tk.NORMAL)
    output_text.delete("1.0", tk.END)
    output_text.config(state=tk.DISABLED)

# ------------------- GUI Setup -------------------
root = tk.Tk()
root.title("SQL Training App")
root.geometry("1200x700")
root.minsize(1000, 600)

root.grid_columnconfigure(0, weight=3)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Left Frame - Query & Results
left_frame = tk.Frame(root)
left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10)
left_frame.grid_columnconfigure(0, weight=1)
left_frame.grid_rowconfigure(2, weight=1)  # Buttons row doesn't grow

tk.Label(left_frame, text="Enter SQL Query:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0,5))

query_text = scrolledtext.ScrolledText(left_frame, height=10, wrap=tk.WORD)
query_text.grid(row=1, column=0, sticky="nsew", pady=(0,10))
query_text.insert(tk.END, "SELECT TOP 20 * FROM flights")

# Buttons
btn_frame = tk.Frame(left_frame)
btn_frame.grid(row=2, column=0, sticky="ew", pady=(0,10))
tk.Button(btn_frame, text="Run Query", command=lambda: execute_query(query_text.get("1.0", tk.END), output_text), width=15).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Clear", command=clear_all, width=15).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Save as Snippet", command=save_current_as_snippet_gui, width=18).pack(side=tk.LEFT, padx=5)

tk.Label(left_frame, text="Query Results:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(10,5))

# Output with horizontal + vertical scrolling
output_container = tk.Frame(left_frame)
output_container.grid(row=4, column=0, sticky="nsew")
output_container.grid_rowconfigure(0, weight=1)
output_container.grid_columnconfigure(0, weight=1)

output_text = tk.Text(output_container, height=15, wrap="none", state=tk.DISABLED, font=("Consolas", 10))
output_text.grid(row=0, column=0, sticky="nsew")

v_scroll = tk.Scrollbar(output_container, orient="vertical", command=output_text.yview)
v_scroll.grid(row=0, column=1, sticky="ns")
output_text.configure(yscrollcommand=v_scroll.set)

h_scroll = tk.Scrollbar(output_container, orient="horizontal", command=output_text.xview)
h_scroll.grid(row=1, column=0, sticky="ew")
output_text.configure(xscrollcommand=h_scroll.set)

# Right Frame - Snippets
right_frame = tk.Frame(root, relief="sunken", bd=2)
right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)

tk.Label(right_frame, text="My Snippets", font=("Arial", 14, "bold")).pack(pady=(0,10))

# Search
search_frame = tk.Frame(right_frame)
search_frame.pack(padx=10, pady=(0,5), fill=tk.X)
tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
search_entry = tk.Entry(search_frame)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
search_entry.bind("<KeyRelease>", filter_snippets)

# Listbox
snippet_listbox = tk.Listbox(right_frame, width=30, height=20)
snippet_listbox.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)
snippet_listbox.bind("<<ListboxSelect>>", load_selected_snippet)
snippet_listbox.bind("<Double-Button-1>", load_selected_snippet)

# Snippet buttons
snippet_btn_frame = tk.Frame(right_frame)
snippet_btn_frame.pack(pady=5)
tk.Button(snippet_btn_frame, text="Add", command=add_snippet_gui, width=8).pack(side=tk.LEFT, padx=3)
tk.Button(snippet_btn_frame, text="Edit", command=edit_snippet_gui, width=8).pack(side=tk.LEFT, padx=3)
tk.Button(snippet_btn_frame, text="Delete", command=delete_snippet_gui, width=8).pack(side=tk.LEFT, padx=3)

# ------------------- Keyboard Shortcuts -------------------
root.bind("<Control-Return>", lambda event: execute_query(query_text.get("1.0", tk.END), output_text))
root.bind("<Control-s>", lambda event: save_current_as_snippet_gui())
root.bind("<Control-l>", lambda event: clear_all())
query_text.focus_set()

# Startup
load_snippets()  # Populates current_snippets in snippets.py
refresh_snippet_list()

root.mainloop()