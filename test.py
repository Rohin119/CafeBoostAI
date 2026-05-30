import google.generativeai as genai

genai.configure(api_key="AQ.Ab8RN6JlClW0ZihXGd4xTT5mOr1fJVZh-iQSSdEmvmOwnImjFw")

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Say hello")

print(response.text)