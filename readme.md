# SQL Training App

A powerful, offline/online SQL training application built with Python and Tkinter. Perfect for practicing SQL queries on your local Microsoft SQL Server database without needing the internet or complex tools.

## ✨ Features

### Core Functionality
- **Clean GUI**: Write SQL queries in a resizable editor, see beautifully formatted results below
- **Resizable Panes**: Drag the divider to adjust query editor vs results view size
- **Permanent Snippets Panel**: Favorite queries always visible on the right side — click to load instantly
- **Save Current Query as Snippet**: One-click save with overwrite protection
- **Multiple Result Sets**: Run several SELECT statements at once — each table displays separately with headers
- **Beautiful Table Formatting**: Aligned columns, clear separators, NULL handling, zebra-striped rows
- **Syntax Highlighting**: SQL keywords, strings, and comments are color-coded in the editor
- **Export Results**: Save query results to CSV or Excel with a friendly dialog
- **Copy to Clipboard**: One-click copy of results, paste directly into Excel
- **Offline/Online**: Everything runs locally with ollama model — no cloud dependencies, or with online AI models as well
- **Dual Database Support**: Switch between Microsoft SQL Server and SQLite databases seamlessly

### Snippets Management
- **Provider Filtering**: Filter snippets by database type (All / SQLite / MSSQL)
- **Auto-tagging**: Snippets are automatically tagged with the current database provider when saved
- **Drag & Drop Reordering**: Click and drag snippets to reorder them
- **Right-Click Context Menu**: Edit or delete snippets with right-click
- **Search/Filter**: Type in the search box to instantly filter snippets
- **Large Edit Dialog**: Edit snippets in a spacious, resizable dialog window
- **Persistent Storage**: Saved automatically to `snippets.json` in the project folder

### Query History
- **Full History Tracking**: Every executed query is automatically saved with:
  - Timestamp (YYYY-MM-DD HH:MM:SS)
  - Query preview (truncated for display)
  - Result status (success/error with row count or error message)
- **Visual Status Indicators**: Success queries in green, errors in red
- **Quick Reload**: Double-click any history entry to load the query back into the editor
- **Right-Click Options**:
  - **Load Query** – reload the selected query
  - **Delete Entry** – remove just that history item
  - **Clear All History** – delete all history (with confirmation)
- **Auto-Cleanup**: Automatically keeps only the last 100 queries (most recent first)
- **Persistent Storage**: History saved to `history.json` and survives app restarts

### Database Management
- **Change Database**: Click the "Change DB" button to switch databases on the fly
- **Dynamic Connection**: Database name shown in the title and updates in real-time

### SQLite Explorer
- **Tree View Browser**: Explore SQLite database schema in a hierarchical tree
- **Tables, Views, & Indexes**: See all database objects organized by type
- **Column Details**: Expand any table to see columns, types, NULL settings, defaults, and primary keys
- **Quick Queries**: Double-click a table to auto-generate a SELECT query (100 rows)
- **Context Menu**: Right-click for SELECT COUNT, SHOW CREATE, and other quick actions
- **Filter/Search**: Type in the search box to filter tables by name
- **Auto-Refresh**: Click the refresh button (⟳) to reload schema after changes

## 📁 Project Structure

```
├── .env
├── .gitignore
├── __pycache__/
├── SQLiteExplorer.py
├── config.py
├── config.json
├── database.py
├── debug_ai.py
├── export.py
├── history.py
├── history.json
├── main.py
├── ollama_client.py
├── settings.py
├── snippets.py
├── snippets.json
├── snippets.example.json
└── readme.md
```
├── readme.md (2600 tokens)
└── main.py (9100 tokens)
```

## 🔧 Requirements

- **Python 3.7+** (SQLite support is built-in, no extra package needed)
- **Microsoft SQL Server** (tested with SQL Server Express) — only if using SQL Server mode
- **Required packages**:
  ```bash
  pip install pyodbc pandas openpyxl
  ```

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install pyodbc pandas openpyxl
```

### 2. Configure Database Connection

The connection string is in `main.py` (around line 132):

```python
def get_conn_str(db_name):
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        f"DATABASE={db_name};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
```

Adjust if needed:
- Different server → change `SERVER=`
- SQL login → replace `Trusted_Connection=yes;` with `UID=username;PWD=password;`
- Different database → change the `current_db = "test"` variable

### 3. Create Test Database (Recommended)

In SSMS or any SQL client:

```sql
CREATE DATABASE test;
GO
USE test;
GO
-- Create your tables here
```

### 4. Files Setup

**Snippets (`snippets.json`)**
- This file is ignored by Git (via `.gitignore`) to keep your personal queries private
- The app will automatically create an empty `snippets.json` the first time you save a snippet
- A template file `snippets.example.json` is provided — copy/rename it to `snippets.json` for starter examples

**History (`history.json`)**
- Also ignored by Git for privacy
- Auto-created on first query execution
- Stores last 100 queries with timestamps and results

### 5. Run the Application

```bash
python main.py
```

## 📖 Usage

### Writing and Executing Queries

1. Type your SQL query in the top text area (with syntax highlighting!)
2. Click **Run Query** (or press `Ctrl+Enter`)
3. View results in the formatted table below
4. Use **Clear** to reset query and results

**Button layout:**
```
[ Run Query ] [ Clear ] [ Save as Snippet ] [ Debug with AI ]     [ Copy Results ] [ Export Results ]
                                                    [ Change DB ] [ Settings ]
```

### Managing Snippets

- **Save Current Query**: Click **Save as Snippet** → enter a name (will ask to overwrite if exists)
- **Use a Snippet**: Click any snippet in the right panel to load it into the editor
- **Search**: Type in the search box above the snippet list to filter by name
- **Edit**: Right-click snippet → **Edit** (opens large dialog for easy editing)
- **Delete**: Right-click snippet → **Delete** (with confirmation)
- **Reorder**: Click and drag snippets to change their order
- **Navigate**: Use arrow keys (↑/↓) to browse snippets, press Enter to load

### Using Query History

1. Click the **History** tab at the bottom to view all past queries
2. History shows:
   - **Time**: When the query was executed
   - **Query**: Preview of the SQL (first 60 characters)
   - **Result**: Number of rows returned or error message
3. **Double-click** any entry to reload that query into the editor
4. **Right-click** for options:
   - Load Query
   - Delete Entry
   - Clear All History (removes everything with confirmation)
5. **Color coding**: Success = green, Errors = red

### Exporting Results

1. Run a query to populate the results table
2. Click **Export Results** (button on the right)
3. A dialog appears — choose CSV (default) or Excel
4. Click **Export** and choose save location
5. File is saved with headers and all rows preserved

### Copying Results

1. Run a query
2. Click **Copy Results**
3. Paste directly into Excel, Google Sheets, or any spreadsheet app
4. Headers and formatting are preserved

### Changing Database

**Using the Title Bar:**
- The DB provider selector (SQLite / MS SQL) is in the title bar on the top right
- Click the radio button to switch between providers
- The current database name is shown next to "SQL Query:" label

**Using the Change DB Button:**
1. Click **Change DB** button (blue button in snippets section)
2. Enter new database name
3. App reconnects and updates the title
4. Previous results are cleared

### Using SQLite

The app supports both Microsoft SQL Server and SQLite databases.

**Multiple Statements:**
- In SQLite mode, you can run multiple SQL statements at once by separating them with semicolons
- Each SELECT statement will show in a separate result tab
- Example:
  ```sql
  SELECT * FROM users;
  SELECT * FROM orders WHERE total > 100;
  INSERT INTO logs VALUES ('action completed');
  ```

**Switching to SQLite:**
1. Click the **Settings** button (gear icon) in the right panel
2. Select **SQLite** radio button in the "Database Provider" section
3. Click **Browse** to select a `.db`, `.sqlite`, or `.sqlite3` file
4. Click **Save** — the app will reconnect using SQLite

**SQLite Explorer Panel:**
- Located in the right panel (second tab below Snippets)
- Shows a tree with Tables, Views, and Indexes
- Click the arrow ▶ to expand a table and see its columns
- **Double-click** any table to load `SELECT * FROM table LIMIT 100;` into the editor
- **Right-click** a table for quick actions:
  - SELECT * FROM table (100 rows)
  - SELECT COUNT(*) FROM table
  - Show CREATE statement
- Use the **search box** to filter tables by name
- Click **⟳** to refresh the schema

**Switching back to SQL Server:**
1. Open Settings
2. Select **SQL Server** radio button
3. Click **Change DB** to select a different SQL Server database

## ⌨️ Keyboard Shortcuts

- `Ctrl+Enter` - Run current query
- `Ctrl+S` - Save as snippet (when query editor is focused)
- `↑/↓` - Navigate snippets (when snippet list is focused)
- `Enter` - Load selected snippet (when snippet list is focused)

## 🤖 AI Assistant (Groq & Gemini & local ollama model )
- **SQL Expert Mode**: Get instant explanations of complex queries.
- **Code Optimization**: AI suggests performance improvements and best practices.
- **Security Auditing**: Detects potential SQL injection or risky operations.
- **Provider Support**: Switch between **Groq** (fast & inexpensive) and **Gemini** (Google) or your own local **Ollama model** via the Settings dialog. The code currently uses a Gemini model string such as `gemini-2.5-flash-lite` in `debug_ai.py` (the exact model can be adjusted in the code).
- **Visual Status**: The status bar includes an `AI:` label that shows the selected provider (initial value shown at app start).

### Known issue (status update)

- The `debug_ai.py` module contains an `update_ai_status()` implementation that calls itself recursively; this causes a crash if that function is invoked. The status label still shows the initial provider value from `main.py`, and changing the provider via Settings updates `config.json` — but automatic background updates using `update_ai_status()` are currently broken. This is documented here so you (or a future contributor) can safely fix the function in code.

## 🐛 Troubleshooting

### Connection Issues:

- Verify SQL Server is running
- Check server name (`localhost\SQLEXPRESS` for default Express installation)
- Ensure Windows Authentication or correct credentials
- Confirm database exists

### Driver Issues:

- Install ODBC Driver 18: [Microsoft download page](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- For older drivers, change connection string to use `ODBC Driver 17` or `SQL Server`

### Export Issues:

- Make sure you have results displayed first
- Install `pandas` and `openpyxl` if Excel export fails
- Check write permissions in the target directory

### History Not Showing:

- Check that `history.py` is in the same directory as `main.py`
- Ensure `history.json` is not corrupted (delete it to reset)
- Verify queries are actually executing (check for error messages)

## 🔒 Privacy & Git

The `.gitignore` file excludes:
- `snippets.json` - Your personal saved queries
- `history.json` - Your query execution history
- `config.json` - Your API_KEY's for Gemini and Groq
- `__pycache__/` - Python cache files

This ensures your personal work stays private when using version control.

```bash
git init
git add main.py database.py snippets.py history.py export.py README.md snippets.example.json .gitignore
git commit -m "Initial commit"
```

## 📝 Files Explained

- **`main.py`** - Main application with GUI, event handlers, and layout
- **`database.py`** - Database connection and query execution logic (supports SQL Server and SQLite)
- **`snippets.py`** - Functions for loading, saving, and managing snippets
- **`history.py`** - Functions for tracking and managing query history
- **`export.py`** - CSV and Excel export functionality
- **`snippets.json`** - Your saved queries (private, auto-generated)
- **`history.json`** - Your query history (private, auto-generated)
- **`snippets_example.json`** - Template with example SQL snippets
- **`settings.py`** - GUI for selecting AI providers and database type
- **`debug_ai.py`** - Logic for communicating with Groq/Gemini and displaying SQL explanations
- **`config.py`** - Helper functions to load and save `config.json`
- **`config.json`** - Stores your active AI provider, API keys, and database settings (Git-ignored)
- **`SQLiteExplorer.py`** - Tree-based SQLite schema browser panel

## 📊 Recent Changes

### Latest Updates:
✅ Multiple SQL statements — run multiple queries at once in SQLite (separated by semicolons)
✅ Snippets provider filtering — filter snippets by SQLite, MSSQL, or All
✅ DB provider selector moved — SQLite/MS SQL radio buttons now in title bar (top right)
✅ SQLite support — work with local .db/.sqlite files
✅ SQLite Explorer panel — tree view of tables, views, indexes, and columns
✅ Dual database mode — switch between SQL Server and SQLite via Settings
✅ Quick query generation — double-click tables in explorer to auto-generate SELECT
✅ Context menu actions — right-click tables for COUNT, CREATE statement, etc.
✅ Filter/search in explorer — quickly find tables by name
✅ Query history tracking with timestamp and results
✅ Drag & drop snippet reordering
✅ Right-click context menus for snippets and history
✅ Large edit dialog for snippets (700x500, resizable)
✅ Resizable query editor and results panes
✅ Fixed: History tab persists through query runs
✅ Fixed: Export functionality restored
✅ Improved: Edit dialog now properly sized and usable

## 📜 License

Free to use for personal and educational purposes.

---

**Enjoy practicing SQL!** 🚀💾🔍