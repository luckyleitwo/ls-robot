import openai


def openChat(query):
        # optional; defaults to `os.environ['OPENAI_API_KEY']`
        openai.api_key = "sk-ZRD4wE1uJUhTm0xh7d5152D55f994b78961540665a50Ff00"

        # all client options can be configured just like the `OpenAI` instantiation counterpart
        openai.base_url = "https://free.gpt.ge/v1/"
        openai.default_headers = {"x-foo": "true"}
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": query,
                },
            ],
            # stream=True  # 开启流式响应
        )
        return completion.choices[0].message.content