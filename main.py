import asyncio
from functools import wraps
from openai.error import APIError, InvalidRequestError, OpenAIError
import time
import os
import openai_async
import httpx
from dotenv import load_dotenv
load_dotenv()
import openai 
gpt3 = "gpt-3.5-turbo"
gpt4 = "gpt-4"
load_dotenv()
api_key = openai.api_key = os.environ["OPENAI_API_KEY"]

from pathlib import Path
import re

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def write_details_to_file(index, book, chatper, details):
    sanitized_book = sanitize_filename(book)
    sanitized_chatper = sanitize_filename(chatper)
    
    Path(sanitized_book).mkdir(parents=True, exist_ok=True)
    
    with open(f"{sanitized_book}/{index}. {sanitized_chatper}.txt", "w", encoding="utf-8") as f:
        f.write(details)


async def chat_completion(messages):
    start_time = time.time()
    response = None 
    model = gpt4
    try:
        response = await openai_async.chat_complete(
            api_key,
            timeout=60, 
            payload={
                "model": gpt4,
                "messages": messages,
                'temperature': 1
            },
        )
    except httpx.ReadTimeout:
        print("Request to OpenAI timed out. Retrying...")
    

    end_time = time.time() 
    api_call_duration = end_time - start_time 
    print(f'api_call_duration = {api_call_duration}')
    result = None
    if response:
        response_json = response.json()
        if 'choices' in response_json and 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
            result = response_json["choices"][0]["message"]["content"]
            print(f'result = {result}')
        else:
            print(f"Unexpected structure in API response: {response_json}")
    return result

def generate_chapter_list_prompt(book_title):
    system_prompt = f"""
You are an AI assistant whose only purpose is to list out chapters to a book. I'm going to give you a book title and I want you to list out the chapters. List out the chapters in order, in a dashed bulleted list.

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

def generate_detail_prompt(book, chatper):
    messages = [
        generate_chat_message("system", f"You are a book summarizer. I'm going to give you the title to a chapter of a specific book and your only goal is to provide me a detailed summary of the book's chapter that I give you. Give me as much detail as possible."),
        generate_chat_message("user", f"The book is '{book}' and the chapter I want you to summarize is '{chatper}'."),
    ]
    return messages


def generate_chat_message(role, content):
    return {"role": role, "content": content}

def ask_for_book():
    book_title = input("What book do you want a summary for?")
    return book_title

def extract_chapters(result):
    chapters = result.split("\n")
    chapters = [chapter.strip().replace("- ", "") for chapter in chapters]
    return chapters

async def main():
    book = ask_for_book()

    messages = generate_chapter_list_prompt(book)

    chapter_bullet_points = await chat_completion(messages)
    
    chapters_array = extract_chapters(chapter_bullet_points)
    print(f'chapters_array = {chapters_array}')
    for i, chapter in enumerate(chapters_array, start=1):
        detail_messages = generate_detail_prompt(book, chapter)
        details = await chat_completion(detail_messages)
        print(f"\nwriting Details: {chapter}\n")
        
        write_details_to_file(i, book, chapter, details)

    
if __name__ == "__main__":
    asyncio.run(main())
