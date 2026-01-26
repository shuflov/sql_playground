import pyodbc
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import ctypes
import re  # for syntax highlighting

# Import your custom modules
from history import load_history, add_history_entry, clear_history, delete_history_entry, get_history
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

class EditSnippetDialog:
    """Custom dialog for editing snippets with larger text area"""
    def __init__(self, parent, title, name, sql):
        self.result_name = None
        self.result_sql = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        
        # Configure grid
        self.dialog.grid_rowconfigure(2, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Name field
        name_label = tk.Label(self.dialog, text="Snippet Name:", font=("Arial", 10, "bold"))
        name_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.name_entry = tk.Entry(self.dialog, font=("Arial", 11))
        self.name_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.name_entry.insert(0, name)
        
        # SQL field
        sql_label = tk.Label(self.dialog, text="SQL Query:", font=("Arial", 10, "bold"))
        sql_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Frame for text with scrollbar
        text_frame = tk.Frame(self.dialog)
        text_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(3, weight=1)
        
        self.sql_text = scrolledtext.ScrolledText(
            text_frame, 
            height=15, 
            font=("Consolas", 11),
            bg="white", 
            fg="black",
            wrap=tk.NONE
        )
        self.sql_text.grid(row=0, column=0, sticky="nsew")
        self.sql_text.insert("1.0", sql)
        
        # Buttons frame
        btn_frame = tk.Frame(self.dialog)
        btn_frame.grid(row=4, column=0, pady=15)
        
        tk.Button(btn_frame, text="Save", command=self.save, width=15, 
                  bg="#2ecc71", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.cancel, width=15,
                  bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Focus on name field
        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)
        
    def save(self):
        self.result_name = self.name_entry.get().strip()
        self.result_sql = self.sql_text.get("1.0", "end-1c").strip()
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()

class TextLineNumbers(tk.Canvas):
    """Canvas widget that displays line numbers for a Text widget"""
    def __init__(self, parent, text_widget, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.text_widget = text_widget
        
    def redraw(self, *args):
        """Redraw line numbers"""
        self.delete("all")
        
        # Get the number of lines in the text widget
        i = self.text_widget.index("@0,0")
        start_line = int(i.split('.')[0])
        
        # Get the last visible line
        last_visible = self.text_widget.index("@0,%d" % self.text_widget.winfo_height())
        end_line = int(last_visible.split('.')[0])
        
        # Draw line numbers for visible lines
        for line_num in range(start_line, end_line + 1):
            try:
                # Get the y coordinate of this line
                line_index = f"{line_num}.0"
                bbox = self.text_widget.bbox(line_index)
                if bbox:
                    y = bbox[1]
                    self.create_text(35, y, anchor="ne", text=str(line_num), 
                                   font=("Consolas", 11), fill="#999999")
            except:
                break

# ... existing imports and DPI settings ...


def on_scroll(*args):
    query_text.yview(*args)
    query_text.after(1, line_numbers.redraw)

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

# ... existing imports and DPI settings ...

current_db = "test"  # existing line
is_running_query = False  # <--- ADD THIS LINE HERE
def run_current_query(event=None):
    global is_running_query
    is_running_query = True
    import time
    start_time = time.time()

    query = query_text.get("1.0", "end-1c").strip()
    if not query:
        messagebox.showwarning("Empty Query", "Please enter a query.")
        is_running_query = False
        return
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        
        if cursor.description is None:
            rows_affected = cursor.rowcount if cursor.rowcount >= 0 else 0
            result_info = f"{rows_affected} row(s) affected"
            row_count = rows_affected
            conn.commit()
        else:
            rows = cursor.fetchall()
            result_info = f"{len(rows)} rows"
            row_count = len(rows)
        
        cursor.close()
        conn.close()
        
        execution_time = time.time() - start_time
        add_history_entry(query, "success", result_info)
        refresh_history_list()
        update_status_bar(f"Executed in {execution_time:.3f}s", row_count, "success")

        execute_query(query, results_notebook, conn_str)
        if results_notebook.index("end") > 0:
            results_notebook.select(1)

    except Exception as e:
        execution_time = time.time() - start_time
        add_history_entry(query, "error", str(e)[:100])
        refresh_history_list()
        update_status_bar(f"Error in {execution_time:.3f}s", 0, "error")
        messagebox.showerror("Query Error", str(e))
    finally:
        is_running_query = False


def on_key_release(event):
    global is_running_query
    if not is_running_query:  # Only format if not running a query
        query = query_text.get("1.0", tk.END).strip()
        formatted_query = format_sql_keywords(query)
        query_text.delete("1.0", tk.END)
        query_text.insert("1.0", formatted_query)
        highlight_sql()

def update_status_bar(execution_msg, row_count, status):
    """Update the status bar with execution info"""
    # Update execution time
    status_exec_label.config(text=execution_msg)
    
    # Update row count
    if status == "success":
        status_rows_label.config(text=f"Rows: {row_count}", fg="green")
    else:
        status_rows_label.config(text="Error", fg="red")
    
    # Update database name (in case it changed)
    status_db_label.config(text=f"DB: {current_db}")

def get_current_treeview():
    """Return the Treeview widget from the currently selected tab, or None."""
    current_tab = results_notebook.select()
    if not current_tab:
        return None
    tab_frame = results_notebook.nametowidget(current_tab)
    
    # First, check direct children
    for child in tab_frame.winfo_children():
        if isinstance(child, ttk.Treeview):
            return child
    
    # If not found, check one level deeper (inside container frame)
    for child in tab_frame.winfo_children():
        if isinstance(child, tk.Frame) or isinstance(child, ttk.Frame):
            for grandchild in child.winfo_children():
                if isinstance(grandchild, ttk.Treeview):
                    return grandchild
    
    return None

# ------------------- History Functions -------------------

def refresh_history_list():
    """Refresh the history treeview"""
    if 'history_tree' not in globals():
        return
    
    # Clear existing items
    for item in history_tree.get_children():
        history_tree.delete(item)
    
    # Add all history entries
    history_entries = get_history()
    for i, entry in enumerate(history_entries):
        # Truncate query for display
        query_preview = entry['query'][:60] + "..." if len(entry['query']) > 60 else entry['query']
        query_preview = query_preview.replace('\n', ' ')  # Remove newlines
        
        # Color code by result type
        tags = ('success',) if entry['result_type'] == 'success' else ('error',)
        
        history_tree.insert("", "end", values=(
            entry['timestamp'],
            query_preview,
            entry['result_info']
        ), tags=tags)

def on_history_double_click(event):
    """Load query from history into query box"""
    selected = history_tree.selection()
    if not selected:
        return
    
    index = history_tree.index(selected[0])
    history_entries = get_history()
    
    if 0 <= index < len(history_entries):
        query = history_entries[index]['query']
        query_text.delete("1.0", tk.END)
        query_text.insert("1.0", query)
        highlight_sql()
        query_text.focus_set()

def show_history_context_menu(event):
    """Show right-click menu on history item"""
    # Select the item under cursor
    item = history_tree.identify_row(event.y)
    if item:
        history_tree.selection_set(item)
        
        # Create context menu
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Load Query", command=lambda: on_history_double_click(None))
        context_menu.add_command(label="Delete Entry", command=delete_history_entry_gui)
        context_menu.add_separator()
        context_menu.add_command(label="Clear All History", command=clear_history_gui)
        
        # Show menu at cursor position
        context_menu.post(event.x_root, event.y_root)

def delete_history_entry_gui():
    """Delete selected history entry"""
    selected = history_tree.selection()
    if not selected:
        return
    
    index = history_tree.index(selected[0])
    if delete_history_entry(index):
        refresh_history_list()

def clear_history_gui():
    """Clear all history with confirmation"""
    if messagebox.askyesno("Clear History", "Clear all query history?"):
        clear_history()
        refresh_history_list()

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
        # Update status bar
        status_snippet_label.config(text=f"Saved: {name[:30]}...")

def edit_snippet_gui():
    selection = snippet_listbox.curselection()
    if not selection: 
        return
    
    old_name = snippet_listbox.get(selection[0])
    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == old_name:
            # Use custom dialog instead of simpledialog
            dialog = EditSnippetDialog(root, "Edit Snippet", s["name"], s["sql"])
            root.wait_window(dialog.dialog)
            
            if dialog.result_name and dialog.result_sql:
                edit_snippet(old_name, dialog.result_name, dialog.result_sql)
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

def on_snippet_key_nav(event):
    snippet_listbox.after(1, load_current_snippet_from_listbox)


def clear_all():
    query_text.delete("1.0", tk.END)
    for tab in results_notebook.winfo_children():
        tab_index = results_notebook.index(tab)
        tab_name = results_notebook.tab(tab_index, "text")
        if tab_name != "History":
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

def load_current_snippet_from_listbox(set_focus=False):
    selection = snippet_listbox.curselection()
    if not selection:
        return

    index = selection[0]
    name = snippet_listbox.get(index)

    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == name:
            query_text.delete("1.0", tk.END)
            query_text.insert("1.0", s["sql"])
            highlight_sql()

            if set_focus:
                query_text.focus_set()
            break


def on_snippet_arrow(delta):
    size = snippet_listbox.size()
    if size == 0:
        return "break"

    selection = snippet_listbox.curselection()
    index = selection[0] if selection else 0

    new_index = max(0, min(size - 1, index + delta))

    snippet_listbox.selection_clear(0, tk.END)
    snippet_listbox.selection_set(new_index)
    snippet_listbox.activate(new_index)
    snippet_listbox.see(new_index)

    load_current_snippet_from_listbox(set_focus=False)

    return "break"  # ⛔ stop Tkinter default behavior

    load_current_snippet_from_listbox()

def show_snippet_context_menu(event):
    """Show right-click menu on snippet"""
    # Select the item under cursor
    index = snippet_listbox.nearest(event.y)
    if index >= 0:
        snippet_listbox.selection_clear(0, tk.END)
        snippet_listbox.selection_set(index)
        
        # Create context menu
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Edit", command=edit_snippet_gui)
        context_menu.add_command(label="Delete", command=delete_snippet_gui)
        
        # Show menu at cursor position
        context_menu.post(event.x_root, event.y_root)

def on_snippet_drag_start(event):
    """Store the index when drag starts"""
    snippet_listbox.drag_start_index = snippet_listbox.nearest(event.y)

def on_snippet_drag_motion(event):
    """Reorder snippet when dragging"""
    if not hasattr(snippet_listbox, 'drag_start_index'):
        return
    
    current_index = snippet_listbox.nearest(event.y)
    start_index = snippet_listbox.drag_start_index
    
    if current_index != start_index and 0 <= current_index < snippet_listbox.size():
        # Get the actual snippet name
        snippet_name = snippet_listbox.get(start_index)
        snippets = get_filtered_snippets(search_entry.get())
        actual_index = next((i for i, s in enumerate(snippets) if s["name"] == snippet_name), None)
        
        if actual_index is not None:
            # Move in data
            from snippets import current_snippets, save_snippets
            if current_index > start_index:
                for _ in range(current_index - start_index):
                    if actual_index < len(current_snippets) - 1:
                        current_snippets[actual_index], current_snippets[actual_index + 1] = \
                            current_snippets[actual_index + 1], current_snippets[actual_index]
                        actual_index += 1
            else:
                for _ in range(start_index - current_index):
                    if actual_index > 0:
                        current_snippets[actual_index], current_snippets[actual_index - 1] = \
                            current_snippets[actual_index - 1], current_snippets[actual_index]
                        actual_index -= 1
            
            save_snippets()
            refresh_snippet_list()
            snippet_listbox.selection_set(current_index)
            snippet_listbox.drag_start_index = current_index

# ------------------- Syntax Highlighting -------------------
def highlight_sql(event=None):
    for tag in ["keyword", "string", "comment"]:
        query_text.tag_remove(tag, "1.0", tk.END)
    
    content = query_text.get("1.0", tk.END)
    
    keywords = r"\b(SELECT|FROM|WHERE|AND|OR|INSERT|INTO|VALUES|PROCEDURE|UPDATE|SET|DELETE|CREATE|TABLE|DROP|ALTER|JOIN|INNER|LEFT|RIGHT|ON|GROUP BY|ORDER BY|HAVING|AS|DISTINCT|COUNT|SUM|AVG|MIN|MAX|NULL|IS|NOT|LIKE|BETWEEN|IN|EXISTS|ALL|ANY|UNION|CASE|WHEN|THEN|ELSE|END)\b"
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

root.grid_columnconfigure(0, weight=1)  # Left (main) expands
root.grid_columnconfigure(1, weight=0)  # Right (snippets) fixed width
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=0)  # line for status bar

# --- LEFT SIDE: Use PanedWindow for resizable split ---
left_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
left_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Top pane: Query editor + buttons
top_frame = tk.Frame(left_pane, bg="#f0f0f0")
left_pane.add(top_frame, weight=1)  # weight allows it to shrink/grow

top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_rowconfigure(1, weight=1)  # Query text expands

# Title row with database info
title_frame = tk.Frame(top_frame, bg="#f0f0f0")
title_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))

tk.Label(title_frame, text="SQL Query:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
db_label = tk.Label(title_frame, text=f"Database: {current_db}", bg="#f0f0f0", font=("Arial", 10, "italic"), fg="#2c3e50")
db_label.pack(side=tk.LEFT, padx=(20, 0))

# Query editor with line numbers
query_frame = tk.Frame(top_frame, bg="#f0f0f0")
query_frame.grid(row=1, column=0, sticky="nsew", pady=(0,10))
query_frame.grid_rowconfigure(0, weight=1)
query_frame.grid_columnconfigure(1, weight=1)

# Line numbers canvas
line_numbers = TextLineNumbers(query_frame, None, width=40, bg="#e8e8e8", highlightthickness=0)
line_numbers.grid(row=0, column=0, sticky="nsew")

# Query text area
query_text = scrolledtext.ScrolledText(query_frame, height=10, font=("Consolas", 11),
                                      bg="white", fg="black", insertbackground="black", 
                                      relief="sunken", bd=2, wrap="none")
query_text.grid(row=0, column=1, sticky="nsew")

# Connect line numbers to text widget
line_numbers.text_widget = query_text

# Syntax highlighting setup (same as before)
query_text.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
query_text.tag_configure("string", foreground="#008000")
query_text.tag_configure("comment", foreground="#808080")
query_text.vbar.configure(command=on_scroll)

# Syntax highlighting setup
query_text.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
query_text.tag_configure("string", foreground="#008000")
query_text.tag_configure("comment", foreground="#808080")

# Combined update function
def update_editor(event=None):
    schedule_highlight(event)
    query_text.after(1, line_numbers.redraw)

# Bind ALL events that might change view or content
query_text.bind("<KeyPress>", update_editor)
query_text.bind("<KeyRelease>", on_key_release)
query_text.bind("<KeyRelease>", update_editor)
query_text.bind("<FocusIn>", update_editor)
query_text.bind("<MouseWheel>", lambda e: query_text.after(1, line_numbers.redraw))
query_text.bind("<Button-1>", lambda e: query_text.after(10, line_numbers.redraw))
query_text.bind("<ButtonRelease-1>", lambda e: query_text.after(1, line_numbers.redraw))

# Poll for changes regularly (catches everything including scrollbar dragging)
def poll_line_numbers():
    line_numbers.redraw()
    query_text.after(100, poll_line_numbers)  # Check every 100ms

# Start polling
query_text.after(100, poll_line_numbers)

# Initial draw
line_numbers.redraw()

# Buttons row
btn_frame = tk.Frame(top_frame, bg="#f0f0f0")
btn_frame.grid(row=2, column=0, sticky="ew", pady=(0,10))
btn_frame.grid_columnconfigure(0, weight=1)

left_btn_frame = tk.Frame(btn_frame, bg="#f0f0f0")
left_btn_frame.grid(row=0, column=0, sticky="w")

tk.Button(left_btn_frame, text="Run Query", command=run_current_query, bg="#c0f405", width=15, cursor="hand2").pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Clear", command=clear_all, width=12, cursor="hand2").pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Save as Snippet", command=save_new_snippet_gui, width=15, cursor="hand2").pack(side=tk.LEFT, padx=2)

right_btn_frame = tk.Frame(btn_frame, bg="#f0f0f0")
right_btn_frame.grid(row=0, column=1, sticky="e")

tk.Button(right_btn_frame, text="Copy Results", command=lambda: copy_treeview_to_clipboard(get_current_treeview()),
          width=14, bg="#bdc3c7", cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

tk.Button(right_btn_frame, text="Export Results", command=lambda: export_results(get_current_treeview()),
          width=15, bg="#2ecc71", fg="white", cursor="hand2").pack(side=tk.LEFT)

# Bottom pane: Results notebook
results_notebook = ttk.Notebook(left_pane)
left_pane.add(results_notebook, weight=3)  # Give more initial space to results (3:1 ratio)

# Initial empty tab
empty_tab = ttk.Frame(results_notebook)
results_notebook.add(empty_tab, text="Results")
empty_tree = ttk.Treeview(empty_tab)
empty_tree.pack(fill="both", expand=True)

# History tab
history_tab = ttk.Frame(results_notebook)
results_notebook.add(history_tab, text="History")

# History treeview with scrollbars
history_container = tk.Frame(history_tab)
history_container.pack(fill="both", expand=True)

history_scroll_y = tk.Scrollbar(history_container, orient="vertical")
history_scroll_x = tk.Scrollbar(history_container, orient="horizontal")

history_tree = ttk.Treeview(
    history_container,
    columns=("Time", "Query", "Result"),
    show="headings",
    yscrollcommand=history_scroll_y.set,
    xscrollcommand=history_scroll_x.set
)

history_tree.heading("Time", text="Time")
history_tree.heading("Query", text="Query")
history_tree.heading("Result", text="Result")

history_tree.column("Time", width=150)
history_tree.column("Query", width=400)
history_tree.column("Result", width=150)

# Color tags
history_tree.tag_configure('success', foreground='green')
history_tree.tag_configure('error', foreground='red')

history_scroll_y.config(command=history_tree.yview)
history_scroll_x.config(command=history_tree.xview)

history_scroll_y.pack(side=tk.RIGHT, fill="y")
history_scroll_x.pack(side=tk.BOTTOM, fill="x")
history_tree.pack(side=tk.LEFT, fill="both", expand=True)

# Bindings
history_tree.bind("<Double-1>", on_history_double_click)
history_tree.bind("<Button-3>", show_history_context_menu)

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

snippet_listbox.bind("<Up>", lambda e: on_snippet_arrow(-1))
snippet_listbox.bind("<Down>", lambda e: on_snippet_arrow(1))
snippet_listbox.bind("<Return>", lambda e: load_current_snippet_from_listbox(set_focus=True))

snippet_scrollbar.config(command=snippet_listbox.yview)

snippet_listbox.pack(side=tk.LEFT, fill="both", expand=True)
snippet_scrollbar.pack(side=tk.RIGHT, fill="y")

snippet_listbox.bind(
    "<<ListboxSelect>>",
    lambda e: load_current_snippet_from_listbox(set_focus=True)
)

snippet_listbox.focus_set()

snippet_listbox.bind("<Button-3>", show_snippet_context_menu)  # Right-click
snippet_listbox.bind("<Button-1>", on_snippet_drag_start)  # Left-click start
snippet_listbox.bind("<B1-Motion>", on_snippet_drag_motion)  # Drag with left button

s_btn_frame = tk.Frame(right_frame, bg="#e1e1e1")
s_btn_frame.pack(fill="x", pady=10)

#tk.Button(s_btn_frame, text="Page Development", bg="#10d931").pack(side=tk.LEFT, padx=5)
# Change DB button — blue
tk.Button(s_btn_frame, text="Change DB", command=change_database, width=12,
          bg="#4a90e2", fg="white", relief="raised", cursor="hand2").pack(side=tk.LEFT, padx=(10, 8))
tk.Button(s_btn_frame, text="Settings", width=12,bg="#ebedf0", relief="raised", cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

# --- STATUS BAR at bottom ---
status_bar = tk.Frame(root, bg="#2c3e50", height=30, relief="sunken", bd=1)
status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
status_bar.grid_propagate(False)

# Execution time
status_exec_label = tk.Label(status_bar, text="Ready", bg="#2c3e50", fg="white", 
                             font=("Arial", 9), anchor="w", padx=10)
status_exec_label.pack(side=tk.LEFT, fill="x")

# Separator
tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

# Row count
status_rows_label = tk.Label(status_bar, text="Rows: -", bg="#2c3e50", fg="#ecf4f4", 
                             font=("Arial", 9), anchor="w")
status_rows_label.pack(side=tk.LEFT, padx=5)

# Separator
tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

# Database name
status_db_label = tk.Label(status_bar, text=f"DB: {current_db}", bg="#2c3e50", fg="#3498db", 
                          font=("Arial", 9, "bold"), anchor="w")
status_db_label.pack(side=tk.LEFT, padx=5)

# Separator
tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

# Last saved snippet
status_snippet_label = tk.Label(status_bar, text="No snippet saved", bg="#2c3e50", fg="#95a5a6", 
                               font=("Arial", 9, "italic"), anchor="w")
status_snippet_label.pack(side=tk.LEFT, padx=5)

# --- START ---
load_snippets()
refresh_snippet_list()
load_history()
refresh_history_list()
root.bind("<Control-Return>", run_current_query)
root.mainloop()