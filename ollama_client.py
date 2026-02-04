# ollama_client.py

import requests
import json

# Ollama Settings (fixed for local development)
OLLAMA_URL = "http://localhost:11434"
CHAT_URL = f"{OLLAMA_URL}/api/chat"
TAGS_URL = f"{OLLAMA_URL}/api/tags"
MODEL = "mistral:7b"


def generate_from_ollama(prompt: str, model: str = MODEL, base_url: str = OLLAMA_URL, timeout: int = 30) -> str:
    """
    Generate a response from a local Ollama model.
    
    Args:
        prompt: The user prompt (full message including system context).
        model: The model name (default: mistral:7b).
        base_url: The base URL of the Ollama server (default: http://localhost:11434).
        timeout: Request timeout in seconds.
    
    Returns:
        The assistant's response text.
    
    Raises:
        ConnectionError: If Ollama server is unreachable.
        RuntimeError: If the API returns an error.
    """
    chat_url = f"{base_url}/api/chat"
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(chat_url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            f"Cannot connect to Ollama at {base_url}. "
            f"Ensure Ollama is running locally on port 11434.\n{str(e)}"
        ) from e
    except requests.exceptions.Timeout as e:
        raise TimeoutError(
            f"Ollama request timed out after {timeout}s. "
            f"The model might be slow or overloaded.\n{str(e)}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API error: {str(e)}") from e
    
    try:
        data = response.json()
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"].strip()
        else:
            raise RuntimeError(f"Unexpected Ollama response format: {data}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Ollama response: {str(e)}") from e
