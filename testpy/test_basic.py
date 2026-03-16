"""Proper tests for SQL Playground system."""
import unittest
import os
import sys
import json
import sqlite3
import tempfile
import requests
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import snippets


class TestGroqConnection(unittest.TestCase):
    """Test 1: Groq API connection."""

    def test_groq_api_key_exists(self):
        """Test that Groq API key is configured."""
        cfg = config.load_config()
        groq_key = cfg.get("groq_api_key")
        self.assertIsNotNone(groq_key, "Groq API key should not be None")
        self.assertTrue(len(groq_key) > 0, "Groq API key should not be empty")
        # Groq keys typically start with 'gsk_'
        self.assertTrue(groq_key.startswith("gsk_"), "Groq API key should start with 'gsk_'")

    def test_groq_api_key_format(self):
        """Test that Groq API key has valid format."""
        cfg = config.load_config()
        groq_key = cfg.get("groq_api_key")
        if groq_key:
            # Basic format check
            self.assertGreater(len(groq_key), 20, "Groq API key should be reasonably long")

    @unittest.skipIf(os.getenv("CI") or not os.getenv("GROQ_API_KEY"), 
                "Skipping live API test in CI or without key")
    def test_groq_api_live_connection(self):
        """Test actual Groq API connection (requires API key)."""
        cfg = config.load_config()
        groq_key = cfg.get("groq_api_key")
        
        if not groq_key:
            self.skipTest("No Groq API key available")
        
        # Test Groq API endpoint
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": "Say 'test passed'"}],
            "max_tokens": 50
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            self.assertEqual(response.status_code, 200, 
                f"Groq API returned status {response.status_code}")
            data = response.json()
            self.assertIn("choices", data, "Response should contain 'choices'")
        except requests.exceptions.ConnectionError:
            self.fail("Cannot connect to Groq API")
        except requests.exceptions.Timeout:
            self.fail("Groq API request timed out")


class TestConfigLoading(unittest.TestCase):
    """Test 2: Config loading."""

    def test_config_loads(self):
        """Test that config loads without errors."""
        cfg = config.load_config()
        self.assertIsInstance(cfg, dict, "Config should be a dictionary")

    def test_config_has_required_keys(self):
        """Test that config has all required keys."""
        cfg = config.load_config()
        required_keys = ["ai_provider", "gemini_api_key", "groq_api_key", "ollama_url"]
        for key in required_keys:
            self.assertIn(key, cfg, f"Config should have '{key}' key")

    def test_config_ai_provider_valid(self):
        """Test that AI provider is valid."""
        cfg = config.load_config()
        valid_providers = ["groq", "gemini", "ollama"]
        self.assertIn(cfg["ai_provider"], valid_providers, 
            f"AI provider should be one of {valid_providers}")


class TestSnippetsAdd(unittest.TestCase):
    """Test 3: Snippets add functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a temporary file for snippets
        self.temp_snippets_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.json'
        )
        self.temp_snippets_file.write("[]")
        self.temp_snippets_file.close()
        
        # Patch the snippets file path
        self.original_file = snippets.SNIPPETS_FILE
        snippets.SNIPPETS_FILE = self.temp_snippets_file.name
        
        # Reload snippets to use temp file
        snippets.current_snippets = []
        snippets.load_snippets()

    def tearDown(self):
        """Clean up test fixtures."""
        snippets.SNIPPETS_FILE = self.original_file
        snippets.current_snippets = []
        
        # Clean up temp file
        try:
            os.unlink(self.temp_snippets_file.name)
        except:
            pass

    def test_add_snippet(self):
        """Test adding a new snippet."""
        snippets.add_snippet("Test Snippet", "SELECT * FROM users", "mssql")
        
        self.assertEqual(len(snippets.current_snippets), 1, 
                        "Should have 1 snippet after adding")
        self.assertEqual(snippets.current_snippets[0]["name"], "Test Snippet")
        self.assertEqual(snippets.current_snippets[0]["sql"], "SELECT * FROM users")
        self.assertEqual(snippets.current_snippets[0]["provider"], "mssql")

    def test_add_multiple_snippets(self):
        """Test adding multiple snippets."""
        snippets.add_snippet("Snippet 1", "SELECT 1", "mssql")
        snippets.add_snippet("Snippet 2", "SELECT 2", "sqlite")
        
        self.assertEqual(len(snippets.current_snippets), 2, 
                        "Should have 2 snippets after adding")


class TestSnippetsFiltering(unittest.TestCase):
    """Test 4: Snippets filtering."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_snippets_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.json'
        )
        test_snippets = [
            {"name": "Get Users", "sql": "SELECT * FROM users", "provider": "mssql"},
            {"name": "Get Orders", "sql": "SELECT * FROM orders", "provider": "sqlite"},
            {"name": "Users Stats", "sql": "SELECT COUNT(*) FROM users", "provider": "mssql"}
        ]
        json.dump(test_snippets, self.temp_snippets_file)
        self.temp_snippets_file.close()
        
        self.original_file = snippets.SNIPPETS_FILE
        snippets.SNIPPETS_FILE = self.temp_snippets_file.name
        snippets.load_snippets()

    def tearDown(self):
        """Clean up test fixtures."""
        snippets.SNIPPETS_FILE = self.original_file
        snippets.current_snippets = []
        
        try:
            os.unlink(self.temp_snippets_file.name)
        except:
            pass

    def test_filter_by_search_term(self):
        """Test filtering snippets by search term."""
        results = snippets.get_filtered_snippets(search_term="users")
        self.assertEqual(len(results), 2, "Should find 2 snippets with 'users'")

    def test_filter_by_provider(self):
        """Test filtering snippets by provider."""
        results = snippets.get_filtered_snippets(provider="mssql")
        self.assertEqual(len(results), 2, "Should find 2 MSSQL snippets")

    def test_filter_by_search_and_provider(self):
        """Test filtering by both search term and provider."""
        results = snippets.get_filtered_snippets(search_term="users", provider="mssql")
        self.assertEqual(len(results), 2, "Should find 2 matching snippets")


class TestSQLiteDatabase(unittest.TestCase):
    """Test 5: SQLite database connection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(
            delete=False, suffix='.db'
        )
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.db_path)
        except:
            pass

    def test_sqlite_connection(self):
        """Test SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        self.assertIsNotNone(conn, "Should be able to connect to SQLite")
        conn.close()

    def test_sqlite_create_table(self):
        """Test creating a table in SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
        result = cursor.fetchone()
        self.assertIsNotNone(result, "Table should be created")
        
        conn.close()

    def test_sqlite_insert_and_select(self):
        """Test inserting and selecting data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO users (name) VALUES ('Test User')")
        
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchone()
        
        self.assertEqual(result[1], "Test User", "Should retrieve inserted data")
        
        conn.close()


if __name__ == "__main__":
    unittest.main()
