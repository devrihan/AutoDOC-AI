# ocean-back/services/ai_service.py
import httpx
from typing import List, Dict, Any
from config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.url = f"https://generativelanguage.googleapis.com/v1beta2/models/{self.model}:generateText"

    async def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> Dict[str, Any]:
        # Build prompt
        prompt_lines = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")
            if role == "system":
                prompt_lines.append(f"SYSTEM: {text}")
            elif role == "user":
                prompt_lines.append(f"USER: {text}")
            else:
                prompt_lines.append(text)
        prompt_text = "\n\n".join(prompt_lines)

        payload = {
            "prompt": {"text": prompt_text},
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }

        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.url}?key={self.api_key}", json=payload, headers=headers)
                data = resp.json()

                if resp.status_code != 200:
                    err = data.get("error") if isinstance(data, dict) else resp.text
                    return {"error": f"API error: {err}", "status": resp.status_code}

                # Try common fields
                content = None
                if isinstance(data, dict):
                    if "candidates" in data:
                        try:
                            content = data["candidates"][0]["content"][0]["text"]
                        except Exception:
                            pass
                    if not content and "outputs" in data:
                        try:
                            content = data["outputs"][0]["content"][0]["text"]
                        except Exception:
                            pass
                    if not content:
                        # fallback to stringifying
                        import json as _json
                        content = _json.dumps(data)[:16000]

                if not content:
                    content = str(data)

                return {"content": content, "status": 200}
        except Exception as e:
            return {"error": str(e), "status": 500}

ai_service = AIService()
