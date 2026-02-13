# debug_ai.py

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

from groq import Groq
from google import genai
from google.genai import types
from config import load_config
from ollama_client import generate_from_ollama
from markdown_renderer import apply_markdown

status_ai_label = None  # This will be set from main.py


def set_status_label(label):
    """Register the status label widget from `main.py` and update it immediately."""
    global status_ai_label
    status_ai_label = label
    update_ai_status()


def update_ai_status(label=None):
    """Update the `AI:` status label with the configured provider.

    Behavior:
    - If `label` is provided, update that label instance.
    - Otherwise update the registered module-level `status_ai_label` if set.
    """
    try:
        config = load_config()
        provider = config.get("ai_provider", "groq").capitalize()
        target = label or status_ai_label
        if target:
            target.config(text=f"AI: {provider}")
    except Exception:
        # Non-fatal: don't crash the app for status updates
        pass


def get_error_from_results(results_notebook):
    """Get the error message from the results notebook if an error tab exists."""
    if not results_notebook:
        return None
    
    for tab_id in results_notebook.tabs():
        tab_name = results_notebook.tab(tab_id, "text")
        if tab_name == "Error":
            tab_frame = results_notebook.nametowidget(tab_id)
            for child in tab_frame.winfo_children():
                if isinstance(child, ttk.Treeview):
                    # Get all values from the treeview
                    for item in child.get_children():
                        values = child.item(item, "values")
                        if values and len(values) > 0:
                            return values[0]
    return None


def show_ai_options_window(query_text_widget, results_notebook=None, parent_window=None):
    """
    Show a popup window with query preview, error (if any), and AI options.
    """
    query = query_text_widget.get("1.0", "end-1c").strip()

    if not query:
        messagebox.showwarning("No Query", "Please write a query first.")
        return

    # Get error message if available
    error_message = get_error_from_results(results_notebook)

    # Create popup window
    popup = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
    popup.title("AI Query Assistant")
    popup.geometry("700x550")
    popup.minsize(600, 450)
    if parent_window:
        popup.transient(parent_window)
    popup.grab_set()

    # Header
    header_frame = tk.Frame(popup)
    header_frame.pack(fill="x", padx=12, pady=(12, 8))
    
    tk.Label(
        header_frame,
        text="Query Preview & AI Options",
        font=("Arial", 14, "bold"),
        fg="#2c3e50"
    ).pack(side="left")

    # Query display section
    query_label = tk.Label(popup, text="SQL Query:", font=("Arial", 11, "bold"), fg="#34495e")
    query_label.pack(anchor="w", padx=12, pady=(5, 3))

    query_text = scrolledtext.ScrolledText(
        popup,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#f8f9fa",
        fg="#2c3e50",
        height=8,
        padx=10, pady=8
    )
    query_text.pack(fill="x", padx=12, pady=(0, 8))
    query_text.insert("1.0", query)
    query_text.config(state="disabled")

    # Error display section (if error exists)
    if error_message:
        error_label = tk.Label(popup, text="Error from Last Execution:", font=("Arial", 11, "bold"), fg="#c0392b")
        error_label.pack(anchor="w", padx=12, pady=(5, 3))
        
        error_text = scrolledtext.ScrolledText(
            popup,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#fdf2f2",
            fg="#c0392b",
            height=4,
            padx=10, pady=8
        )
        error_text.pack(fill="x", padx=12, pady=(0, 10))
        error_text.insert("1.0", error_message)
        error_text.config(state="disabled")

    # AI Options section
    options_frame = tk.Frame(popup, bg="#ecf0f1", bd=2, relief="groove")
    options_frame.pack(fill="x", padx=12, pady=(5, 12))
    
    tk.Label(
        options_frame,
        text="Choose AI Action:",
        font=("Arial", 12, "bold"),
        fg="#2c3e50",
        bg="#ecf0f1"
    ).pack(pady=(12, 8))

    btn_frame = tk.Frame(options_frame, bg="#ecf0f1")
    btn_frame.pack(pady=(0, 12), padx=12)

    # Button styles
    btn_config = {
        "width": 15,
        "font": ("Arial", 11, "bold"),
        "cursor": "hand2"
    }

    # Debug button
    tk.Button(
        btn_frame,
        text="Debug",
        command=lambda: (
            popup.destroy(),
            execute_ai_action(query, "debug", error_message, parent_window)
        ),
        bg="#e74c3c",
        fg="white",
        **btn_config
    ).pack(side="left", padx=8)

    # Explain button
    tk.Button(
        btn_frame,
        text="Explain",
        command=lambda: (
            popup.destroy(),
            execute_ai_action(query, "explain", error_message, parent_window)
        ),
        bg="#3498db",
        fg="white",
        **btn_config
    ).pack(side="left", padx=8)

    # Chat button
    tk.Button(
        btn_frame,
        text="Chat",
        command=lambda: (
            popup.destroy(),
            execute_ai_action(query, "chat", error_message, parent_window)
        ),
        bg="#9b59b6",
        fg="white",
        **btn_config
    ).pack(side="left", padx=8)

    # Cancel button
    tk.Button(
        btn_frame,
        text="Cancel",
        command=popup.destroy,
        bg="#95a5a6",
        fg="white",
        width=12,
        font=("Arial", 10, "bold"),
        cursor="hand2"
    ).pack(side="left", padx=15)


def execute_ai_action(query, action, error_message=None, parent_window=None):
    """
    Execute the selected AI action (debug, explain, or chat).
    """
    config = load_config()
    provider = config.get("ai_provider", "groq").lower()
    
    # Check API key
    if provider != "ollama":
        api_key = config.get(f"{provider}_api_key")
        if not api_key:
            messagebox.showerror("Missing API Key",
                                 f"No API key found for {provider.capitalize()}.\n"
                                 "Please set API key in Settings.")
            return

    # Build the appropriate prompt based on action
    if action == "debug":
        system_prompt = (
            "You are an expert SQL Server developer. "
            "Debug the SQL query, identify any errors, performance issues, security risks, "
            "and suggest corrections and improvements."
        )
        if error_message:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nThe query produced the following error:\n```\n{error_message}\n```\n\nPlease debug and fix this query."
        else:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nPlease debug and identify any potential issues."
    elif action == "explain":
        system_prompt = (
            "You are an expert SQL Server developer. "
            "Explain the SQL query clearly, breaking down each part, "
            "describing what it does, and highlighting best practices."
        )
        if error_message:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nThe query produced the following error:\n```\n{error_message}\n```\n\nPlease explain what this query does and address the error."
        else:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nPlease explain what this query does in detail."
    else:  # chat
        system_prompt = (
            "You are a helpful SQL assistant. "
            "Answer questions about the SQL query in a conversational way. "
            "Provide clarifications, suggestions, and help the user understand better."
        )
        if error_message:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nThe query produced the following error:\n```\n{error_message}\n```\n\nI have questions about this query."
        else:
            user_content = f"Here is the SQL query:\n```sql\n{query}\n```\n\nI have questions about this query."

    try:
        ai_answer = ""

        if provider == "groq":
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model="openai/gpt-oss-120b",
                temperature=0.65,
                max_tokens=1200,
                top_p=0.9
            )
            ai_answer = response.choices[0].message.content.strip()

        elif provider == "gemini":
            client = genai.Client(api_key=api_key)
            prompt_text = f"{system_prompt}\n\n{user_content}"
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1200
                )
            )
            ai_answer = response.text.strip()

        elif provider == "ollama":
            prompt_text = f"{system_prompt}\n\n{user_content}"
            ai_answer = generate_from_ollama(prompt_text)

        else:
            messagebox.showerror("Invalid Provider", f"Unknown provider: {provider}")
            return

        # Show result in popup
        if action == "chat":
            show_chat_window(query, error_message, parent_window)
        else:
            show_ai_result_window(ai_answer, provider, action, parent_window)

    except Exception as e:
        messagebox.showerror(
            "AI Error",
            f"{provider.capitalize()} failed:\n\n{str(e)}\n\n"
            f"Check your API key and internet connection."
        )


def show_ai_result_window(ai_answer, provider, action, parent_window=None):
    """Show the AI response in a popup window."""
    popup = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
    
    action_titles = {
        "debug": "AI Debug Result",
        "explain": "AI Explanation",
        "chat": "AI Chat"
    }
    
    popup.title(f"{action_titles.get(action, 'AI Result')} – {provider.capitalize()}")
    popup.geometry("900x700")
    popup.minsize(700, 500)
    if parent_window:
        popup.transient(parent_window)
    popup.grab_set()

    # Header
    header_frame = tk.Frame(popup)
    header_frame.pack(fill="x", padx=12, pady=(12, 5))
    
    action_colors = {
        "debug": "#e74c3c",
        "explain": "#3498db",
        "chat": "#9b59b6"
    }
    
    tk.Label(
        header_frame,
        text=f"{action_titles.get(action, 'AI Result')} from {provider.capitalize()}",
        font=("Arial", 13, "bold"),
        fg=action_colors.get(action, "#2c3e50")
    ).pack(side="left")

    # Main text area
    text_area = scrolledtext.ScrolledText(
        popup,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#ffffff",
        fg="#1a1a1a",
        padx=12, pady=12
    )
    text_area.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    # Apply markdown formatting
    apply_markdown(text_area, ai_answer)
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


def show_chat_window(query, error_message=None, parent_window=None):
    """Show an interactive chat window for the SQL query."""
    config = load_config()
    provider = config.get("ai_provider", "groq").lower()
    
    # Check API key
    if provider != "ollama":
        api_key = config.get(f"{provider}_api_key")
        if not api_key:
            messagebox.showerror("Missing API Key",
                                 f"No API key found for {provider.capitalize()}.\n"
                                 "Please set API key in Settings.")
            return

    # Initialize chat history
    system_prompt = (
        "You are a helpful SQL assistant. "
        "Answer questions about the SQL query in a conversational way. "
        "Provide clarifications, suggestions, and help the user understand better."
    )
    
    conversation_history = []
    conversation_history.append({"role": "system", "content": system_prompt})
    
    # Initial user message
    if error_message:
        initial_message = f"Here is the SQL query:\n```sql\n{query}\n```\n\nThe query produced the following error:\n```\n{error_message}\n```\n\nI have questions about this query."
    else:
        initial_message = f"Here is the SQL query:\n```sql\n{query}\n```\n\nI have questions about this query."
    
    conversation_history.append({"role": "user", "content": initial_message})

    # Sending flag to prevent double-sends
    is_sending = [False]  # Use list to allow mutation in nested function
    
    # Create chat popup
    popup = tk.Toplevel(parent_window) if parent_window else tk.Toplevel()
    popup.title(f"AI Chat – {provider.capitalize()}")
    popup.geometry("800x650")
    popup.minsize(600, 500)
    if parent_window:
        popup.transient(parent_window)
    popup.grab_set()

    # Header with query preview
    header_frame = tk.Frame(popup, bg="#9b59b6")
    header_frame.pack(fill="x")
    
    tk.Label(
        header_frame,
        text="AI Chat Assistant",
        font=("Arial", 13, "bold"),
        fg="white",
        bg="#9b59b6",
        pady=8
    ).pack(side="left", padx=12)

    # Query preview button
    def show_query_preview():
        preview = tk.Toplevel(popup)
        preview.title("SQL Query")
        preview.geometry("600x300")
        preview.transient(popup)
        preview.grab_set()
        
        text = scrolledtext.ScrolledText(
            preview,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f9fa",
            padx=10, pady=10
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", query)
        text.config(state="disabled")
        
        tk.Button(preview, text="Close", command=preview.destroy, width=12).pack(pady=10)

    tk.Button(
        header_frame,
        text="Show Query",
        command=show_query_preview,
        bg="#8e44ad",
        fg="white",
        font=("Arial", 9, "bold"),
        cursor="hand2"
    ).pack(side="right", padx=12, pady=5)

    # Main content frame using grid layout
    content_frame = tk.Frame(popup, bg="#ffffff")
    content_frame.pack(fill="both", expand=True, padx=12, pady=(10, 12))
    content_frame.grid_rowconfigure(1, weight=1)  # Chat area expands
    content_frame.grid_rowconfigure(2, weight=0)  # Input area fixed
    content_frame.grid_columnconfigure(0, weight=1)
    
    # Chat display area (row 1)
    chat_frame = tk.Frame(content_frame, bg="#ffffff")
    chat_frame.grid(row=1, column=0, sticky="nsew")
    
    chat_text = scrolledtext.ScrolledText(
        chat_frame,
        wrap=tk.WORD,
        font=("Arial", 11),
        bg="#ffffff",
        fg="#1a1a1a",
        padx=12, pady=12,
        height=15  # Minimum height
    )
    chat_text.pack(fill="both", expand=True)
    chat_text.config(state="disabled")

    def add_message(sender, message, is_user=True):
        """Add a message to the chat display."""
        chat_text.config(state="normal")
        
        if is_user:
            chat_text.insert("end", f"\nYou:\n", "user_tag")
            chat_text.insert("end", f"{message}\n")
        else:
            chat_text.insert("end", f"\nAI:\n", "ai_tag")
            apply_markdown(chat_text, message)
        
        chat_text.insert("end", "\n" + "-" * 40 + "\n")
        chat_text.see("end")
        chat_text.config(state="disabled")

    # Configure tags
    chat_text.tag_config("user_tag", foreground="#2980b9", font=("Arial", 11, "bold"))
    chat_text.tag_config("ai_tag", foreground="#9b59b6", font=("Arial", 11, "bold"))

    # Input area (row 2)
    input_frame = tk.Frame(content_frame, bg="#ecf0f1")
    input_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    input_frame.grid_columnconfigure(0, weight=1)
    
    tk.Label(input_frame, text="Type your message:", font=("Arial", 10, "bold"), bg="#ecf0f1").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 3))
    
    input_text = tk.Text(input_frame, height=3, font=("Arial", 11), wrap=tk.WORD)
    input_text.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 8))

    # Buttons frame - must be defined before send_message
    btn_frame = tk.Frame(input_frame, bg="#ecf0f1")
    btn_frame.grid(row=2, column=0, sticky="e", pady=(0, 5))
    
    send_btn = tk.Button(
        btn_frame,
        text="Send",
        width=12,
        font=("Arial", 11, "bold"),
        bg="#9b59b6",
        fg="white",
        cursor="hand2"
    )
    send_btn.pack(side="right", padx=5)
    
    tk.Button(
        btn_frame,
        text="Close",
        command=popup.destroy,
        width=12,
        font=("Arial", 11, "bold"),
        bg="#6c757d",
        fg="white",
        cursor="hand2"
    ).pack(side="right", padx=5)

    def send_message():
        """Send user message and get AI response."""
        if is_sending[0]:
            return  # Prevent double-sends
            
        user_msg = input_text.get("1.0", "end-1c").strip()
        if not user_msg:
            return
        
        input_text.delete("1.0", "end")
        
        # Add user message to chat
        add_message("user", user_msg, is_user=True)
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_msg})
        
        # Mark as sending
        is_sending[0] = True
        send_btn.config(state="disabled", text="Sending...")
        
        # Get AI response
        try:
            ai_response = ""
            
            if provider == "groq":
                client = Groq(api_key=api_key)
                # Convert history to API format
                api_messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
                response = client.chat.completions.create(
                    messages=api_messages,
                    model="openai/gpt-oss-120b",
                    temperature=0.65,
                    max_tokens=1200
                )
                ai_response = response.choices[0].message.content.strip()
            
            elif provider == "gemini":
                client = genai.Client(api_key=api_key)
                # Build conversation for Gemini
                conversation_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in conversation_history])
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=conversation_text,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1200
                    )
                )
                ai_response = response.text.strip()
            
            elif provider == "ollama":
                # Build conversation for Ollama
                conversation_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in conversation_history])
                ai_response = generate_from_ollama(conversation_text)
            
            # Add AI response to chat and history
            add_message("ai", ai_response, is_user=False)
            conversation_history.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            add_message("ai", f"Error: {str(e)}", is_user=False)
            messagebox.showerror("AI Error", f"{provider.capitalize()} failed: {str(e)}")
        
        # Re-enable input
        is_sending[0] = False
        send_btn.config(state="normal", text="Send")
        input_text.focus_set()
    
    # Now bind the key and set command after send_message is defined
    input_text.bind("<Return>", lambda e: send_message() if not e.state & 0x1 else None)
    input_text.bind("<Shift-Return>", lambda e: None)
    send_btn.config(command=send_message)

    # Display initial messages
    add_message("user", initial_message, is_user=True)
    
    # Mark as sending during initial response
    is_sending[0] = True
    send_btn.config(state="disabled", text="Loading...")
    
    # Get and display initial AI response
    def get_initial_response():
        try:
            ai_response = ""
            
            if provider == "groq":
                client = Groq(api_key=api_key)
                api_messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
                response = client.chat.completions.create(
                    messages=api_messages,
                    model="openai/gpt-oss-120b",
                    temperature=0.65,
                    max_tokens=1200
                )
                ai_response = response.choices[0].message.content.strip()
            
            elif provider == "gemini":
                client = genai.Client(api_key=api_key)
                conversation_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in conversation_history])
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=conversation_text,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1200
                    )
                )
                ai_response = response.text.strip()
            
            elif provider == "ollama":
                conversation_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in conversation_history])
                ai_response = generate_from_ollama(conversation_text)
            
            add_message("ai", ai_response, is_user=False)
            conversation_history.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            add_message("ai", f"Error: {str(e)}", is_user=False)
            messagebox.showerror("AI Error", f"{provider.capitalize()} failed: {str(e)}")
        
        # Re-enable for user input
        is_sending[0] = False
        send_btn.config(state="normal", text="Send")
        input_text.focus_set()
    
    # Get initial response after window is shown
    popup.after(500, get_initial_response)
    
    # Focus on input
    input_text.focus_set()
