# SQL Training App

A simple, offline SQL training application built with Python and Tkinter. Perfect for practicing SQL queries on your local Microsoft SQL Server database without needing the internet or complex tools.

## Features

- **Clean GUI**: Write SQL queries on the left, see nicely formatted results below
- **Permanent Snippets Panel**: Favorite queries always visible on the right side — click to load instantly
- **Save Current Query as Snippet**: One-click save with overwrite protection
- **Multiple Result Sets**: Run several SELECT statements at once — each table displays separately with headers
- **Beautiful Table Formatting**: Aligned columns, clear separators, NULL handling
- **Export Results**: Save query results to CSV or Excel with a friendly dialog (CSV selected by default)
- **Fully Offline**: Everything runs locally — no cloud dependencies
- **Persistent Snippets**: Saved automatically to `snippets.json` in the project folder
- **Single File**: Everything is now contained in one easy-to-manage `sql_gui.py` file

## Project Structure
├── sql_gui.py              # Complete application (GUI, database, snippets, export)
├── snippets.example.json   # Template/example snippets (copy to snippets.json if desired)
├── .gitignore              # Ignores private files like snippets.json
└── README.md               # This file
text## Requirements

- Python 3.7+
- Microsoft SQL Server (tested with SQL Server Express)
- Required packages:
  ```bash
  pip install pyodbc pandas openpyxl
Setup
1. Install Dependencies
Bashpip install pyodbc pandas openpyxl
2. Configure Database Connection
The connection string is near the top of sql_gui.py:
PythonCONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=test;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
Adjust if needed:

Different server → change SERVER=
SQL login → replace Trusted_Connection=yes; with UID=username;PWD=password;
Different database → change DATABASE=test;

3. Create Test Database (Recommended)
In SSMS or any SQL client:
SQLCREATE DATABASE test;
GO
USE test;
GO
-- Create your tables here
4. Snippets Setup
Your personal saved queries are stored in snippets.json.
Important: snippets.json is private

This file is ignored by Git (via .gitignore) to keep your personal queries private.
The app will automatically create an empty snippets.json the first time you save a snippet.
A template file snippets.example.json is provided — you can copy/rename it to snippets.json if you want starter examples.

5. Run the Application
Bashpython sql_gui.py
Usage
Writing and Executing Queries

Type your SQL query in the top text area
Click Run Query (or press Ctrl+Enter)
View results in the formatted table below
Use Clear to reset query and results

Button layout (top row):
text[ Run Query ] [ Clear ] [ Save as Snippet ]                                         [ Export Results ]
Managing Snippets

Save Current Query: Click Save as Snippet → enter a name (will ask to overwrite if exists)
Use a Snippet: Click any snippet in the right panel to load it into the editor
Search: Type in the search box above the snippet list to filter
Add / Edit / Delete: Use the small buttons below the snippet list

Exporting Results

Run a query to populate the results table
Click Export Results (button on the far right)
A small dialog appears — choose CSV (default) or Excel
Click Export and choose save location
File is saved with headers and all rows preserved (suggested filename: query_results.csv or .xlsx)

Troubleshooting
Connection Issues:

Verify SQL Server is running
Check server name (localhost\SQLEXPRESS for default Express)
Ensure Windows Authentication or correct credentials
Confirm database exists

Driver Issues:

Install ODBC Driver 18: Microsoft download page

Export Issues:

Make sure you have results displayed first
Install pandas and openpyxl if Excel export fails

Version Control with Git
Bashgit init
git add sql_gui.py README.md snippets.example.json .gitignore
git commit -m "Initial commit"
Important: snippets.json is already ignored — your personal queries stay private and local.
License
Free to use for personal and educational purposes.

Enjoy practicing SQL! 🚀
textThis README is fully updated for your **current single-file version** of the app.  
Just replace the content of your `readme.md` (note: it's `readme.md`, not `readme.dm` 😊) with the text above.

You're all set — clean code, clean docs, private snippets, and a professional look! 

Let me know what you'd like to add next (tooltips, dark mode, syntax highlighting, etc.). Happy coding!