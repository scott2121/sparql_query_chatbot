from openai import OpenAI


def excute_gpt(content):
    """
    Extracts the variable parameter from the query.
    """
    model_name = "gpt-4-1106-preview"
    client = OpenAI()

    prompt = {"role": "user", "content": content}

    completion = client.chat.completions.create(
        model=model_name,
        messages=[prompt],
    )
    gpt_output = completion.choices[0].message.content
    return gpt_output
