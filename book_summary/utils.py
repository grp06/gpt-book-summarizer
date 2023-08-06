import re


def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def ask_for_book():
    book_title = input("What book do you want a summary for?")
    return book_title


def extract_chapters(result):
    chapters = result.split("\n")
    chapters = [chapter.strip().replace("- ", "") for chapter in chapters]
    return chapters
