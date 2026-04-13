import google.generativeai as genai

# ✅ Directly set your key here
genai.api_key = "AIzaSyBmijRyhhJ2xXrxKXjHHHi53MsOreyPqEc"

# List available models
models = genai.list_models()
for m in models:
    print(m)