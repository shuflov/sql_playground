import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import ctypes

# Import your custom modules
from database import execute_query
from snippets import (
    load_snippets,
    get_filtered_snippets,
    add_snippet,
    edit_snippet,
    delete_snippet,
    save_current_as_snippet
)

from export import export_results

# 1. HIGH-DPI AWARENESS
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

# ------------------- GUI Helper Functions -------------------

def refresh_snippet_list():
    filtered = get_filtered_snippets(search_entry.get())
    snippet_listbox.delete(0, tk.END)
    for s in filtered:
        snippet_listbox.insert(tk.END, s["name"])

def run_current_query(event=None):
    sql_to_run = query_text.get("1.0", tk.END).strip()
    if not sql_to_run:
        messagebox.showwarning("Warning", "The query box is empty!")
        return
    execute_query(sql_to_run, output_tree)

def load_selected_snippet(event=None):
    selection = snippet_listbox.curselection()
    if not selection: return
    name = snippet_listbox.get(selection[0])
    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == name:
            query_text.delete("1.0", tk.END)
            query_text.insert("1.0", s["sql"])
            query_text.focus_set()
            break

def save_new_snippet_gui():
    sql = query_text.get("1.0", tk.END).strip()
    if not sql: return
    name = simpledialog.askstring("Save Snippet", "Enter snippet name:")
    if name:
        save_current_as_snippet(name, sql)
        refresh_snippet_list()

def edit_snippet_gui():
    selection = snippet_listbox.curselection()
    if not selection: return
    old_name = snippet_listbox.get(selection[0])
    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == old_name:
            new_name = simpledialog.askstring("Edit", "Name:", initialvalue=s["name"])
            if not new_name: return
            new_sql = simpledialog.askstring("Edit", "SQL:", initialvalue=s["sql"])
            if new_sql is not None:
                edit_snippet(old_name, new_name, new_sql)
                refresh_snippet_list()
            break

def delete_snippet_gui():
    selection = snippet_listbox.curselection()
    if not selection: return
    name = snippet_listbox.get(selection[0])
    if messagebox.askyesno("Delete", f"Delete '{name}'?"):
        delete_snippet(name)
        refresh_snippet_list()

def clear_all():
    # Clear the text box
    query_text.delete("1.0", tk.END)
    
    # Delete all rows
    for item in output_tree.get_children():
        output_tree.delete(item)
    
    # Instead of deleting columns, just HIDE the headings text 
    # This keeps the "structure" alive so the next query doesn't fail
    for col in output_tree["columns"]:
        output_tree.heading(col, text="")



    # This effectively makes the table look empty without "breaking" the widget

# ------------------- Main GUI Setup -------------------

root = tk.Tk()
root.title("SQL Training Tool")
root.state('zoomed') 
root.configure(bg="#f0f0f0")
# FIX: Changed 'windows' to 'alt' for maximum compatibility
style = ttk.Style()
style.theme_use("alt") 
style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
style.configure("Treeview.Heading", background="#e1e1e1", font=("Segoe UI", 9, "bold"))

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=0)
root.grid_rowconfigure(0, weight=1)

# --- LEFT SIDE ---
left_frame = tk.Frame(root, bg="#f0f0f0")
left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
left_frame.grid_columnconfigure(0, weight=1)
left_frame.grid_rowconfigure(4, weight=1)

tk.Label(left_frame, text="SQL Query:", bg="#f0f0f0", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")

query_text = scrolledtext.ScrolledText(left_frame, height=10, font=("Consolas", 11), 
                                      bg="white", fg="black", insertbackground="black", relief="sunken", bd=2)
query_text.grid(row=1, column=0, sticky="nsew", pady=(5,10))

# Main Buttons - with Export on the far right
btn_frame = tk.Frame(left_frame, bg="#f0f0f0")
btn_frame.grid(row=2, column=0, sticky="ew")  # Make it stretch horizontally
btn_frame.grid_columnconfigure(0, weight=1)   # Allows right alignment

# Left side: group the first three buttons
left_btn_frame = tk.Frame(btn_frame, bg="#f0f0f0")
left_btn_frame.grid(row=0, column=0, sticky="w")

tk.Button(left_btn_frame, text="Run Query", command=run_current_query, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Clear", command=clear_all, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Save as Snippet", command=save_new_snippet_gui, width=15).pack(side=tk.LEFT, padx=2)

# Right side: Export button
tk.Button(btn_frame, text="Export Results", command=lambda: export_results(output_tree), width=15).grid(row=0, column=1, sticky="e", padx=(0, 10))

# Results
tree_container = tk.Frame(left_frame)
tree_container.grid(row=4, column=0, sticky="nsew", pady=(10,0))
tree_container.grid_rowconfigure(0, weight=1)
tree_container.grid_columnconfigure(0, weight=1)

v_scroll = tk.Scrollbar(tree_container)
h_scroll = tk.Scrollbar(tree_container, orient="horizontal")
output_tree = ttk.Treeview(tree_container, show="headings", 
                          yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

output_tree.grid(row=0, column=0, sticky="nsew")
v_scroll.grid(row=0, column=1, sticky="ns"); v_scroll.config(command=output_tree.yview)
h_scroll.grid(row=1, column=0, sticky="ew"); h_scroll.config(command=output_tree.xview)

# --- RIGHT SIDE (Locked at 300px) ---
right_frame = tk.Frame(root, width=300, bg="#e1e1e1", relief="sunken", bd=1)
right_frame.grid_propagate(False) 
right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)

tk.Label(right_frame, text="Snippets", bg="#e1e1e1", font=("Arial", 11, "bold")).pack(pady=10)

search_entry = tk.Entry(right_frame, font=("Arial", 10))
search_entry.pack(fill="x", padx=10, pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_snippet_list())

snippet_listbox = tk.Listbox(right_frame, exportselection=False, font=("Arial", 10))
snippet_listbox.pack(fill="both", expand=True, padx=10, pady=5)
snippet_listbox.bind("<<ListboxSelect>>", load_selected_snippet)

s_btn_frame = tk.Frame(right_frame, bg="#e1e1e1")
s_btn_frame.pack(fill="x", pady=10)

tk.Button(s_btn_frame, text="Add", width=7, command=lambda: [add_snippet(simpledialog.askstring("Add", "Name:"), ""), refresh_snippet_list()]).pack(side=tk.LEFT, padx=5)
tk.Button(s_btn_frame, text="Edit", width=7, command=edit_snippet_gui).pack(side=tk.LEFT, padx=2)
tk.Button(s_btn_frame, text="Del", width=7, command=delete_snippet_gui).pack(side=tk.LEFT, padx=2)

# --- START ---
load_snippets()
refresh_snippet_list()
root.bind("<Control-Return>", run_current_query)
root.mainloop()