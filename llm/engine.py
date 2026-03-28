import os

import requests
from env_config import get_required_env, load_project_env


load_project_env(__file__)
required = get_required_env(["OLLAMA_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT_SECONDS"])

OLLAMA_URL = required["OLLAMA_URL"]
OLLAMA_MODEL = required["OLLAMA_MODEL"]
OLLAMA_TIMEOUT_SECONDS = float(required["OLLAMA_TIMEOUT_SECONDS"])

def ask_llm(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("response", "")
    except requests.RequestException as exc:
        return f'{{"message":"LLM service unavailable: {str(exc)}"}}'