from openai import OpenAI
import os

'''
方式1：自定义model name
'''
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),  # or Replace with your OpenRouter API key
)

# batch
completion = client.chat.completions.create(
    model="[https://openrouter.ai/api/v1]google/gemini-2.0-flash-lite-preview-02-05:free", 
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why is AI cool? Answer in 20 words or less."}
    ]
)
print(completion.choices[0].message.content)


# stream
response = client.chat.completions.create(
    model="[https://openrouter.ai/api/v1]google/gemini-2.0-flash-lite-preview-02-05:free",
    messages=[
        {'role': 'user', 'content': "What's 1+1? Answer in one word."}
    ],
    temperature=0,
    stream=True  # this time, we set stream=True
)

for chunk in response:
    print(chunk)
    print(chunk.choices[0].delta.content)
    print("****************")



'''
方式2：query -> "proxy" field
'''
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.getenv('OPENROUTER_API_KEY')
    default_query={"proxy":"https://openrouter.ai/api/v1"}
)

completion = client.chat.completions.create(
    model="google/gemini-2.0-flash-lite-preview-02-05:free", 
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Why is AI cool? Answer in 20 words or less."}
    ]
)
print(completion.choices[0].message.content)
