import ollama
try:
    models = ollama.list()
    print("Ollama API connection successful.")
    print("Available models:", [m['name'] for m in models['models']])
except Exception as e:
    print(f"Ollama API connection failed: {e}")

try:
    import requests
    response = requests.get("http://localhost:11434/api/tags")
    print(f"Direct HTTP search status: {response.status_code}")
    print(f"Direct HTTP response: {response.text[:100]}...")
except Exception as e:
    print(f"Direct HTTP connection failed: {e}")
