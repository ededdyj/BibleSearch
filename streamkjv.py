#!/usr/bin/env python3
"""
Stream KJV chapter audio from https://www.mp3bible.ca/ using per-book directories.

Usage:
  python kjv_stream.py --list "Genesis"
  python kjv_stream.py --play "Genesis" 1
  python kjv_stream.py --play "1 Corinthians" 13

If VLC isn't installed (python-vlc import fails), the script will open the stream
URL in your default browser.
"""

import argparse
import re
import sys
import time
import webbrowser
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# Try to import VLC; if not available, we'll just open the URL in a browser
try:
    import vlc  # type: ignore
    HAS_VLC = True
except Exception:
    HAS_VLC = False

BASE = "https://www.mp3bible.ca"

# Canonical 66-book mapping -> site directory slugs.
# (You can abbreviate or vary user input; we normalize via ALIASES below.)
BOOK_DIRS: Dict[str, str] = {
    "Genesis": "01_Genesis",
    "Exodus": "02_Exodus",
    "Leviticus": "03_Leviticus",
    "Numbers": "04_Numbers",
    "Deuteronomy": "05_Deuteronomy",
    "Joshua": "06_Joshua",
    "Judges": "07_Judges",
    "Ruth": "08_Ruth",
    "1 Samuel": "09_1_Samuel",
    "2 Samuel": "10_2_Samuel",
    "1 Kings": "11_1_Kings",
    "2 Kings": "12_2_Kings",
    "1 Chronicles": "13_1_Chronicles",
    "2 Chronicles": "14_2_Chronicles",
    "Ezra": "15_Ezra",
    "Nehemiah": "16_Nehemiah",
    "Esther": "17_Esther",
    "Job": "18_Job",
    "Psalms": "19_Psalms",
    "Proverbs": "20_Proverbs",
    "Ecclesiastes": "21_Ecclesiastes",
    "Song of Solomon": "22_Song_of_Solomon",
    "Isaiah": "23_Isaiah",
    "Jeremiah": "24_Jeremiah",
    "Lamentations": "25_Lamentations",
    "Ezekiel": "26_Ezekiel",
    "Daniel": "27_Daniel",
    "Hosea": "28_Hosea",
    "Joel": "29_Joel",
    "Amos": "30_Amos",
    "Obadiah": "31_Obadiah",
    "Jonah": "32_Jonah",
    "Micah": "33_Micah",
    "Nahum": "34_Nahum",
    "Habakkuk": "35_Habakkuk",
    "Zephaniah": "36_Zephaniah",
    "Haggai": "37_Haggai",
    "Zechariah": "38_Zechariah",
    "Malachi": "39_Malachi",
    "Matthew": "40_Matthew",
    "Mark": "41_Mark",
    "Luke": "42_Luke",
    "John": "43_John",
    "Acts": "44_Acts",
    "Romans": "45_Romans",
    "1 Corinthians": "46_1_Corinthians",
    "2 Corinthians": "47_2_Corinthians",
    "Galatians": "48_Galatians",
    "Ephesians": "49_Ephesians",
    "Philippians": "50_Philippians",
    "Colossians": "51_Colossians",
    "1 Thessalonians": "52_1_Thessalonians",
    "2 Thessalonians": "53_2_Thessalonians",
    "1 Timothy": "54_1_Timothy",
    "2 Timothy": "55_2_Timothy",
    "Titus": "56_Titus",
    "Philemon": "57_Philemon",
    "Hebrews": "58_Hebrews",
    "James": "59_James",
    "1 Peter": "60_1_Peter",
    "2 Peter": "61_2_Peter",
    "1 John": "62_1_John",
    "2 John": "63_2_John",
    "3 John": "64_3_John",
    "Jude": "65_Jude",
    "Revelation": "66_Revelation",
}

# Flexible aliases so user can type "Gen", "1 Kgs", "Song", etc.
ALIASES: Dict[str, str] = {
    # Pentateuch
    "gen": "Genesis", "ge": "Genesis", "gn": "Genesis",
    "ex": "Exodus", "exo": "Exodus",
    "lev": "Leviticus", "lv": "Leviticus",
    "num": "Numbers", "nm": "Numbers", "nu": "Numbers",
    "deut": "Deuteronomy", "dt": "Deuteronomy", "deu": "Deuteronomy",
    # Historical
    "jos": "Joshua", "josh": "Joshua",
    "jdg": "Judges", "judg": "Judges",
    "ru": "Ruth", "ruth": "Ruth",
    "1sa": "1 Samuel", "1 sam": "1 Samuel", "i samuel": "1 Samuel",
    "2sa": "2 Samuel", "2 sam": "2 Samuel", "ii samuel": "2 Samuel",
    "1ki": "1 Kings", "1 kgs": "1 Kings", "i kings": "1 Kings",
    "2ki": "2 Kings", "2 kgs": "2 Kings", "ii kings": "2 Kings",
    "1ch": "1 Chronicles", "i chronicles": "1 Chronicles",
    "2ch": "2 Chronicles", "ii chronicles": "2 Chronicles",
    "ezr": "Ezra",
    "neh": "Nehemiah",
    "est": "Esther",
    # Poetry/Wisdom
    "job": "Job",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "pr": "Proverbs", "prov": "Proverbs",
    "eccl": "Ecclesiastes", "ecc": "Ecclesiastes",
    "song": "Song of Solomon", "sos": "Song of Solomon", "song of songs": "Song of Solomon",
    # Major Prophets
    "isa": "Isaiah",
    "jer": "Jeremiah",
    "lam": "Lamentations",
    "ezek": "Ezekiel",
    "dan": "Daniel",
    # Minor Prophets
    "hos": "Hosea", "joe": "Joel", "amo": "Amos", "oba": "Obadiah",
    "jon": "Jonah", "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk",
    "zep": "Zephaniah", "hag": "Haggai", "zec": "Zechariah", "mal": "Malachi",
    # Gospels/Acts
    "mt": "Matthew", "mk": "Mark", "lk": "Luke", "jn": "John",
    "ac": "Acts",
    # Epistles
    "rom": "Romans",
    "1co": "1 Corinthians", "i corinthians": "1 Corinthians",
    "2co": "2 Corinthians", "ii corinthians": "2 Corinthians",
    "gal": "Galatians",
    "eph": "Ephesians",
    "php": "Philippians", "phil": "Philippians",
    "col": "Colossians",
    "1th": "1 Thessalonians", "i thessalonians": "1 Thessalonians",
    "2th": "2 Thessalonians", "ii thessalonians": "2 Thessalonians",
    "1ti": "1 Timothy", "i timothy": "1 Timothy",
    "2ti": "2 Timothy", "ii timothy": "2 Timothy",
    "tit": "Titus",
    "phm": "Philemon",
    "heb": "Hebrews",
    "jas": "James",
    "1pe": "1 Peter", "i peter": "1 Peter",
    "2pe": "2 Peter", "ii peter": "2 Peter",
    "1jn": "1 John", "i john": "1 John",
    "2jn": "2 John", "ii john": "2 John",
    "3jn": "3 John", "iii john": "3 John",
    "jud": "Jude",
    "rev": "Revelation", "re": "Revelation", "apocalypse": "Revelation",
}

def normalize_book(user_input: str) -> str:
    s = user_input.strip().lower()
    s = re.sub(r"\s+", " ", s)
    # standardize leading numerals like "1st", "2nd"
    s = s.replace("first ", "1 ").replace("second ", "2 ").replace("third ", "3 ")
    s = re.sub(r"^1st\s+", "1 ", s)
    s = re.sub(r"^2nd\s+", "2 ", s)
    s = re.sub(r"^3rd\s+", "3 ", s)

    # exact alias hit
    if s in ALIASES:
        return ALIASES[s]

    # try to coerce "1 kings" style spacing
    m = re.match(r"^(1|2|3)\s+([a-z].*)$", s)
    if m:
        numeral, rest = m.groups()
        candidate = f"{numeral} {rest.title()}"
        # exact match?
        for k in BOOK_DIRS.keys():
            if k.lower() == candidate.lower():
                return k

    # fallback: titlecase and try direct match with BOOK_DIRS
    t = s.title()
    for k in BOOK_DIRS.keys():
        if k.lower() == t.lower():
            return k

    raise ValueError(f"Unrecognized book name: {user_input!r}")

def list_chapter_files(book: str) -> List[Tuple[int, str]]:
    """
    Return a sorted list of (chapter_number, absolute_stream_url) for a book.
    We parse the directory listing at https://www.mp3bible.ca/<DIR>/
    """
    canonical = normalize_book(book)
    dirslug = BOOK_DIRS[canonical]
    url = f"{BASE}/{dirslug}/"
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    links = [a.get("href", "") for a in soup.find_all("a")]
    mp3s = [h for h in links if h and h.lower().endswith(".mp3")]

    # infer chapter number from the last 3 digits before ".mp3"
    out: List[Tuple[int, str]] = []
    for name in mp3s:
        # name could be relative like "01003 0_KJV_Bible-Genesis001.mp3"
        m = re.search(r"(\d{1,3})(?=\.mp3$)", name)
        if not m:
            continue
        chap = int(m.group(1))
        out.append((chap, f"{url}{name}"))

    # Some folders include leading/trailer/intro files; keep only 1..max
    out.sort(key=lambda x: x[0])
    return out

def play_stream(url: str) -> None:
    if HAS_VLC:
        player = vlc.MediaPlayer(url)  # noqa: F405 (if mypy)
        player.play()
        # Wait until it actually starts (simple polling)
        for _ in range(100):
            if player.is_playing():
                break
            time.sleep(0.1)
        print("Streaming (press Ctrl+C to quit)...")
        try:
            while True:
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        player.stop()
    else:
        print("python-vlc not available; opening in default browser instead.")
        print(url)
        webbrowser.open(url)

def main():
    ap = argparse.ArgumentParser(description="Stream KJV chapter audio from mp3bible.ca")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", metavar="BOOK", help="List available chapters for BOOK")
    g.add_argument("--play", nargs=2, metavar=("BOOK", "CHAPTER"),
                   help="Play a specific BOOK and CHAPTER (number)")
    args = ap.parse_args()

    try:
        if args.list:
            chapters = list_chapter_files(args.list)
            if not chapters:
                print("No chapters found (unexpected).")
                return
            canonical = normalize_book(args.list)
            print(f"{canonical}: {len(chapters)} chapter(s)")
            for ch, url in chapters:
                print(f"  {ch:>3}  {url}")
        else:
            book, ch_str = args.play
            chapter = int(ch_str)
            chapters = dict(list_chapter_files(book))
            if chapter not in chapters:
                raise SystemExit(f"Chapter {chapter} not found for {book}. "
                                 f"Available: 1..{max(chapters) if chapters else '??'}")
            url = chapters[chapter]
            print(f"Streaming {normalize_book(book)} {chapter}:")
            print(url)
            play_stream(url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
