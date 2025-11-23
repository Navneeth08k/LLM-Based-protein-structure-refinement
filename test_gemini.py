import os
import google.generativeai as genai

def test_gemini(api_key):
    print(f"Testing Gemini with key: {api_key[:5]}...")
    try:
        genai.configure(api_key=api_key)
        print("Listing models...")
        with open("models.txt", "w") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
                    print(m.name)
    except Exception as e:
        with open("gemini_error.log", "w") as f:
            f.write(str(e))
            import traceback
            traceback.print_exc(file=f)
        print(f"Error logged to gemini_error.log")

if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_API_KEY", "")
    test_gemini(key)
