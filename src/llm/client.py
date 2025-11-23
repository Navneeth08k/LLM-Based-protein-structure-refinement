import os
import json
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def query(self, prompt):
        pass

class MockLLMClient(LLMClient):
    """
    Mock client for testing without API keys.
    Returns a fixed plausible response.
    """
    def query(self, prompt):
        return {
            "secondary_structure_prediction": "Helix",
            "confidence": "Medium",
            "reasoning": "Sequence shows periodicity typical of alpha helices.",
            "constraints": ["Residue 1 and 4 should be close"]
        }

class OpenAIClient(LLMClient):
    """
    Client for OpenAI API.
    """
    def __init__(self, api_key=None, model="gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OpenAI API key not found.")
        
        # Import here to avoid dependency if not used
        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def query(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            return None

class GeminiClient(LLMClient):
    """
    Client for Google Gemini API.
    """
    def __init__(self, api_key=None, model="models/gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        if not self.api_key:
            raise ValueError("Gemini API key not found.")
        
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name, generation_config={"response_mime_type": "application/json"})

    def query(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            with open("pipeline_debug.log", "a") as log:
                log.write(f"RAW LLM RESPONSE:\n{text}\n")
            # Strip markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error querying Gemini: {e}")
            import traceback
            traceback.print_exc()
            return None
