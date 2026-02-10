# markdown_renderer.py
"""
Markdown renderer for tkinter text widgets.
Supports: code blocks, headers, bold, italic, and list formatting.
"""

import tkinter as tk
import re


def configure_tags(text_widget):
    """Configure text tags for markdown formatting."""
    
    # Code blocks - Consolas font with gray background
    text_widget.tag_configure(
        "code",
        font=("Consolas", 11),
        background="#f0f0f0",
        lmargin1=20,
        lmargin2=20,
        rmargin=10,
        spacing1=5,
        spacing3=5
    )
    
    # Headers - Bold Arial fonts with spacing
    text_widget.tag_configure(
        "header1",
        font=("Arial", 16, "bold"),
        foreground="#2c3e50",
        spacing1=10,
        spacing3=8
    )
    
    text_widget.tag_configure(
        "header2",
        font=("Arial", 14, "bold"),
        foreground="#2c3e50",
        spacing1=8,
        spacing3=6
    )
    
    text_widget.tag_configure(
        "header3",
        font=("Arial", 12, "bold"),
        foreground="#2c3e50",
        spacing1=6,
        spacing3=4
    )
    
    # Bold text
    text_widget.tag_configure(
        "bold",
        font=("Arial", 11, "bold")
    )
    
    # Italic text
    text_widget.tag_configure(
        "italic",
        font=("Arial", 11, "italic")
    )
    
    # List items
    text_widget.tag_configure(
        "list_item",
        lmargin1=30,
        lmargin2=30,
        spacing1=3,
        spacing3=3
    )
    
    # Bullet list items (with explicit bullet)
    text_widget.tag_configure(
        "bullet",
        lmargin1=20,
        lmargin2=35,
        spacing1=3,
        spacing3=3
    )


def escape_markdown(text):
    """Escape special tkinter regex characters."""
    special_chars = r'[\\.*?^${}|()[\]]'
    return re.sub(special_chars, lambda m: '\\' + m.group(), text)


def apply_markdown(text_widget, markdown_text):
    """
    Parse markdown text and apply formatting tags to the text widget.
    
    Args:
        text_widget: tkinter ScrolledText widget to format
        markdown_text: Raw markdown text string
    """
    # Clear existing text and configure tags
    text_widget.delete("1.0", tk.END)
    configure_tags(text_widget)
    
    # Process the markdown in order
    pos = 0
    text = markdown_text
    
    # 1. Process code blocks first (highest priority)
    code_pattern = r'```(\w*)\n([\s\S]*?)```'
    
    # Find all code blocks
    code_matches = list(re.finditer(code_pattern, text))
    
    if code_matches:
        for i, match in enumerate(code_matches):
            # Insert text before this code block
            before_code = text[pos:match.start()]
            if before_code:
                insert_formatted_text(text_widget, before_code)
            
            # Extract code content
            code_content = match.group(2).strip()
            lang = match.group(1)
            
            # Insert code with tag
            if code_content:
                text_widget.insert(tk.END, code_content + "\n", "code")
            
            pos = match.end()
        
        # Insert remaining text
        remaining = text[pos:]
        if remaining:
            insert_formatted_text(text_widget, remaining)
    else:
        # No code blocks, process all text
        insert_formatted_text(text_widget, text)


def insert_formatted_text(text_widget, text):
    """Insert text with inline formatting (headers, bold, italic, lists)."""
    
    # Process headers first
    header_patterns = [
        (r'^# (.+)$', "header1"),  # H1
        (r'^## (.+)$', "header2"),  # H2
        (r'^### (.+)$', "header3"),  # H3
    ]
    
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        formatted_line = line
        for pattern, tag in header_patterns:
            match = re.match(pattern, line)
            if match:
                header_text = match.group(1)
                # Apply inline formatting to header text
                header_text = apply_inline_formatting(header_text)
                formatted_line = header_text
                # We'll tag the entire line
                text_widget.insert(tk.END, formatted_line + "\n", tag)
                break
        else:
            # Not a header, process inline formatting
            processed_line = apply_inline_formatting(line)
            
            # Check for list items
            list_match = re.match(r'^(\s*)([-*]|\d+\.) (.+)$', line)
            if list_match:
                bullet = list_match.group(2)
                list_content = apply_inline_formatting(list_match.group(3))
                indent = list_match.group(1)
                
                if bullet in ['-', '*']:
                    text_widget.insert(tk.END, indent + "• " + list_content + "\n", "bullet")
                else:
                    text_widget.insert(tk.END, indent + list_content + "\n", "list_item")
            else:
                text_widget.insert(tk.END, processed_line + "\n")


def apply_inline_formatting(text):
    """Apply inline formatting (bold, italic) to text."""
    
    # Process bold first: **text**
    bold_pattern = r'\*\*(.+?)\*\*'
    text = re.sub(bold_pattern, r'\1', text)
    
    # Process italic: *text*
    italic_pattern = r'\*(.+?)\*'
    text = re.sub(italic_pattern, r'\1', text)
    
    # Process inline code: `code`
    # Note: We replace backticks with a marker for later processing
    inline_code_pattern = r'`([^`]+)`'
    text = re.sub(inline_code_pattern, r'\1', text)
    
    return text
