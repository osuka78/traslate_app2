import google.generativeai as genai

API_KEY = "AIzaSyDvjO6t6dv4h_ReZ2VtT3K6sQtGVgl9c_o"
genai.configure(api_key=API_KEY)

print("--- 使えるモデル一覧 ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)