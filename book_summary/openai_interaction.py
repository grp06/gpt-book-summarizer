import asyncio
import httpx
import openai_async
from openai.error import APIError, InvalidRequestError, OpenAIError
import os
import openai
from dotenv import load_dotenv
import time

load_dotenv()
api_key = openai.api_key = os.environ["OPENAI_API_KEY"]
gpt3 = "gpt-3.5-turbo"
gpt4 = "gpt-4"


async def chat_completion(messages):
    start_time = time.time()
    response = None

    try:
        response = await openai_async.chat_complete(
            api_key,
            timeout=60,
            payload={"model": gpt3, "messages": messages, "temperature": 1},
        )
    except httpx.ReadTimeout:
        print("Request to OpenAI timed out. Retrying...")

    end_time = time.time()
    api_call_duration = end_time - start_time
    print(f"api_call_duration = {api_call_duration}")
    result = None
    if response:
        response_json = response.json()
        if (
            "choices" in response_json
            and "message" in response_json["choices"][0]
            and "content" in response_json["choices"][0]["message"]
        ):
            result = response_json["choices"][0]["message"]["content"]
        else:
            print(f"Unexpected structure in API response: {response_json}")
    return result


def generate_chapter_list_prompt(book_title):
    system_prompt = f"""
You are an AI that specializes in providing chapter lists of books. When I provide you with a title, your task is to generate the chapters of the specified book, using publicly available summaries or overviews. The list must be presented in order, using dashes as bullet points.

// Example output
```
- The Power of Thought
- Desire: The Starting Point of All Achievement
- Faith: Visualizing and Believing in the Attainment of Desire
```

Output should only contain the dashed list, no explanations.
"""
    messages = [
        generate_chat_message("system", system_prompt),
        generate_chat_message("user", f"Here's the book: {book_title}"),
    ]
    return messages


def generate_chapter_summary_prompt(book, chapter):
    messages = [
        generate_chat_message(
            "system",
            f"You are a specialist in summarizing book chapters. When I present you with the title of a specific chapter from a particular book, your task is to provide me with an in-depth summary of that chapter. Your summary must be detailed, capturing the core essence, themes, and underlying spirit of the chapter without mentioning its title. Provide as much insight and information as possible to represent the content accurately.",
        ),
        generate_chat_message(
            "user",
            f"The book is '{book}' and the chapter I want you to summarize is '{chapter}'.",
        ),
    ]
    return messages


def generate_chat_message(role, content):
    return {"role": role, "content": content}
