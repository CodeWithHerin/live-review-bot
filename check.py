import google.generativeai as genai

# PASTE YOUR API KEY INSIDE THE QUOTES BELOW
api_key = "AIzaSyBwoOpk1UNGWe5LK3aQVoCUgtIsZr4_Em4"

genai.configure(api_key=api_key)

print("Searching for available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"FOUND: {m.name}")