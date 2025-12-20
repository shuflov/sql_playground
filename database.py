import pyodbc
from tkinter import messagebox, ttk
import tkinter as tk

def execute_query(query, results_notebook, conn_str):
    if not query.strip():
        messagebox.showwarning("Warning", "Enter a query first!")
        return

    # Clear all existing tabs
    for tab in results_notebook.winfo_children():
        tab.destroy()

    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(query)

        result_count = 0
        has_any_result = False

        while True:
            has_any_result = True
            result_count += 1

            if cursor.description:
                cols = [column[0] for column in cursor.description]

                tab_frame = ttk.Frame(results_notebook)
                results_notebook.add(tab_frame, text=f"Result {result_count}")

                tree = ttk.Treeview(tab_frame, show="headings")
                tree.pack(fill="both", expand=True)

                tree["columns"] = cols
                tree.column("#0", width=0, stretch=False)
                for col in cols:
                    tree.heading(col, text=col)
                    tree.column(col, anchor="w", width=120)

                rows = cursor.fetchall()
                if rows:
                    for i, row in enumerate(rows):
                        values = ["" if val is None else str(val) for val in row]
                        tag = "even" if i % 2 == 0 else "odd"
                        tree.insert("", "end", values=values, tags=(tag,))
                    tree.tag_configure("even", background="#f9f9f9")
                    tree.tag_configure("odd", background="#ffffff")
                else:
                    tree.insert("", "end", values=["(No rows returned)"] + [""] * (len(cols) - 1))

            else:
                affected = cursor.rowcount if cursor.rowcount >= 0 else "unknown"
                tab_frame = ttk.Frame(results_notebook)
                results_notebook.add(tab_frame, text=f"Query {result_count}")

                tree = ttk.Treeview(tab_frame, show="headings")
                tree.pack(fill="both", expand=True)

                tree["columns"] = ("Message",)
                tree.heading("Message", text="Execution Result")
                tree.column("Message", width=500, anchor="w")
                tree.insert("", "end", values=(f"Success: {affected} row(s) affected",))

            if not cursor.nextset():
                break

        cursor.close()
        conn.close()

        if not has_any_result:
            tab_frame = ttk.Frame(results_notebook)
            results_notebook.add(tab_frame, text="Result 1")
            tree = ttk.Treeview(tab_frame)
            tree.pack(fill="both", expand=True)
            tree.insert("", "end", values=("Query executed successfully (no result set)",))

    except Exception as e:
        tab_frame = ttk.Frame(results_notebook)
        results_notebook.add(tab_frame, text="Error")
        tree = ttk.Treeview(tab_frame, show="headings")
        tree.pack(fill="both", expand=True)
        tree["columns"] = ("Error",)
        tree.heading("Error", text="SQL Error")
        tree.column("Error", width=800)
        tree.insert("", "end", values=(str(e),))