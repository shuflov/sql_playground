import pyodbc
import sqlite3
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import ctypes
import re  # for syntax highlighting
import webbrowser

# Import your custom modules
from history import load_history, add_history_entry, clear_history, delete_history_entry, get_history
from snippets import (
    load_snippets,
    get_filtered_snippets,
    edit_snippet,
    delete_snippet,
    save_current_as_snippet,
    move_snippet_up,
    move_snippet_down
)
from export import export_results
from debug_ai import show_ai_options_window, update_ai_status
from settings import open_settings

# Import display helpers
from database import create_scrollable_tree, autosize_treeview_columns

# *** NEW: Import the SQLite Explorer ***
from SQLiteExplorer import SQLiteExplorer


# HIGH-DPI AWARENESS
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
        
        i = self.text_widget.index("@0,0")
        start_line = int(i.split('.')[0])
        
        last_visible = self.text_widget.index("@0,%d" % self.text_widget.winfo_height())
        end_line = int(last_visible.split('.')[0])
        
        for line_num in range(start_line, end_line + 1):
            try:
                line_index = f"{line_num}.0"
                bbox = self.text_widget.bbox(line_index)
                if bbox:
                    y = bbox[1]
                    self.create_text(35, y, anchor="ne", text=str(line_num), 
                                   font=("Consolas", 11), fill="#999999")
            except:
                break


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
db_type = "sqlserver"  # "sqlserver" or "sqlite"
sqlite_db_path = ""  # Path to SQLite database file
_is_setting_provider = False  # Flag to prevent recursive callback

def get_conn_str(db_name, database_type="sqlserver"):
    if database_type == "sqlite":
        return db_name
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        f"DATABASE={db_name};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

conn_str = get_conn_str(current_db, db_type)

current_db = "test"
is_running_query = False

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
    
    for tab_id in results_notebook.tabs():
        tab_name = results_notebook.tab(tab_id, "text")
        if tab_name != "History":
            results_notebook.forget(tab_id)
    
    try:
        if db_type == "sqlite":
            conn = sqlite3.connect(conn_str)
            conn.row_factory = sqlite3.Row
        else:
            conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(query)
        
        result_count = 0
        has_any_result = False
        row_count = 0
        result_infos = []
        
        while True:
            has_any_result = True
            result_count += 1
            
            tab_frame = ttk.Frame(results_notebook)
            
            if cursor.description:
                if db_type == "sqlite":
                    cols = [description[0] for description in cursor.description]
                else:
                    cols = [column[0] for column in cursor.description]
                results_notebook.add(tab_frame, text=f"Result {result_count}")
                
                tree = create_scrollable_tree(tab_frame, cols)
                
                for col in cols:
                    tree.heading(col, text=col)
                    tree.column(col, anchor="center", width=120)
                
                rows = cursor.fetchall()
                result_infos.append(f"{len(rows)} rows")
                row_count += len(rows)
                
                if rows:
                    for i, row in enumerate(rows):
                        values = ["" if val is None else str(val) for val in row]
                        tag = "even" if i % 2 == 0 else "odd"
                        tree.insert("", "end", values=values, tags=(tag,))
                    autosize_treeview_columns(tree)
                    
                    tree.tag_configure("even", background="#f9f9f9")
                    tree.tag_configure("odd", background="#ffffff")
                else:
                    tree.insert(
                        "",
                        "end",
                        values=["(No rows returned)"] + [""] * (len(cols) - 1)
                    )
            
            else:
                affected = cursor.rowcount if cursor.rowcount >= 0 else "unknown"
                result_infos.append(f"{affected} row(s) affected")
                if affected != "unknown":
                    row_count += affected
                
                results_notebook.add(tab_frame, text=f"Query {result_count}")
                
                tree = create_scrollable_tree(tab_frame, ("Message",))
                tree.heading("Message", text="Execution Result")
                tree.column("Message", anchor="w", width=600)
                
                tree.insert(
                    "",
                    "end",
                    values=(f"Success: {affected} row(s) affected",)
                )
                autosize_treeview_columns(tree)
            
            # nextset() is not supported by SQLite
            try:
                if not cursor.nextset():
                    break
            except AttributeError:
                # SQLite doesn't support nextset()
                break
        
        cursor.close()
        if db_type == "sqlite":
            conn.commit()
        conn.close()
        
        if not has_any_result:
            tab_frame = ttk.Frame(results_notebook)
            results_notebook.add(tab_frame, text="Result")
            
            tree = create_scrollable_tree(tab_frame, ("Message",))
            tree.heading("Message", text="Info")
            tree.column("Message", anchor="w", width=600)
            tree.insert("", "end", values=("Query executed successfully.",))
            
            result_infos.append("executed successfully")
        
        result_info = "; ".join(result_infos) if result_infos else "executed"
        execution_time = time.time() - start_time
        add_history_entry(query, "success", result_info)
        refresh_history_list()
        update_status_bar(f"Executed in {execution_time:.3f}s", row_count, "success")
        
        if results_notebook.index("end") > 1:
            results_notebook.select(1)

    except Exception as e:
        execution_time = time.time() - start_time
        add_history_entry(query, "error", str(e)[:100])
        refresh_history_list()
        update_status_bar(f"Error in {execution_time:.3f}s", 0, "error")
        
        tab_frame = ttk.Frame(results_notebook)
        results_notebook.add(tab_frame, text="Error")
        
        tree = create_scrollable_tree(tab_frame, ("Error",))
        tree.heading("Error", text="SQL Error")
        tree.column("Error", anchor="w", width=900)
        
        tree.insert("", "end", values=(str(e),))
        autosize_treeview_columns(tree)
        
        results_notebook.select(tab_frame)
    
    finally:
        is_running_query = False

def format_sql_keywords(sql):
    if not sql:
        return sql

    keywords = {
        "select", "from", "where", "join", "inner", "left", "right", "outer",
        "group", "by", "order", "having", "limit", "offset",
        "insert", "update", "delete", "create", "drop",
        "and", "or", "not"
    }

    formatted = []
    i = 0
    while i < len(sql):
        char = sql[i]
        if char.isalpha():
            word_start = i
            while i < len(sql) and sql[i].isalnum() or sql[i] == '_':
                i += 1
            word = sql[word_start:i]
            if word.lower() in keywords:
                formatted.append(word.upper())
            else:
                formatted.append(word)
        else:
            formatted.append(char)
            i += 1

    return ''.join(formatted)


def on_key_release(event):
    global is_running_query
    if not is_running_query:
        query = query_text.get("1.0", tk.END).strip()
        formatted_query = format_sql_keywords(query)
        query_text.delete("1.0", tk.END)
        query_text.insert("1.0", formatted_query)
        highlight_sql()

def update_status_bar(execution_msg, row_count, status):
    status_exec_label.config(text=execution_msg)
    
    if status == "success":
        status_rows_label.config(text=f"Rows: {row_count}", fg="green")
    else:
        status_rows_label.config(text="Error", fg="red")
    
    status_db_label.config(text=f"DB: {current_db}")

def get_current_treeview():
    current_tab = results_notebook.select()
    if not current_tab:
        return None
    tab_frame = results_notebook.nametowidget(current_tab)
    
    for child in tab_frame.winfo_children():
        if isinstance(child, ttk.Treeview):
            return child
    
    for child in tab_frame.winfo_children():
        if isinstance(child, (tk.Frame, ttk.Frame)):
            for grandchild in child.winfo_children():
                if isinstance(grandchild, ttk.Treeview):
                    return grandchild
    
    return None

# ------------------- History Functions -------------------

def refresh_history_list():
    if 'history_tree' not in globals():
        return
    
    for item in history_tree.get_children():
        history_tree.delete(item)
    
    history_entries = get_history()
    for i, entry in enumerate(history_entries):
        query_preview = entry['query'][:60] + "..." if len(entry['query']) > 60 else entry['query']
        query_preview = query_preview.replace('\n', ' ')
        
        tags = ('success',) if entry['result_type'] == 'success' else ('error',)
        
        history_tree.insert("", "end", values=(
            entry['timestamp'],
            query_preview,
            entry['result_info']
        ), tags=tags)

def on_history_double_click(event):
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
    item = history_tree.identify_row(event.y)
    if item:
        history_tree.selection_set(item)
        
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Load Query", command=lambda: on_history_double_click(None))
        context_menu.add_command(label="Delete Entry", command=delete_history_entry_gui)
        context_menu.add_separator()
        context_menu.add_command(label="Clear All History", command=clear_history_gui)
        
        context_menu.post(event.x_root, event.y_root)

def delete_history_entry_gui():
    selected = history_tree.selection()
    if not selected:
        return
    
    index = history_tree.index(selected[0])
    if delete_history_entry(index):
        refresh_history_list()

def clear_history_gui():
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
        status_snippet_label.config(text=f"Saved: {name[:30]}...")

def edit_snippet_gui():
    selection = snippet_listbox.curselection()
    if not selection: 
        return
    
    old_name = snippet_listbox.get(selection[0])
    for s in get_filtered_snippets(search_entry.get()):
        if s["name"] == old_name:
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
    for tab in results_notebook.tabs():
        tab_name = results_notebook.tab(tab, "text")
        if tab_name != "History":
            results_notebook.forget(tab)

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

    lines = ["\t".join(columns)]

    for child in tree.get_children():
        values = tree.item(child)["values"]
        values = ["" if v is None else str(v) for v in values]
        lines.append("\t".join(values))

    text = "\n".join(lines)

    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()

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

    return "break"

def show_snippet_context_menu(event):
    index = snippet_listbox.nearest(event.y)
    if index >= 0:
        snippet_listbox.selection_clear(0, tk.END)
        snippet_listbox.selection_set(index)
        
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Edit", command=edit_snippet_gui)
        context_menu.add_command(label="Delete", command=delete_snippet_gui)
        
        context_menu.post(event.x_root, event.y_root)

def on_snippet_drag_start(event):
    snippet_listbox.drag_start_index = snippet_listbox.nearest(event.y)

def on_snippet_drag_motion(event):
    if not hasattr(snippet_listbox, 'drag_start_index'):
        return
    
    current_index = snippet_listbox.nearest(event.y)
    start_index = snippet_listbox.drag_start_index
    
    if current_index != start_index and 0 <= current_index < snippet_listbox.size():
        snippet_name = snippet_listbox.get(start_index)
        snippets = get_filtered_snippets(search_entry.get())
        actual_index = next((i for i, s in enumerate(snippets) if s["name"] == snippet_name), None)
        
        if actual_index is not None:
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
        
        query_text.delete(start, end)
        query_text.insert(start, match.group().upper())
        
        query_text.tag_add("keyword", start, end)
    
    content = query_text.get("1.0", tk.END)
    
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
    """Open database selection dialog for current provider"""
    global db_type
    select_database_for_provider(db_type)

def select_database_for_provider(provider):
    """Select database for a given provider and update UI"""
    global conn_str, current_db, db_type, sqlite_db_path, db_provider_var, _is_setting_provider
    
    if provider == "sqlite":
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select SQLite Database",
            filetypes=[
                ("SQLite databases", "*.db *.sqlite *.sqlite3"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            # User cancelled, restore previous selection
            _is_setting_provider = True
            db_provider_var.set(db_type)
            _is_setting_provider = False
            return
        
        sqlite_db_path = file_path
        current_db = file_path
        db_type = "sqlite"
        conn_str = get_conn_str(current_db, db_type)

        import os
        short = os.path.basename(file_path)
        root.title(f"SQL Playground - SQLite: {short}")
        db_label.config(text=f"Database: SQLite ({short})")
        status_db_label.config(text=f"DB: SQLite")

        # *** Notify the SQLite Explorer ***
        sqlite_explorer.set_database(file_path)
        # Switch right panel to the Explorer tab
        right_notebook.select(explorer_tab)

    else:  # sqlserver
        new_db = simpledialog.askstring("Change Database", "Enter database name:", initialvalue=current_db)
        if not new_db or not new_db.strip():
            # User cancelled, restore previous selection
            _is_setting_provider = True
            db_provider_var.set(db_type)
            _is_setting_provider = False
            return
        
        current_db = new_db.strip()
        db_type = "sqlserver"
        conn_str = get_conn_str(current_db, db_type)
        root.title(f"SQL Training Tool - Database: {current_db}")
        db_label.config(text=f"Database: {current_db}")
        status_db_label.config(text=f"DB: {current_db}")
        # Clear the explorer when switching to SQL Server
        sqlite_explorer.clear()
        clear_all()
    
    # Update the radio button to reflect actual state
    _is_setting_provider = True
    db_provider_var.set(db_type)
    _is_setting_provider = False
    messagebox.showinfo("Database Changed", f"Now connected to: {db_type.upper()}")
    clear_all()

def open_web_db():
    webbrowser.open("https://shuflov.github.io/database/")

# ------------------- Main GUI Setup -------------------

root = tk.Tk()
root.title("SQL Playground")
root.state('zoomed')
root.configure(bg="lightblue")

style = ttk.Style()
style.theme_use("alt")
style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
style.configure("Treeview.Heading", background="lightblue", font=("Segoe UI", 9, "bold"))

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=0)

# --- Main PanedWindow ---
main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
main_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Left side
left_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
main_pane.add(left_pane, weight=1)

# Top pane: Query editor
top_frame = tk.Frame(left_pane, bg="#f0f0f0")
left_pane.add(top_frame, weight=1)

top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_rowconfigure(1, weight=1)

# Title row
title_frame = tk.Frame(top_frame, bg="lightblue")
title_frame.grid(row=0, column=0, sticky="w", pady=(0, 5))

tk.Label(title_frame, text="SQL Query:", bg="lightblue", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
db_label = tk.Label(title_frame, text=f"Database: {current_db}", bg="lightblue", font=("Arial", 10, "italic"), fg="#2c3e50")
db_label.pack(side=tk.LEFT, padx=(20, 0))

# Query editor with line numbers
query_frame = tk.Frame(top_frame, bg="lightblue")
query_frame.grid(row=1, column=0, sticky="nsew", pady=(0,10))
query_frame.grid_rowconfigure(0, weight=1)
query_frame.grid_columnconfigure(1, weight=1)

line_numbers = TextLineNumbers(query_frame, None, width=40, bg="#e8e8e8", highlightthickness=0)
line_numbers.grid(row=0, column=0, sticky="nsew")

query_text = scrolledtext.ScrolledText(query_frame, height=10, font=("Consolas", 11),
                                      bg="white", fg="black", insertbackground="black", 
                                      relief="sunken", bd=2, wrap="none")
query_text.grid(row=0, column=1, sticky="nsew")

line_numbers.text_widget = query_text

query_text.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
query_text.tag_configure("string", foreground="#008000")
query_text.tag_configure("comment", foreground="#808080")
query_text.vbar.configure(command=on_scroll)

query_text.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
query_text.tag_configure("string", foreground="#008000")
query_text.tag_configure("comment", foreground="#808080")

def update_editor(event=None):
    schedule_highlight(event)
    query_text.after(1, line_numbers.redraw)

query_text.bind("<KeyPress>", update_editor)
query_text.bind("<KeyRelease>", on_key_release)
query_text.bind("<KeyRelease>", update_editor)
query_text.bind("<FocusIn>", update_editor)
query_text.bind("<MouseWheel>", lambda e: query_text.after(1, line_numbers.redraw))
query_text.bind("<Button-1>", lambda e: query_text.after(10, line_numbers.redraw))
query_text.bind("<ButtonRelease-1>", lambda e: query_text.after(1, line_numbers.redraw))

def poll_line_numbers():
    line_numbers.redraw()
    query_text.after(100, poll_line_numbers)

query_text.after(100, poll_line_numbers)
line_numbers.redraw()

# Buttons row
btn_frame = tk.Frame(top_frame, bg="lightblue")
btn_frame.grid(row=2, column=0, sticky="ew", pady=(0,10))
btn_frame.grid_columnconfigure(0, weight=1)

left_btn_frame = tk.Frame(btn_frame, bg="lightblue")
left_btn_frame.grid(row=0, column=0, sticky="w")

tk.Button(left_btn_frame, text="Run Query", command=run_current_query, bg="#c0f405", width=15, cursor="hand2").pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Clear", bg="#9db1f3", command=clear_all, width=12, cursor="hand2").pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Save as Snippet", bg="#7391f3", command=save_new_snippet_gui, width=15, cursor="hand2").pack(side=tk.LEFT, padx=2)
tk.Button(left_btn_frame, text="Play with AI", bg="#b0dc11", command=lambda: show_ai_options_window(query_text, results_notebook), width=15, cursor="hand2").pack(side=tk.LEFT, padx=2)

right_btn_frame = tk.Frame(btn_frame, bg="lightblue")
right_btn_frame.grid(row=0, column=1, sticky="e")

tk.Button(right_btn_frame, text="Copy Results", command=lambda: copy_treeview_to_clipboard(get_current_treeview()),
          width=14, bg="#bdc3c7", cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

tk.Button(right_btn_frame, text="Export Results", command=lambda: export_results(get_current_treeview()),
          width=15, bg="#2ecc71", fg="white", cursor="hand2").pack(side=tk.LEFT)

tk.Button(right_btn_frame, text="Web DB", command=open_web_db,
          width=10, bg="#3498db", fg="white", cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))

# Bottom pane: Results notebook
results_notebook = ttk.Notebook(left_pane)
left_pane.add(results_notebook, weight=3)

empty_tab = ttk.Frame(results_notebook)
results_notebook.add(empty_tab, text="Results")
empty_tree = ttk.Treeview(empty_tab)
empty_tree.pack(fill="both", expand=True)

# History tab
history_tab = ttk.Frame(results_notebook)
results_notebook.add(history_tab, text="History")

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

history_tree.tag_configure('success', foreground='green')
history_tree.tag_configure('error', foreground='red')

history_scroll_y.config(command=history_tree.yview)
history_scroll_x.config(command=history_tree.xview)

history_scroll_y.pack(side=tk.RIGHT, fill="y")
history_scroll_x.pack(side=tk.BOTTOM, fill="x")
history_tree.pack(side=tk.LEFT, fill="both", expand=True)

history_tree.bind("<Double-1>", on_history_double_click)
history_tree.bind("<Button-3>", show_history_context_menu)

# ============================================================
# --- RIGHT SIDE: Notebook with Snippets + SQLite Explorer ---
# ============================================================
right_frame = tk.Frame(main_pane, width=310, bg="#e1e1e1", relief="sunken", bd=1)
right_frame.grid_propagate(False)
main_pane.add(right_frame, weight=0)

right_notebook = ttk.Notebook(right_frame)
right_notebook.pack(fill="both", expand=True)

# ---- Tab 1: Snippets (unchanged) ----
snippets_tab = tk.Frame(right_notebook, bg="#e1e1e1")
right_notebook.add(snippets_tab, text="Snippets")

tk.Label(snippets_tab, text="Snippets", bg="#e1e1e1", font=("Arial", 11, "bold")).pack(pady=10)

search_entry = tk.Entry(snippets_tab, font=("Arial", 10))
search_entry.pack(fill="x", padx=10, pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_snippet_list())

snippet_container = tk.Frame(snippets_tab, bg="#40138d")
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

snippet_listbox.bind("<Button-3>", show_snippet_context_menu)
snippet_listbox.bind("<Button-1>", on_snippet_drag_start)
snippet_listbox.bind("<B1-Motion>", on_snippet_drag_motion)

s_btn_frame = tk.Frame(snippets_tab, bg="#e1e1e1")
s_btn_frame.pack(fill="x", pady=10)

tk.Button(s_btn_frame, text="Change DB", command=change_database, width=12,
          bg="#4a90e2", fg="white", relief="raised", cursor="hand2").pack(side=tk.LEFT, padx=(10, 8))
tk.Button(s_btn_frame, text="Settings", command=lambda: open_settings(root, status_ai_label), width=12,
          bg="#ebedf0", relief="raised", cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

# ---- Tab 2: SQLite Explorer ----
explorer_tab = tk.Frame(right_notebook, bg="#e1e1e1")
right_notebook.add(explorer_tab, text="🗃 DB Explorer")

sqlite_explorer = SQLiteExplorer(
    parent=explorer_tab,
    query_text_widget=query_text,
    highlight_fn=highlight_sql
)

# --- STATUS BAR ---
status_bar = tk.Frame(root, bg="#2c3e50", height=30, relief="sunken", bd=1)
status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
status_bar.grid_propagate(False)

# --- Database Provider Selection (Radio Buttons) ---
db_provider_frame = tk.Frame(status_bar, bg="#2c3e50")
db_provider_frame.pack(side=tk.LEFT, padx=(5, 10))

tk.Label(db_provider_frame, text="DB:", bg="#2c3e50", fg="#7f8c8d", 
         font=("Arial", 9), anchor="w").pack(side=tk.LEFT, padx=(5, 2))

db_provider_var = tk.StringVar(value=db_type)

# Flag to prevent recursive callback when programmatically setting value
_is_setting_provider = False

def on_provider_change(*args):
    """Handle database provider change - trigger database selection"""
    global _is_setting_provider
    if _is_setting_provider:
        return
    new_provider = db_provider_var.get()
    if new_provider != db_type:
        # Provider changed, now select the database
        select_database_for_provider(new_provider)

db_provider_var.trace_add("write", on_provider_change)

tk.Radiobutton(db_provider_frame, text="SQLite", variable=db_provider_var, value="sqlite",
               bg="#2c3e50", fg="#27ae60", selectcolor="#2c3e50", font=("Arial", 9),
               activebackground="#2c3e50", activeforeground="#27ae60",
               cursor="hand2").pack(side=tk.LEFT, padx=2)

tk.Radiobutton(db_provider_frame, text="MS SQL", variable=db_provider_var, value="sqlserver",
               bg="#2c3e50", fg="#4a90e2", selectcolor="#2c3e50", font=("Arial", 9),
               activebackground="#2c3e50", activeforeground="#4a90e2",
               cursor="hand2").pack(side=tk.LEFT, padx=2)

tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

status_exec_label = tk.Label(status_bar, text="Ready", bg="#2c3e50", fg="white", 
                             font=("Arial", 9), anchor="w", padx=10)
status_exec_label.pack(side=tk.LEFT, fill="x")

tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

status_rows_label = tk.Label(status_bar, text="Rows: -", bg="#2c3e50", fg="#ecf4f4", 
                             font=("Arial", 9), anchor="w")
status_rows_label.pack(side=tk.LEFT, padx=5)

tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

status_db_label = tk.Label(status_bar, text=f"DB: {current_db}", bg="#2c3e50", fg="#3498db", 
                          font=("Arial", 9, "bold"), anchor="w")
status_db_label.pack(side=tk.LEFT, padx=5)

tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

global status_ai_label
status_ai_label = tk.Label(
    status_bar,
    text="AI: groq",
    bg="#2c3e50",
    fg="#00d4ff",
    font=("Arial", 9, "bold"),
    anchor="w"
)
status_ai_label.pack(side=tk.LEFT, padx=5)

from debug_ai import update_ai_status
update_ai_status(status_ai_label)

tk.Label(status_bar, text="|", bg="#2c3e50", fg="#7f8c8d", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

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