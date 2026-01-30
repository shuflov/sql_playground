# debug_ai.py

import tkinter as tk
from tkinter import scrolledtext, messagebox

from groq import Groq
from google import genai
from google.genai import types # Correct way to import types for config
from config import load_config

status_ai_label = None  # This will be set from sql_gui.py

def update_ai_status():
    from config import load_config
    config = load_config()
    provider = config.get("ai_provider", "groq").capitalize()
    status_ai_label.config(text=f"AI: {provider}")
    update_ai_status()

def debug_with_ai(query_text_widget, parent_window=None):
    """
    Debugs the current SQL query using selected AI provider (Groq or Gemini).
    Shows result in a popup window.
    """
    query = query_text_widget.get("1.0", "end-1c").strip()

    if not query:
        messagebox.showwarning("No Query", "Please write a query first.")
        return

    config = load_config()
    provider = config.get("ai_provider", "groq").lower()
    api_key = config.get(f"{provider}_api_key")


    if not api_key:
        messagebox.showerror("Missing API Key",
                             f"No API key found for {provider.capitalize()}.\n"
                             f"Please set GEMINI_API_KEY or GROQ_API_KEY in .env\n"
                             "or use the Settings dialog.")
        return

    try:
        ai_answer = ""

        if provider == "groq":
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert SQL Server developer. "
                            "Explain the query clearly, point out potential performance issues, "
                            "security risks, best practice violations, and suggest improvements / rewrites."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Here is the SQL query:\n```sql\n{query}\n```"
                    }
                ],
                model="openai/gpt-oss-120b",   # or "mixtral-8x7b-32768", etc.
                temperature=0.65,
                max_tokens=1200,
                top_p=0.9
            )
            ai_answer = response.choices[0].message.content.strip()

        elif provider == "gemini":
            # Initialize the client
            client = genai.Client(api_key=api_key)
            # Define your prompt
            prompt_text = (
                "You are an expert SQL Server developer. "
                "Explain the query clearly, point out potential performance issues, "
                "security risks, best practice violations, and suggest improvements / rewrites.\n\n"
                f"SQL query:\n```sql\n{query}\n```"
            )

            # Simplified generate_content call
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", 
                contents=prompt_text,
                config=types.GenerateContentConfig(  # Note: it's 'config', not 'generation_config' in the new SDK
                    temperature=0.7,
                    max_output_tokens=1200
                )
            )
            
            # Simplified response access
            ai_answer = response.text.strip()

        else:
            messagebox.showerror("Invalid Provider", f"Unknown provider: {provider}")
            return

        # ── Show result in popup ────────────────────────────────────────
        popup = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
        popup.title(f"AI Debug – {provider.capitalize()}")
        popup.geometry("900x700")
        popup.minsize(700, 500)
        popup.transient(parent_window) if parent_window else None
        popup.grab_set()

        # Header
        tk.Label(
            popup,
            text=f"AI Response from {provider.capitalize()}",
            font=("Arial", 13, "bold"),
            pady=8
        ).pack()

        # Main text area
        text_area = scrolledtext.ScrolledText(
            popup,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#fdfdfd",
            fg="#1a1a1a",
            padx=12, pady=12
        )
        text_area.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        text_area.insert(tk.END, ai_answer)
        text_area.config(state="disabled")

        # Buttons
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=12)

        tk.Button(
            btn_frame,
            text="Close",
            command=popup.destroy,
            width=12,
            font=("Arial", 10, "bold"),
            bg="#6c757d",
            fg="white"
        ).pack(side="left", padx=8)

        # Optional: copy button
        def copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append(ai_answer)
            popup.update()
            messagebox.showinfo("Copied", "AI response copied to clipboard.")

        tk.Button(
            btn_frame,
            text="Copy to Clipboard",
            command=copy_to_clipboard,
            width=18,
            bg="#007bff",
            fg="white"
        ).pack(side="left", padx=8)

    except Exception as e:
        messagebox.showerror(
            "AI Error",
            f"{provider.capitalize()} failed:\n\n{str(e)}\n\n"
            f"Check your API key and internet connection."
        )