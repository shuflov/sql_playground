# export.py  (fixed version — buttons now visible!)

import pandas as pd
from tkinter import filedialog, messagebox, Toplevel, Radiobutton, Button, Label, StringVar, Frame
import tkinter as tk  # Make sure tk is imported for Frame

def export_results(tree):
    """Export Treeview results to CSV or Excel with a radio button dialog."""
    # --- Extract data ---
    columns = tree["columns"]
    if not columns:
        messagebox.showwarning("No Data", "No columns available to export!")
        return

    data = []
    for child in tree.get_children():
        values = tree.item(child)['values']
        data.append(values)

    if not data:
        messagebox.showwarning("No Data", "No rows available to export!")
        return

    df = pd.DataFrame(data, columns=columns)

    # --- Create dialog window ---
    dialog = Toplevel(tree.winfo_toplevel())
    dialog.title("Export Format")
    dialog.resizable(False, False)
    dialog.configure(padx=20, pady=20)
    dialog.transient(tree.winfo_toplevel())
    dialog.grab_set()

    # Title label
    Label(dialog, text="Choose export format:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # Radio buttons
    format_var = StringVar(value="csv")  # Default: CSV

    Radiobutton(dialog, text="CSV (.csv)", variable=format_var, value="csv", font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky="w")
    Radiobutton(dialog, text="Excel (.xlsx)", variable=format_var, value="excel", font=("Arial", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 20))

    # Buttons frame
    btn_frame = Frame(dialog)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    result = {"choice": None}

    def on_export():
        result["choice"] = format_var.get()
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    Button(btn_frame, text="Export", command=on_export, width=12, bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=15)
    Button(btn_frame, text="Cancel", command=on_cancel, width=12, font=("Arial", 9)).pack(side="left", padx=15)

    # Keyboard shortcuts
    dialog.bind("<Return>", lambda e: on_export())
    dialog.bind("<Escape>", lambda e: on_cancel())

    # Center the dialog on screen
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"+{x}+{y}")

    # Wait for user action
    dialog.wait_window()

    if not result["choice"]:
        return  # Canceled

    format_type = result["choice"]

    # --- Save file dialog ---
    if format_type == "excel":
        filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
        def_ext = ".xlsx"
        initial = "query_results.xlsx"
    else:
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        def_ext = ".csv"
        initial = "query_results.csv"

    file_path = filedialog.asksaveasfilename(
        title="Save Results As",
        defaultextension=def_ext,
        filetypes=filetypes,
        initialfile=initial
    )

    if not file_path:
        return

    # --- Export ---
    try:
        if format_type == "csv":
            df.to_csv(file_path, index=False)
        else:
            df.to_excel(file_path, index=False, engine="openpyxl")
        messagebox.showinfo("Success", f"Exported successfully!\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export:\n{str(e)}")