import json
import os
import re
from collections import defaultdict

import streamlit as st
import streamkjv
import unicodedata
import subprocess
import sys
import string
from openai import OpenAI

# Search cheat-sheet markdown
SEARCH_CHEAT_SHEET_MD = """
### Search Cheat Sheet

- **substring**: kingdom
- **whole‑word**: =love
- **phrase**: "living water"
- **regex**: /grace.*faith/
- **AND**: love & joy
- **OR**: mercy | grace
- **Case flags**: append :c (case) or :i (ignore)
"""

# Pricing table for cost tracking
MODEL_PRICES = {
    "gpt-3.5-turbo-0125": {"in": 0.0005, "out": 0.0015},
    "gpt-4o":             {"in": 0.005 , "out": 0.015 },
}
DEFAULT_MODEL = "gpt-3.5-turbo-0125"
TEMPERATURE = 0.5

# Get API key from env or user input
api_key = os.getenv("OPENAI_API_KEY", "")
api_key = st.sidebar.text_input(
    "OpenAI API key", value=api_key, type="password",
    help="Enter your OpenAI API key for AI features"
)
if not api_key:
    st.sidebar.warning("AI features disabled until API key is provided")
client = OpenAI(api_key=api_key) if api_key else None

# Load Bible data (no caching to avoid pickle issues)
def load_bible():
    raw = json.load(open("kjv_strongs.json", encoding="utf-8"))
    bible = {}
    for ref, txt in raw.items():
        try:
            bc, verse = ref.rsplit(":", 1)
            parts = bc.split()
            book = " ".join(parts[:-1])
            chap = int(parts[-1])
            verse_num = int(verse)
        except ValueError:
            continue
        bible.setdefault(book, {}).setdefault(chap, {})[verse_num] = txt
    return bible, raw

bible, raw = load_bible()
books = list(bible.keys())

def load_interlinear(path: str = "kjv_interlinear.json"):
    """Load interlinear mapping of KJV words to original language (Strong's, lemma, morphology)."""
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        wlc_dir = os.path.join("data", "morphhb", "wlc")
        if os.path.isdir(wlc_dir):
            if st.sidebar.button("Generate interlinear JSON", key="gen_interlinear"):
                subprocess.run([sys.executable, "generate_interlinear.py"])
                st.sidebar.success("Generated kjv_interlinear.json")
                return json.load(open(path, encoding="utf-8"))
        st.sidebar.warning(f"Interlinear data '{path}' not found; original-language lookup disabled.")
        return {}

interlinear = load_interlinear()


def normalize(s: str) -> str:
    """Normalize to ASCII lowercase for matching."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


@st.cache_data
def list_mp3bible_chapters(book_name: str):
    """Return chapter stream URLs from mp3bible.ca for a given KJV book."""
    return dict(streamkjv.list_chapter_files(book_name))

# Initialize session state defaults
if "book" not in st.session_state:
    st.session_state.book = books[0]
if "chap" not in st.session_state:
    st.session_state.chap = sorted(bible[st.session_state.book].keys())[0]

# Helper to navigate from search hit
def go_to_ref(ref: str) -> None:
    # switch back to chapter view when navigating from search
    st.session_state.view = "Chapter View"
    parts = ref.rsplit(":", 1)[0].split()
    st.session_state.book = " ".join(parts[:-1])
    st.session_state.chap = int(parts[-1])

def _on_search_change() -> None:
    """Switch UI to Search Results when a new search is entered."""
    st.session_state.view = "Search Results"

st.title("Bible Search + AI Assistant")

# Sidebar configuration
st.sidebar.title("Options")
model = st.sidebar.selectbox("Model", list(MODEL_PRICES.keys()), index=list(MODEL_PRICES.keys()).index(DEFAULT_MODEL))

# Navigation: Book and Chapter selection
# Navigation: Book and Chapter selection
st.sidebar.header("Navigation")
book = st.sidebar.selectbox("Book", books, key="book")
chap = st.sidebar.selectbox("Chapter", sorted(bible[st.session_state.book].keys()), key="chap")

# top-level view selector to switch between chapter and search views
view = st.sidebar.radio("View", ["Chapter View", "Search Results"], index=0, key="view")

# Functions to move chapters via callbacks
def prev_chapter():
    # Go to previous chapter or previous book's last chapter
    curr_book = st.session_state.book
    curr_chap = st.session_state.chap
    chaps = sorted(bible[curr_book].keys())
    first_ch = chaps[0]
    if curr_chap > first_ch:
        st.session_state.chap = curr_chap - 1
    else:
        book_idx = books.index(curr_book)
        if book_idx > 0:
            prev_book = books[book_idx - 1]
            st.session_state.book = prev_book
            st.session_state.chap = sorted(bible[prev_book].keys())[-1]

def next_chapter():
    # Go to next chapter or next book's first chapter
    curr_book = st.session_state.book
    curr_chap = st.session_state.chap
    chaps = sorted(bible[curr_book].keys())
    last_ch = chaps[-1]
    if curr_chap < last_ch:
        st.session_state.chap = curr_chap + 1
    else:
        book_idx = books.index(curr_book)
        if book_idx < len(books) - 1:
            next_book = books[book_idx + 1]
            st.session_state.book = next_book
            st.session_state.chap = sorted(bible[next_book].keys())[0]

if view == "Chapter View":
    st.header(f"{book} {chap}")

    # Audio Playback
    st.subheader("Audio Playback")
    chap_manifest = list_mp3bible_chapters(book)
    audio_url = chap_manifest.get(chap)
    if audio_url:
        st.audio(audio_url)
    else:
        st.warning("Audio not found for this chapter.")

    # Chapter navigation buttons
    chaps = sorted(bible[book].keys())
    first_chap = chaps[0]
    last_chap = chaps[-1]
    book_idx = books.index(book)
    prev_disabled = book_idx == 0 and chap == first_chap
    next_disabled = book_idx == len(books) - 1 and chap == last_chap
    col1, col2 = st.columns([1, 1])
    col1.button("Previous Chapter", key="prev_top", on_click=prev_chapter, disabled=prev_disabled)
    col2.button("Next Chapter", key="next_top", on_click=next_chapter, disabled=next_disabled)

    # Render each verse as clickable word buttons with lemma lookup
    for verse_num in sorted(bible[book][chap]):
        raw_text = bible[book][chap][verse_num]
        text = re.sub(r"^\s*#\s*", "", raw_text)
        text = re.sub(r"\[([^\]]+)\]", r"*\1*", text)
        # strip punctuation so word index matches interlinear tokens
        words = [w.strip(string.punctuation) for w in text.split()]
        cols = st.columns(len(words) + 1)
        cols[0].markdown(f"**{verse_num}.**")
        for idx, w in enumerate(words):
            key = f"word_{book}_{chap}_{verse_num}_{idx}"
            if cols[idx + 1].button(w, key=key):
                st.session_state.lookup = (book, chap, verse_num, idx)
    # Display original-language lookup in sidebar
    if st.session_state.get("lookup") and interlinear:
        b, c, v, i = st.session_state.lookup
        verse_key = f"{b} {c}:{v}"
        lemma_info = interlinear.get(verse_key, {}).get(str(i), {})
        if lemma_info:
            st.sidebar.markdown(f"**Original word:** {lemma_info.get('lemma','')} ({lemma_info.get('strongs','')})")
            st.sidebar.markdown(f"**Morphology:** {lemma_info.get('morph','')}")
            st.sidebar.markdown(f"**Definition:** {lemma_info.get('def','')}")
        else:
            st.sidebar.info("No interlinear data for this word.")

    # Bottom navigation buttons
    col1, col2 = st.columns([1, 1])
    col1.button("Previous Chapter", key="prev_bottom", on_click=prev_chapter, disabled=prev_disabled)
    col2.button("Next Chapter", key="next_bottom", on_click=next_chapter, disabled=next_disabled)

# Search interface
st.sidebar.header("Search")
# auto-switch to search results when entering a new query
query = st.sidebar.text_input(
    "Enter search term", "", key="query", on_change=_on_search_change
)
st.sidebar.markdown(SEARCH_CHEAT_SHEET_MD)
context = f"{book} {chap}\n" + "\n".join(f"{v}. {bible[book][chap][v]}" for v in sorted(bible[book][chap]))

if view == "Search Results" and query:
        # Case sensitivity flags
        cs = None
        if query.endswith(":c"):
            cs, q = True, query[:-2]
        elif query.endswith(":i"):
            cs, q = False, query[:-2]
        else:
            cs, q = False, query

        # Regex or plain search
        if q.startswith("/") and q.endswith("/") and len(q) >= 3:
            pattern = re.compile(q[1:-1], 0 if cs else re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(q), 0 if cs else re.IGNORECASE)

        # Find hits
        hits = [(ref, raw[ref]) for ref in raw if pattern.search(raw[ref])]

        if not hits:
            st.write("No matches found.")
        else:
            st.subheader(f"{len(hits)} Search Result(s)")
            for i, (ref, text) in enumerate(hits):
                highlighted = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)
                # navigate to chapter on click via callback
                st.button(
                    ref,
                    key=f"goto_{i}",
                    on_click=go_to_ref,
                    args=(ref,)
                )
                st.markdown(f"- **{ref}**: {highlighted}", unsafe_allow_html=True)

# AI Q&A interface
st.sidebar.header("AI Assistant")
question = st.sidebar.text_input("Ask AI", "")
if st.sidebar.button("Ask AI") and question.strip():
    if not client:
        st.error("API key missing; cannot perform AI call")
    else:
        prompt = (
            "You are a helpful Bible study assistant.\n\n"
            f"CONTEXT:\n{context}\n\nQUESTION: {question}\n\n"
            "Answer clearly and concisely."
        )
        with st.spinner("Contacting AI..."):
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
            )
        answer = resp.choices[0].message.content.strip()
        usage = resp.usage
        price = MODEL_PRICES.get(model, {"in": 0, "out": 0})
        cost = (usage.prompt_tokens * price["in"] + usage.completion_tokens * price["out"]) / 1000
        if "total_cost" not in st.session_state:
            st.session_state.total_cost = 0.0
            st.session_state.total_tokens = 0
        st.session_state.total_cost += cost
        st.session_state.total_tokens += usage.prompt_tokens + usage.completion_tokens
        st.subheader("AI Answer")
        st.write(answer)
        st.sidebar.write(f"Tokens: {usage.prompt_tokens + usage.completion_tokens}")
        st.sidebar.write(f"Cost this call: ${cost:.4f}")
        st.sidebar.write(f"Cumulative cost: ${st.session_state.total_cost:.4f}")
