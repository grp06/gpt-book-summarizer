from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
from pathlib import Path
from book_summary.openai_interaction import (
    chat_completion,
    generate_chapter_list_prompt,
    generate_chapter_summary_prompt,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from pydantic import BaseModel
from book_summary.utils import sanitize_filename, extract_chapters
from fastapi.responses import FileResponse

import tempfile

from pathlib import Path

import uuid

file_mapping = {}
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import redis

try:
    redis_conn = redis.StrictRedis(host="localhost", port=6379, db=0)
    print("Connected to Redis")
except redis.ConnectionError:
    print("Could not connect to Redis")


class Book(BaseModel):
    title: str


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from rq import Queue
import redis

q = Queue(connection=redis_conn)


@app.get("/get_job_status/{job_id}")
async def get_job_status(job_id: str):
    job = q.fetch_job(job_id)
    if job.is_finished:
        return {"status": "finished", "file_id": job.result}
    else:
        return {"status": "pending"}


def create_pdf_file(summary_text, chapters):
    pdfmetrics.registerFont(TTFont("Vera", "Vera.ttf"))

    temp_file_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name

    c = canvas.Canvas(temp_file_path, pagesize=letter)

    width, height = letter
    left_margin = 100
    right_margin = 100
    top_margin = 100
    bottom_margin = 100
    line_height = 15

    normal_font_name = "Vera"
    normal_font_size = 12
    c.setFont(normal_font_name, normal_font_size)

    draw_width = width - left_margin - right_margin
    y_position = height - top_margin

    for chapter, text in zip(chapters, summary_text.split("\n\n")):
        c.setFont(normal_font_name, normal_font_size * 2)
        c.drawString(left_margin, y_position, chapter)
        y_position -= line_height * 2
        c.setFont(normal_font_name, normal_font_size)

        for line in text.splitlines():
            words = line.split()
            while words:
                line_to_draw = ""
                while (
                    words
                    and pdfmetrics.stringWidth(
                        line_to_draw + words[0], normal_font_name, normal_font_size
                    )
                    < draw_width
                ):
                    line_to_draw += words.pop(0) + " "

                c.drawString(left_margin, y_position, line_to_draw)
                y_position -= line_height
                if y_position < bottom_margin:
                    c.showPage()
                    y_position = height - top_margin

        y_position -= line_height * 4

    c.save()
    return temp_file_path


async def process_chapters(book, chapters_array):
    async def process_chapter(i, chapter):
        print(f"Processing Chapter: {chapter}")
        detail_messages = generate_chapter_summary_prompt(book, chapter)
        chapter_summary = await chat_completion(detail_messages)
        return chapter_summary  # Only return the summary

    tasks = [process_chapter(i, chapter) for i, chapter in enumerate(chapters_array)]
    full_summary = await asyncio.gather(*tasks)
    return full_summary  # Return a list of summaries


def process_book_and_create_pdf(book_title, chapters_array):
    full_summary = asyncio.run(process_chapters(book_title, chapters_array))
    full_summary_text = "\n\n".join(full_summary)  # Join the summaries
    print(f"full summary {full_summary}")
    pdf_path = create_pdf_file(full_summary_text, chapters_array)
    file_id = str(uuid.uuid4())
    file_mapping[file_id] = pdf_path
    print(f"file_id {file_id}")
    return file_id


@app.post("/get_summary/")
async def get_summary(book: Book):
    messages = generate_chapter_list_prompt(book.title)
    chapter_bullet_points = await chat_completion(messages)
    print(chapter_bullet_points)
    chapters_array = extract_chapters(chapter_bullet_points)
    job = q.enqueue(process_book_and_create_pdf, book.title, chapters_array)
    return {"job_id": job.get_id()}


@app.get("/download_pdf/{file_id}")
async def download_pdf(file_id: str):
    file_path = file_mapping.get(file_id)
    if file_path:
        return FileResponse(
            file_path,
            headers={"Content-Disposition": "attachment; filename=summary.pdf"},
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")
