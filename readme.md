# SQL Training App

A simple, offline SQL training application built with Python and Tkinter. Perfect for practicing SQL queries on your local Microsoft SQL Server database without needing the internet or complex tools.

## Features

- **Clean GUI**: Write SQL queries on the left, see nicely formatted results below
- **Permanent Snippets Panel**: Favorite queries always visible on the right side — click to load instantly
- **Save Current Query as Snippet**: One-click save with overwrite protection
- **Multiple Result Sets**: Run several SELECT statements at once — each table displays separately with headers
- **Beautiful Table Formatting**: Aligned columns, clear separators, NULL handling
- **Fully Offline**: Everything runs locally — no cloud dependencies
- **Persistent Snippets**: Saved automatically to `snippets.json` in the project folder
- **Git Ready**: Easy to version-control your progress

## Project Structure

```
├── sql_gui.py        # Main application file
├── snippets.json     # Your saved SQL snippets (auto-generated, kept private)
└── README.md         # This file
```

## Requirements

- Python 3.7+
- Microsoft SQL Server (tested with SQL Server 2025 Express)
- pyodbc: `pip install pyodbc`

## Setup

### 1. Install Dependencies

```bash
pip install pyodbc
```

### 2. Configure Database Connection

Inside `sql_gui.py`, the connection string is configured around line 110-117:

```python
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=test;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
```

**Default settings:**
- SQL Server Express named instance: `localhost\SQLEXPRESS`
- Windows Authentication
- Database: `test`

**If you need different settings**, modify the connection string:
- For SQL login: Replace `Trusted_Connection=yes;` with `UID=your_username;PWD=your_password;`
- For different server: Change `SERVER=localhost\\SQLEXPRESS;`
- For different database: Change `DATABASE=test;`

### 3. Create Test Database (Recommended)

Open SQL Server Management Studio (SSMS) or another SQL client and run:

```sql
CREATE DATABASE test;
GO
USE test;
```

### 4. Create your own snippets and store them in snippet.json file

### 5. Run the Application

```bash
python sql_gui.py
```

## Usage

### Writing and Executing Queries

1. Type your SQL query in the top text area
2. Click **Run Query** to execute
3. View results in the formatted table below
4. Use **Clear** to reset both query and results

### Managing Snippets

**Save Current Query:**
- Click **Save as Snippet** to save the current query
- Enter a name when prompted
- If the name exists, you'll be asked to confirm overwrite

**Using Saved Snippets:**
- All saved snippets appear in the right panel
- Single-click a snippet to load it into the query area
- Double-click also works

**Managing Snippets:**
- **Add**: Create a new snippet from scratch
- **Edit**: Modify an existing snippet's name or SQL
- **Delete**: Remove a snippet permanently

### Snippet File

The `snippets.json` file stores your saved queries and is automatically created on first use. This file contains your personal SQL practice work and should be kept private (add to `.gitignore` if using version control).


## Troubleshooting

**Connection Issues:**
- Verify SQL Server is running
- Check server name (use `localhost\SQLEXPRESS` for default Express installation)
- Ensure Windows Authentication is enabled, or add SQL login credentials
- Confirm the database exists

**Driver Issues:**
- Install ODBC Driver 18: Download from [Microsoft's website](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- If driver is not found, check available drivers: `pyodbc.drivers()`

**Snippets Not Saving:**
- Ensure `snippets.json` is in the same directory as `sql_gui.py`
- Check file permissions
- The file is created automatically on first save

## Contributing

This is a personal training tool, but feel free to:
- Fork and customize for your needs
- Add new features
- Share improvements

## Version Control with Git

To track your progress:

```bash
git init
git add sql_gui.py README.md
git commit -m "Initial commit"
```

**Important:** Add `snippets.json` to `.gitignore` to keep your personal queries private:

```bash
echo "snippets.json" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
git add .gitignore
git commit -m "Add gitignore"
```

## License

Free to use for personal and educational purposes.

## Feedback & Support

This is a learning tool. Experiment, break things, and learn from errors!
