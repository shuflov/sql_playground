import sqlite3
import tkinter as tk
from tkinter import ttk


class SQLiteExplorer:
    """
    A tree-based SQLite schema explorer panel.
    Shows tables, views, columns, and types.
    Double-clicking a table loads a SELECT query into the editor.
    """

    def __init__(self, parent, query_text_widget, highlight_fn=None):
        self.parent = parent
        self.query_text = query_text_widget
        self.highlight_fn = highlight_fn
        self.db_path = None

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.parent, bg="#e1e1e1")
        header.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(
            header, text="SQLite Explorer",
            bg="#e1e1e1", font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(
            header, text="No DB connected",
            bg="#e1e1e1", fg="#888", font=("Arial", 8, "italic")
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Refresh button
        tk.Button(
            header, text="⟳", command=self.refresh,
            bg="#e1e1e1", relief="flat", font=("Arial", 12), cursor="hand2"
        ).pack(side=tk.RIGHT)

        # Search bar
        search_frame = tk.Frame(self.parent, bg="#e1e1e1")
        search_frame.pack(fill="x", padx=10, pady=(0, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 9))
        search_entry.pack(fill="x")
        tk.Label(search_frame, text="Filter tables...", bg="#e1e1e1", fg="#aaa",
                 font=("Arial", 8)).pack(anchor="w")

        # Treeview
        tree_frame = tk.Frame(self.parent, bg="#e1e1e1")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.tree.column("#0", stretch=True)

        vsb = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        vsb.pack(side=tk.RIGHT, fill="y")

        # Tags for styling
        self.tree.tag_configure("table",   foreground="#1a3e6e", font=("Consolas", 10, "bold"))
        self.tree.tag_configure("view",    foreground="#5a2d82", font=("Consolas", 10, "bold"))
        self.tree.tag_configure("column",  foreground="#333",    font=("Consolas", 9))
        self.tree.tag_configure("pk",      foreground="#b8400b", font=("Consolas", 9, "bold"))
        self.tree.tag_configure("section", foreground="#555",    font=("Arial", 9, "italic"))

        # Bindings
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>",   self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)

        # Bottom info bar
        self.info_label = tk.Label(
            self.parent, text="",
            bg="#d4d4d4", fg="#333",
            font=("Arial", 8), anchor="w", padx=5
        )
        self.info_label.pack(fill="x", side=tk.BOTTOM)

        # Context menu
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="SELECT * FROM table (100 rows)", command=self._select_table)
        self.context_menu.add_command(label="SELECT COUNT(*) FROM table",     command=self._count_table)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show CREATE statement",          command=self._show_create)
        self.tree.bind("<Button-3>", self._show_context_menu)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_database(self, db_path: str):
        """Call this whenever the user connects to a new SQLite file."""
        self.db_path = db_path
        self.refresh()

    def clear(self):
        """Clear the tree (called when switching away from SQLite)."""
        self.db_path = None
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text="No DB connected")
        self.info_label.config(text="")

    def refresh(self):
        if not self.db_path:
            return
        self.tree.delete(*self.tree.get_children())
        self._load_schema()

    # ------------------------------------------------------------------
    # Schema loading
    # ------------------------------------------------------------------

    def _load_schema(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # ---- Tables ----
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [r[0] for r in cur.fetchall()]

            tables_node = self.tree.insert(
                "", "end", text=f"📋 Tables  ({len(tables)})",
                open=True, tags=("section",)
            )

            for tbl in tables:
                tbl_node = self.tree.insert(
                    tables_node, "end",
                    text=f"🗃  {tbl}",
                    tags=("table",),
                    values=(tbl, "table")
                )
                # Placeholder so the expand arrow appears
                self.tree.insert(tbl_node, "end", text="Loading…", tags=("section",))

            # ---- Views ----
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            )
            views = [r[0] for r in cur.fetchall()]

            if views:
                views_node = self.tree.insert(
                    "", "end", text=f"👁  Views  ({len(views)})",
                    open=False, tags=("section",)
                )
                for v in views:
                    self.tree.insert(
                        views_node, "end",
                        text=f"🔍  {v}",
                        tags=("view",),
                        values=(v, "view")
                    )

            # ---- Indexes ----
            cur.execute(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name"
            )
            indexes = cur.fetchall()

            if indexes:
                idx_node = self.tree.insert(
                    "", "end", text=f"🔑 Indexes  ({len(indexes)})",
                    open=False, tags=("section",)
                )
                for idx_name, tbl_name in indexes:
                    self.tree.insert(
                        idx_node, "end",
                        text=f"   {idx_name}  → {tbl_name}",
                        tags=("section",)
                    )

            conn.close()

            # Update status
            import os
            short = os.path.basename(self.db_path)
            self.status_label.config(
                text=f"{short}  •  {len(tables)} tables",
                fg="#1a6e1a"
            )
            self.info_label.config(
                text=f"Path: {self.db_path}"
            )

        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="red")

    def _load_columns_for(self, table_name, parent_node):
        """Load columns for a table node (lazy loading on expand)."""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info(\"{table_name}\")")
            cols = cur.fetchall()
            conn.close()

            for col in cols:
                # col: (cid, name, type, notnull, dflt_value, pk)
                cid, name, ctype, notnull, default, pk = col
                icon = "🔑" if pk else "  "
                not_null = " NOT NULL" if notnull else ""
                default_str = f"  default={default}" if default is not None else ""
                label = f"{icon} {name}  :  {ctype}{not_null}{default_str}"
                tag = "pk" if pk else "column"
                self.tree.insert(parent_node, "end", text=label, tags=(tag,))

        except Exception as e:
            self.tree.insert(parent_node, "end", text=f"Error: {e}", tags=("section",))

    def _on_expand(self, event):
        """Lazy-load columns when a table node is expanded."""
        node = self.tree.focus()
        values = self.tree.item(node, "values")
        if not values or values[1] != "table":
            return

        children = self.tree.get_children(node)
        # If only placeholder child
        if len(children) == 1 and self.tree.item(children[0], "text") == "Loading…":
            self.tree.delete(children[0])
            self._load_columns_for(values[0], node)

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def _get_selected_table(self):
        node = self.tree.focus()
        values = self.tree.item(node, "values")
        if values and values[1] in ("table", "view"):
            return values[0]
        return None

    def _on_double_click(self, event=None):
        table = self._get_selected_table()
        if table:
            self._load_select_query(table)

    def _select_table(self):
        table = self._get_selected_table()
        if table:
            self._load_select_query(table)

    def _count_table(self):
        table = self._get_selected_table()
        if not table:
            return
        sql = f"SELECT COUNT(*) AS row_count FROM \"{table}\";"
        self._set_query(sql)

    def _show_create(self):
        table = self._get_selected_table()
        if not table or not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT sql FROM sqlite_master WHERE name=?", (table,)
            )
            row = cur.fetchone()
            conn.close()
            if row:
                self._set_query(row[0])
        except Exception as e:
            pass

    def _load_select_query(self, table):
        sql = f"SELECT *\nFROM \"{table}\"\nLIMIT 100;"
        self._set_query(sql)

    def _set_query(self, sql):
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", sql)
        self.query_text.focus_set()
        if self.highlight_fn:
            self.highlight_fn()

    def _apply_filter(self):
        """Re-render tree showing only tables matching the search term."""
        term = self.search_var.get().lower().strip()
        # Simple approach: rebuild from scratch
        self.refresh()
        if not term:
            return
        # Hide non-matching table nodes
        for section_node in self.tree.get_children():
            for child in self.tree.get_children(section_node):
                label = self.tree.item(child, "text").lower()
                if term not in label:
                    self.tree.detach(child)

    def _show_context_menu(self, event):
        node = self.tree.identify_row(event.y)
        if node:
            self.tree.focus(node)
            self.tree.selection_set(node)
            if self._get_selected_table():
                self.context_menu.post(event.x_root, event.y_root)