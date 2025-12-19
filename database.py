import pyodbc
from tkinter import messagebox
import tkinter as tk

# Database Connection Configuration
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=test;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

def execute_query(query, output_tree):
    """
    Executes a SQL query and populates the provided ttk.Treeview with results.
    """
    # 1. Validation
    if not query.strip():
        messagebox.showwarning("Warning", "Enter a query first!")
        return

    # 2. Clear existing data and reset columns
    for item in output_tree.get_children():
        output_tree.delete(item)
    
    # Reset columns to avoid "ghost" headers from previous different queries
    output_tree["columns"] = ()

    try:
        # 3. Establish Connection
        conn = pyodbc.connect(CONN_STR, autocommit=True)
        cursor = conn.cursor()
        
        # 4. Execute Query
        cursor.execute(query)

        # 5. Handle Results (SELECT statements)
        if cursor.description:
            # Extract column names from cursor description
            cols = [col[0] for col in cursor.description]
            
            # Configure Treeview columns
            output_tree["columns"] = cols
            output_tree.column("#0", width=0, stretch=tk.NO)  # Hide ghost column

            for col in cols:
                output_tree.heading(col, text=col)
                # stretch=False prevents the columns from expanding the whole window
                output_tree.column(col, anchor="w", width=150, stretch=False)

            # Fetch and Insert Data
            rows = cursor.fetchall()
            for i, row in enumerate(rows):
                # Convert None to NULL for display, and everything else to string
                values = [str(item) if item is not None else "NULL" for item in row]
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                output_tree.insert("", "end", values=values, tags=(tag,))
            
            # Add a summary row at the bottom
            summary_vals = [f"Count: {len(rows)}"] + [""] * (len(cols) - 1)
            output_tree.insert("", "end", values=summary_vals, tags=("title",))

        # 6. Handle Non-Select Queries (INSERT, UPDATE, DELETE)
        else:
            output_tree["columns"] = ("Message",)
            output_tree.column("#0", width=0, stretch=tk.NO)
            output_tree.heading("Message", text="Operation Info")
            output_tree.column("Message", width=600, stretch=False)
            
            rowcount = cursor.rowcount if cursor.rowcount >= 0 else 0
            output_tree.insert("", "end", values=(f"Success: {rowcount} rows affected.",), tags=("info",))

        # 7. Multi-statement result cleanup
        while cursor.nextset():
            pass

        # 8. Apply Visual Tags (Matching your GUI style)
        output_tree.tag_configure("title", background="#4472c4", foreground="white", font=("Arial", 10, "bold"))
        output_tree.tag_configure("evenrow", background="#ffffff")
        output_tree.tag_configure("oddrow", background="#f0f0f0")
        output_tree.tag_configure("info", foreground="darkgreen", font=("Arial", 10, "italic"))

        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        # Handle Database Specific Errors (Syntax, Connection, etc.)
        output_tree["columns"] = ("Error",)
        output_tree.heading("Error", text="Database Error")
        output_tree.column("Error", width=800)
        output_tree.insert("", "end", values=(str(e),))
        
    except Exception as e:
        # Handle General Python Errors
        output_tree["columns"] = ("Error",)
        output_tree.heading("Error", text="System Error")
        output_tree.column("Error", width=800)
        output_tree.insert("", "end", values=(str(e),))