import pyodbc
from tkinter import messagebox
import tkinter as tk

CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=test;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

def execute_query(query, output_tree):
    if not query.strip():
        messagebox.showwarning("Warning", "Enter a query first!")
        return

    # 1. Clear existing data and columns
    for item in output_tree.get_children():
        output_tree.delete(item)
    output_tree["columns"] = ()

    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(query)

        if cursor.description:
            # 2. Extract Columns
            cols = [col[0] for col in cursor.description]
            output_tree["columns"] = cols
            
            # Hide the default ghost column
            output_tree.column("#0", width=0, stretch=tk.NO)

            for col in cols:
                output_tree.heading(col, text=col)
                # stretch=False prevents the Treeview from pushing the side panel
                output_tree.column(col, anchor="center", width=150, stretch=False)

            # 3. Fetch and Insert Rows
            rows = cursor.fetchall()
            if not rows:
                output_tree.insert("", "end", values=("(No rows returned)",) + ("",) * (len(cols)-1))
            else:
                for i, row in enumerate(rows):
                    values = [str(item) if item is not None else "NULL" for item in row]
                    # Alternating row colors
                    tag = "evenrow" if i % 2 == 0 else "oddrow"
                    output_tree.insert("", "end", values=values, tags=(tag,))

        else:
            # For non-SELECT queries
            output_tree["columns"] = ("Result",)
            output_tree.heading("Result", text="Execution Info")
            output_tree.column("Result", width=400)
            count = cursor.rowcount if cursor.rowcount >= 0 else 0
            output_tree.insert("", "end", values=(f"Query OK: {count} rows affected",))

        # Cleanup
        cursor.close()
        conn.close()

    except Exception as e:
        # Show error directly in the results table
        output_tree["columns"] = ("Error",)
        output_tree.heading("Error", text="SQL Error Details")
        output_tree.column("Error", width=800)
        output_tree.insert("", "end", values=(str(e),))