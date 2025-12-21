import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import ctypes
import re  # for syntax highlighting

# Import your custom modules
from database import execute_query
from snippets import (
    load_snippets,
    get_filtered_snippets,
    add_snippet,
    edit_snippet,
    delete_snippet,
    save_current_as_snippet,
    move_snippet_up,
    move_snippet_down
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
    search_term = search_entry.get()
    filtered = get_filtered_snippets(search_term)
    
    selected_name = None
    selection = snippet_listbox.curselection()
    if selection:
        selected_name = snippet_listbox.get(selection[0])
    
    snippet_listbox.delete(0, tk.END)
    for s in filtered:
        snippet_listbox.insert(tk.END, s["name"])
    
    if selected_name:
        for i, s in enumerate(filtered):
            if s["name"] == selected_name:
                snippet_listbox.selection_set(i)
                snippet_listbox.see(i)
                break

# Dynamic connection string
current_db = "test"  # default

def get_conn_str(db_name):
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        f"DATABASE={db_name};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

conn_str = get_conn_str(current_db)

def run_current_query(event=None):
    sql_to_run = query_text.get("1.0", tk.END).strip()
    if not sql_to_run:
        messagebox.showwarning("Warning", "The query box is empty!")
        return
    execute_query(sql_to_run, results_notebook, conn_str)

def get_current_treeview():
    """Return the Treeview widget from the currently selected tab, or None."""
    current_tab = results_notebook.select()
    if not current_tab:
        return None
    tab_frame = results_notebook.nametowidget(current_tab)
    for child in tab_frame.winfo_children():
        if isinstance(child, ttk.Treeview):
            return child
    return None

def load_selected_snippet(event=None):
    selection = snippet_listbox.curselection()
    if not selection: return
    name = snippet_listbox.get(selection[0])
    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == name:
            query_text.delete("1.0", tk.END)
            query_text.insert("1.0", s["sql"])
            query_text.focus_set()
            highlight_sql()
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

def move_snippet_up_gui():
    selection = snippet_listbox.curselection()
    if not selection or selection[0] == 0:
        return
    displayed_idx = selection[0]
    name = snippet_listbox.get(displayed_idx)
    
    for i, s in enumerate(get_filtered_snippets("")):
        if s["name"] == name:
            if move_snippet_up(i) is not None:
                refresh_snippet_list()
                new_idx = displayed_idx - 1
                if new_idx >= 0:
                    snippet_listbox.selection_set(new_idx)
                    snippet_listbox.see(new_idx)
            break

def move_snippet_down_gui():
    selection = snippet_listbox.curselection()
    if not selection:
        return
    displayed_idx = selection[0]
    if displayed_idx >= snippet_listbox.size() - 1:
        return
    name = snippet_listbox.get(displayed_idx)
    
    for i, s in enumerate(get_filtered_snippets("")):
        if s["name"] == name:
            if move_snippet_down(i) is not None:
                refresh_snippet_list()
                new_idx = displayed_idx + 1
                if new_idx < snippet_listbox.size():
                    snippet_listbox.selection_set(new_idx)
                    snippet_listbox.see(new_idx)
            break

def clear_all():
    query_text.delete("1.0", tk.END)
    for tab in results_notebook.winfo_children():
        tab.destroy()
    # Add empty placeholder tab
    empty_tab = ttk.Frame(results_notebook)
    results_notebook.add(empty_tab, text="Results")
    empty_tree = ttk.Treeview(empty_tab)
    empty_tree.pack(fill="both", expand=True)
    highlight_sql()

def copy_treeview_to_clipboard(tree):
    if tree is None:
        messagebox.showwarning("No Selection", "No result table selected.")
        return

    columns = tree["columns"]
    if not columns:
        messagebox.showwarning("No Data", "Nothing to copy.")
        return

    # Header row
    lines = ["\t".join(columns)]

    # Data rows
    for child in tree.get_children():
        values = tree.item(child)["values"]
        values = ["" if v is None else str(v) for v in values]
        lines.append("\t".join(values))

    text = "\n".join(lines)

    # Copy to clipboard
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()  # keeps clipboard after app closes

    messagebox.showinfo("Copied", "Result table copied to clipboard.\nPaste directly into Excel.")



# ------------------- Syntax Highlighting -------------------
def highlight_sql(event=None):
    for tag in ["keyword", "string", "comment"]:
        query_text.tag_remove(tag, "1.0", tk.END)
    
    content = query_text.get("1.0", tk.END)
    
    keywords = r"\b(SELECT|FROM|WHERE|AND|OR|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|DROP|ALTER|JOIN|INNER|LEFT|RIGHT|ON|GROUP BY|ORDER BY|HAVING|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|NULL|IS|NOT|LIKE|BETWEEN|IN|EXISTS|ALL|ANY|UNION|CASE|WHEN|THEN|ELSE|END)\b"
    for match in re.finditer(keywords, content, re.IGNORECASE):
        start = query_text.index(f"1.0 + {match.start()} chars")
        end = query_text.index(f"1.0 + {match.end()} chars")
        query_text.tag_add("keyword", start, end)
    
    strings = r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")"
    for match in re.finditer(strings, content):
        start = query_text.index(f"1.0 + {match.start()} chars")
        end = query_text.index(f"1.0 + {match.end()} chars")
        query_text.tag_add("string", start, end)
    
    comments = r"--.*$"
    for match in re.finditer(comments, content, re.MULTILINE):
        start = query_text.index(f"1.0 + {match.start()} chars")
        end = query_text.index(f"1.0 + {match.end()} chars")
        query_text.tag_add("comment", start, end)

def schedule_highlight(event=None):
    query_text.after_cancel("highlight")
    query_text.after(200, highlight_sql)

def change_database():
    global conn_str, current_db, db_label  # Add db_label here
    new_db = simpledialog.askstring("Change Database", "Enter database name:", initialvalue=current_db)
    if new_db and new_db.strip():
        current_db = new_db.strip()
        conn_str = get_conn_str(current_db)
        root.title(f"SQL Training Tool - Database: {current_db}")
        
        # UPDATE THE LABEL
        db_label.config(text=f"Database: {current_db}")
        
        messagebox.showinfo("Database Changed", f"Now connected to: {current_db}")
        clear_all()  # Clear results

# ------------------- Main GUI Setup -------------------

root = tk.Tk()
root.title("SQL Playground")
root.state('zoomed')
root.configure(bg="#f0f0f0")

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

# Title row with dynamic database info
title_frame = tk.Frame(left_frame, bg="#f0f0f0")
title_frame.grid(row=0, column=0, sticky="w")

tk.Label(title_frame, text="SQL Query:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

# Dynamic database label — we'll update this later
db_label = tk.Label(title_frame, text=f"Database: {current_db}", bg="#f0f0f0", font=("Arial", 10, "italic"), fg="#2c3e50")
db_label.pack(side=tk.LEFT, padx=(20, 0))

query_text = scrolledtext.ScrolledText(left_frame, height=10, font=("Consolas", 11),
                                      bg="white", fg="black", insertbackground="black", relief="sunken", bd=2)
query_text.grid(row=1, column=0, sticky="nsew", pady=(5,10))

# Syntax highlighting setup
query_text.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
query_text.tag_configure("string", foreground="#008000")
query_text.tag_configure("comment", foreground="#808080")
query_text.bind("<KeyRelease>", schedule_highlight)
query_text.bind("<FocusIn>", schedule_highlight)

# Main Buttons row
btn_frame = tk.Frame(left_frame, bg="#f0f0f0")
btn_frame.grid(row=2, column=0, sticky="ew")
btn_frame.grid_columnconfigure(0, weight=1)  # Allows right-side buttons to align properly

# Left side: Run, Clear, Save as Snippet
left_btn_frame = tk.Frame(btn_frame, bg="#f0f0f0")
left_btn_frame.grid(row=0, column=0, sticky="w")

tk.Button(left_btn_frame, text="Run Query", command=run_current_query, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Clear", command=clear_all, width=12).pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Save as Snippet", command=save_new_snippet_gui, width=15).pack(side=tk.LEFT, padx=2)

# Right side: Change DB and Export Results — side by side
right_btn_frame = tk.Frame(btn_frame, bg="#f0f0f0")
right_btn_frame.grid(row=0, column=1, sticky="e", padx=(0, 10))

# Change DB button — blue
tk.Button(right_btn_frame, text="Change DB", command=change_database, width=12,
          bg="#4a90e2", fg="white", relief="raised").pack(side=tk.LEFT, padx=(0, 8))

# Copy Results button — neutral
tk.Button(
    right_btn_frame,
    text="Copy Results",
    command=lambda: copy_treeview_to_clipboard(get_current_treeview()),
    width=14,
    bg="#bdc3c7",
    relief="raised"
).pack(side=tk.LEFT, padx=(0, 8))

# Export Results button — green
tk.Button(
    right_btn_frame,
    text="Export Results",
    command=lambda: export_results(get_current_treeview()),
    width=15,
    bg="#2ecc71",
    fg="white",
    relief="raised"
).pack(side=tk.LEFT)


# --- RESULTS: Multi-tab Notebook ---
results_notebook = ttk.Notebook(left_frame)
results_notebook.grid(row=4, column=0, sticky="nsew", pady=(10,0))

# Initial empty tab
empty_tab = ttk.Frame(results_notebook)
results_notebook.add(empty_tab, text="Results")
empty_tree = ttk.Treeview(empty_tab)
empty_tree.pack(fill="both", expand=True)

# --- RIGHT SIDE (Snippets) ---
right_frame = tk.Frame(root, width=300, bg="#e1e1e1", relief="sunken", bd=1)
right_frame.grid_propagate(False)
right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10)

tk.Label(right_frame, text="Snippets", bg="#e1e1e1", font=("Arial", 11, "bold")).pack(pady=10)

search_entry = tk.Entry(right_frame, font=("Arial", 10))
search_entry.pack(fill="x", padx=10, pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_snippet_list())

# --- Snippet list with scrollbar ---
snippet_container = tk.Frame(right_frame, bg="#e1e1e1")
snippet_container.pack(fill="both", expand=True, padx=10, pady=5)

snippet_scrollbar = tk.Scrollbar(snippet_container, orient="vertical")

snippet_listbox = tk.Listbox(
    snippet_container,
    exportselection=False,
    font=("Arial", 10),
    yscrollcommand=snippet_scrollbar.set
)

snippet_scrollbar.config(command=snippet_listbox.yview)

snippet_listbox.pack(side=tk.LEFT, fill="both", expand=True)
snippet_scrollbar.pack(side=tk.RIGHT, fill="y")

snippet_listbox.bind("<<ListboxSelect>>", load_selected_snippet)
snippet_listbox.focus_set()


s_btn_frame = tk.Frame(right_frame, bg="#e1e1e1")
s_btn_frame.pack(fill="x", pady=10)

tk.Button(s_btn_frame, text="Add", width=7, command=lambda: [add_snippet(simpledialog.askstring("Add", "Name:"), ""), refresh_snippet_list()]).pack(side=tk.LEFT, padx=5)
tk.Button(s_btn_frame, text="Edit", width=7, command=edit_snippet_gui).pack(side=tk.LEFT, padx=2)
tk.Button(s_btn_frame, text="Del", width=7, command=delete_snippet_gui).pack(side=tk.LEFT, padx=2)
tk.Button(s_btn_frame, text="↑ Up", width=6, command=move_snippet_up_gui).pack(side=tk.LEFT, padx=8)
tk.Button(s_btn_frame, text="↓ Down", width=6, command=move_snippet_down_gui).pack(side=tk.LEFT, padx=2)

# --- START ---
load_snippets()
refresh_snippet_list()
root.bind("<Control-Return>", run_current_query)
root.mainloop()