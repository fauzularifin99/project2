import os
from openai import OpenAI

# Masukkan API Key Anda di sini
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-3.5-turbo", # atau "gpt-4"
    messages=[
        {"role": "system", "content": "Anda adalah asisten pintar."},
        {"role": "user", "content": "sekarang hari apa?"}
    ]
)

# Menampilkan jawaban
print(response.choices[0].message.content)
