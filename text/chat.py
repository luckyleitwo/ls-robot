import os
import openai

# optional; defaults to `os.environ['OPENAI_API_KEY']`
openai.api_key = "sk-hSaUp2XwPvZB4zdVShdYiFVC0Exc2dwOOpoKaYaemeLAbGCW"

# all client options can be configured just like the `OpenAI` instantiation counterpart
openai.base_url = "https://api.chatanywhere.tech/v1/"
openai.default_headers = {"x-foo": "true"}

completion = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "讲个笑话",
        },
    ],
)
print(completion.choices[0].message.content)