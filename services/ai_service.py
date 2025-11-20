# ocean-back/services/ai_service.py
import httpx
from typing import List, Dict, Any
from config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    # INCREASED default max_tokens from 800 -> 4000 to prevent cut-offs
    async def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4000) -> Dict[str, Any]:
        # Build prompt
        prompt_lines = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "")
            if role == "system":
                prompt_lines.append(f"SYSTEM INSTRUCTION: {text}")
            elif role == "user":
                prompt_lines.append(f"USER: {text}")
            else:
                prompt_lines.append(text)
        prompt_text = "\n\n".join(prompt_lines)

        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        headers = {"Content-Type": "application/json"}

        try:
            # Increased timeout to 60s because generating 4000 tokens takes longer
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.url}?key={self.api_key}", json=payload, headers=headers)
                data = resp.json()

                if resp.status_code != 200:
                    err = data.get("error", {}).get("message") if isinstance(data, dict) else resp.text
                    print(f"Gemini API Error: {err}")
                    return {"error": f"Google API error: {err}", "status": resp.status_code}

                content = None
                try:
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        
                        # Log if the model stopped early
                        if candidate.get("finishReason") != "STOP":
                            print(f"Warning: Generation stopped due to {candidate.get('finishReason')}")

                        # Extract text safely
                        if "content" in candidate and "parts" in candidate["content"]:
                            content = candidate["content"]["parts"][0]["text"]
                except Exception as e:
                    print(f"Parsing Error: {e}")
                    pass

                if not content:
                    # Fallback: Don't show raw JSON to the user
                    print(f"Raw Response (Empty content): {data}")
                    content = "Error: The AI could not generate content for this section. Please try refining the title or regenerating."

                return {"content": content, "status": 200}
        except Exception as e:
            return {"error": str(e), "status": 500}

ai_service = AIService()