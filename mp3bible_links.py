#!/usr/bin/env python3
"""
Utility for generating and fetching MP3 Bible streaming links from mp3bible.ca.
"""

import json
import re
import requests
import sys
from typing import Dict, List

def load_books(json_path: str = "kjv_strongs.json") -> List[str]:
    """
    Load Bible books order from JSON verse file.
    Returns list of book names in the order they appear.
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    pattern = re.compile(r"^(.*) \d+:\d+$")
    books: List[str] = []
    for key in data.keys():
        m = pattern.match(key)
        if m:
            book = m.group(1)
            if book not in books:
                books.append(book)
    return books

def book_code(book: str, books: List[str]) -> str:
    """
    Return URL code for a book, e.g. '01_Genesis'.
    """
    try:
        idx = books.index(book) + 1
    except ValueError:
        raise ValueError(f"Book '{book}' not found in book list")
    name = book.replace(" ", "_")
    return f"{idx:02d}_{name}"

def get_book_page_url(book: str, books: List[str], base_url: str = "https://mp3bible.ca") -> str:
    """
    Return the URL of the mp3bible.ca page for a given book.
    """
    code = book_code(book, books)
    return f"{base_url}/{code}/"

def fetch_chapter_links(book: str, books: List[str], base_url: str = "https://mp3bible.ca") -> Dict[int, str]:
    """
    Fetch all chapter audio URLs for a book by scraping its mp3bible.ca page.
    Returns a dict mapping chapter number to full mp3 URL.
    """
    page_url = get_book_page_url(book, books, base_url)
    resp = requests.get(page_url, timeout=10)
    resp.raise_for_status()
    pattern = re.compile(r'href="(' + re.escape(book_code(book, books)) + r'_(\d{3})\.mp3)"')
    links: Dict[int, str] = {}
    for match in pattern.finditer(resp.text):
        filename, num = match.groups()
        chap = int(num)
        links[chap] = f"{page_url}{filename}"
    return links

def get_chapter_audio_url(book: str, chapter: int, books: List[str], base_url: str = "https://mp3bible.ca") -> str:
    """
    Return direct mp3 URL for a given book and chapter using naming convention.
    """
    code = book_code(book, books)
    filename = f"{code}_{chapter:03d}.mp3"
    return f"{base_url}/{code}/{filename}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python mp3bible_links.py <BookName> <ChapterNumber>")
        sys.exit(1)
    book = sys.argv[1]
    chapter = int(sys.argv[2])
    books = load_books()
    url = get_chapter_audio_url(book, chapter, books)
    print(url)

if __name__ == "__main__":
    main()
