# database.py
import tkinter as tk
import pyodbc
from tkinter import messagebox

# Connection string — central place, easy to change later
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=test;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

def execute_query(query, output_text):
    """
    Executes the SQL query and inserts formatted results into output_text.
    output_text is the Tkinter Text widget from the main GUI.
    """
    if not query.strip():
        messagebox.showwarning("Warning", "Enter a query first!")
        return

    # Clear previous results
    output_text.config(state="normal")
    output_text.delete("1.0", tk.END)

    try:
        conn = pyodbc.connect(CONN_STR, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(query)

        output_text.insert(tk.END, "Query executed successfully.\n\n")

        result_set_number = 1
        has_results = False

        while True:
            if cursor.description:  # There's a result set (SELECT)
                has_results = True
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                if rows:
                    # Prepare data
                    data = [[str(item) if item is not None else "NULL" for item in row] for row in rows]

                    # Calculate column widths
                    col_widths = [len(col) for col in columns]
                    for row in data:
                        for i, val in enumerate(row):
                            col_widths[i] = max(col_widths[i], len(val))

                    # Print result set header and table
                    output_text.insert(tk.END, f"--- Result Set {result_set_number} ({len(rows)} rows) ---\n")
                    header = "  ".join(f"{col:<{w}}" for col, w in zip(columns, col_widths))
                    output_text.insert(tk.END, header + "\n")
                    output_text.insert(tk.END, "-" * len(header) + "\n")

                    for row in data:
                        line = "  ".join(f"{val:<{w}}" for val, w in zip(row, col_widths))
                        output_text.insert(tk.END, line + "\n")
                    output_text.insert(tk.END, "\n")
                else:
                    output_text.insert(tk.END, f"--- Result Set {result_set_number} (0 rows) ---\n")
                    header = "  ".join(col.ljust(10) for col in columns)
                    output_text.insert(tk.END, header + "\n")
                    output_text.insert(tk.END, "-" * len(header) + "\n\n")

                result_set_number += 1

            if not cursor.nextset():
                break

        if not has_results and cursor.rowcount >= 0:
            output_text.insert(tk.END, f"Rows affected: {cursor.rowcount}\n")

        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        output_text.insert(tk.END, "Error:\n" + str(e) + "\n")
    except Exception as e:
        output_text.insert(tk.END, "Unexpected error:\n" + str(e) + "\n")

    finally:
        output_text.config(state="disabled")