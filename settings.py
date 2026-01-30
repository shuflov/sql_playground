# settings.py
import tkinter as tk
from tkinter import messagebox
from config import load_config, save_config


def open_settings(parent):
    config = load_config()

    dialog = tk.Toplevel(parent)
    dialog.title("AI Settings")
    dialog.geometry("600x400")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    # Provider selection
    tk.Label(dialog, text="Select AI Provider:", font=("Arial", 11, "bold")).pack(pady=(20, 10))

    provider_var = tk.StringVar(value=config["ai_provider"])

    tk.Radiobutton(dialog, text="Groq (fast & cheap)", variable=provider_var, value="groq").pack(anchor="w", padx=40)
    tk.Radiobutton(dialog, text="Gemini (Google)", variable=provider_var, value="gemini").pack(anchor="w", padx=40)

    # Keys display (read-only for safety)
    tk.Label(dialog, text="Current API Keys (from .env):", font=("Arial", 10, "bold")).pack(pady=(20, 5))

    groq_key = config["groq_api_key"] or "Not set"
    gemini_key = config["gemini_api_key"] or "Not set"

    tk.Label(dialog, text=f"Groq:   {groq_key[:10]}...{groq_key[-4:] if groq_key != 'Not set' else ''}",
             font=("Consolas", 10)).pack(anchor="w", padx=40)
    tk.Label(dialog, text=f"Gemini: {gemini_key[:10]}...{gemini_key[-4:] if gemini_key != 'Not set' else ''}",
             font=("Consolas", 10)).pack(anchor="w", padx=40)

    # Buttons
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=30)

    def save():
        new_provider = provider_var.get()
        config["ai_provider"] = new_provider
        save_config(config)                     # this must be called
        messagebox.showinfo("Settings Saved",
                            f"AI provider set to {new_provider.capitalize()}.\n"
                            "Changes take effect after restart.")
        dialog.destroy()

    tk.Button(btn_frame, text="Save", command=save,
              width=12, bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)

    tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
              width=12, font=("Arial", 10)).pack(side="left", padx=10)