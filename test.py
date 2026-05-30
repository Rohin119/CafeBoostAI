import google.generativeai as genai

import os

GEMINI_API_KEY = os.getenv("")


model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Say hello")

print(response.text)
