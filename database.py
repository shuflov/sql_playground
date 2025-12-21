import pyodbc
from tkinter import messagebox, ttk
import tkinter as tk
import tkinter.font as tkfont

def autosize_treeview_columns(tree, padding=20):
    """
    Auto-resize Treeview columns based on header and cell content.
    """
    font = tkfont.Font()

    for col in tree["columns"]:
        max_width = font.measure(col)

        for item in tree.get_children():
            value = tree.set(item, col)
            max_width = max(max_width, font.measure(str(value)))

        tree.column(col, width=max_width + padding)


def create_scrollable_tree(parent, columns):
    """
    Create a Treeview with both vertical and horizontal scrollbars.
    Returns the Treeview widget.
    """
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)

    tree = ttk.Treeview(
        container,
        columns=columns,
        show="headings"
    )

    y_scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    x_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)

    tree.configure(
        yscrollcommand=y_scroll.set,
        xscrollcommand=x_scroll.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    return tree


def execute_query(query, results_notebook, conn_str):
    if not query.strip():
        messagebox.showwarning("Warning", "Enter a query first!")
        return

    # Clear existing result tabs
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

            tab_frame = ttk.Frame(results_notebook)

            # ---------------- SELECT queries ----------------
            if cursor.description:
                cols = [column[0] for column in cursor.description]
                results_notebook.add(tab_frame, text=f"Result {result_count}")

                tree = create_scrollable_tree(tab_frame, cols)

                for col in cols:
                    tree.heading(col, text=col)
                    tree.column(col, anchor="center", width=120)

                rows = cursor.fetchall()

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

            # ---------------- Non-SELECT queries ----------------
            else:
                affected = cursor.rowcount if cursor.rowcount >= 0 else "unknown"
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


            if not cursor.nextset():
                break

        cursor.close()
        conn.close()

        if not has_any_result:
            tab_frame = ttk.Frame(results_notebook)
            results_notebook.add(tab_frame, text="Result")

            tree = create_scrollable_tree(tab_frame, ("Message",))
            tree.heading("Message", text="Info")
            tree.column("Message", anchor="w", width=600)
            tree.insert("", "end", values=("Query executed successfully.",))

    # ---------------- Error handling ----------------
    except Exception as e:
        tab_frame = ttk.Frame(results_notebook)
        results_notebook.add(tab_frame, text="Error")

        tree = create_scrollable_tree(tab_frame, ("Error",))
        tree.heading("Error", text="SQL Error")
        tree.column("Error", anchor="w", width=900)

        tree.insert("", "end", values=(str(e),))
        autosize_treeview_columns(tree)

