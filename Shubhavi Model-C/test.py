import google.generativeai as genai

genai.api_key = "AIzaSyBYiXBrhnO4mq0ILtmxXP_oi4xuvFjmrj0"

model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Who is the Prime Minister of India?")
print(response.text)
