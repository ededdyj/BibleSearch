"""
Bible Reader + OpenAI Assistant (enhanced)
================================================
• Navigate by book/chapter
• Powerful search (substring, whole‑word, phrase, regex, AND/OR, case flags)
• Built‑in searchable help: type `searchguide` to view a detailed cheat‑sheet
• AI Q&A using chapter or search context
• Live model switching and budget tracking
• Rich colours; keeps [bracketed] text intact
"""

import json, os, sys, re
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Optional
from openai import OpenAI                    # openai-python ≥1.0 client

# ─── Rich (pretty) setup ──────────────────────────────────────────────────
try:
    from rich import print as rprint
    from rich.console import Console
    console = Console()
    USE_RICH = True
except ImportError:                          # fall back to plain stdout
    def rprint(*args, **kwargs):
        print(*args, **kwargs)
    console = None
    USE_RICH = False

def plain(text: str):                        # prints without Rich markup
    (console.print if USE_RICH else print)(text, **({"markup": False} if USE_RICH else {}))
# ──────────────────────────────────────────────────────────────────────────

# ─── Search Guide (cheat‑sheet) ──────────────────────────────────────────
SEARCH_GUIDE_RICH = """
[bold magenta]Search Cheat‑Sheet[/]
───────────────────────────────
• [bold cyan]substring[/]:   kingdom
• [bold cyan]whole‑word[/]:  =love
• [bold cyan]phrase[/]:      "living water"
• [bold cyan]regex[/]:       /grace.*faith/
• [bold cyan]AND[/]:         love & joy
• [bold cyan]OR[/]:          mercy | grace
• [bold cyan]Case flags[/]:  append :c (case) or :i (ignore)

[green]After results[/] you can type [bold]ai[/] to ask the assistant about the hit‑list.
"""

SEARCH_GUIDE_PLAIN = """
SEARCH CHEAT‑SHEET
──────────────────
• substring   : kingdom
• whole‑word  : =love
• phrase      : "living water"
• regex       : /grace.*faith/
• AND         : love & joy
• OR          : mercy | grace
• Case flags  : append :c (case) or :i (ignore)

After results you can type "ai" to ask the assistant about the hit‑list.
"""


def display_searchguide() -> None:
    """Print the search cheat‑sheet and wait for the user to continue."""
    rprint(SEARCH_GUIDE_RICH if USE_RICH else SEARCH_GUIDE_PLAIN)
    input("\nPress Enter to return to the menu…")
# ──────────────────────────────────────────────────────────────────────────

# ─── OpenAI + pricing/budget ──────────────────────────────────────────────
MODEL_PRICES = {
    "gpt-3.5-turbo-0125": {"in": 0.0005, "out": 0.0015},
    "gpt-4o":             {"in": 0.005 , "out": 0.015 },
}
DEFAULT_MODEL = "gpt-3.5-turbo-0125"
TEMPERATURE   = 0.5

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or input("Enter your OpenAI API key: ").strip()
)

total_tokens: float = 0.0
total_cost:   float = 0.0


def log_cost(model: str, prompt_t: int, comp_t: int) -> None:
    global total_tokens, total_cost
    total_tokens += prompt_t + comp_t
    price = MODEL_PRICES.get(model, {"in": 0, "out": 0})
    cost  = (prompt_t * price["in"] + comp_t * price["out"]) / 1000
    total_cost += cost
    msg = f"💰 Cost this call: ${cost:.4f} | Cumulative: ${total_cost:.4f}"
    if USE_RICH:
        console.rule(f"[bold yellow]{msg}")
    else:
        print("\n" + "-" * 70 + f"\n{msg}\n" + "-" * 70)
# ──────────────────────────────────────────────────────────────────────────

# ─── Load Bible JSON ──────────────────────────────────────────────────────
with open("verses-1769.json", encoding="utf-8") as f:
    raw = json.load(f)

bible: defaultdict[str, defaultdict[int, dict[int, str]]] = defaultdict(lambda: defaultdict(dict))
for ref, txt in raw.items():
    try:
        bc, verse = ref.rsplit(":", 1)
        parts     = bc.split()
        book      = " ".join(parts[:-1])
        chap      = int(parts[-1])
        bible[book][chap][int(verse)] = txt
    except ValueError:
        rprint(f"[red]Could not parse reference: {ref}")
# ──────────────────────────────────────────────────────────────────────────

# ─── Bible navigation helpers ─────────────────────────────────────────────

def list_books() -> None:
    hdr = "[bold cyan]Books of the Bible:[/]" if USE_RICH else "Books of the Bible:"
    rprint("\n" + hdr)
    for i, b in enumerate(bible.keys(), 1):
        rprint(f"{i}. {b}")


def list_chapters(book: str) -> None:
    chs = " ".join(str(c) for c in sorted(bible[book]))
    hdr = f"[bold cyan]Chapters in {book}:[/]" if USE_RICH else f"Chapters in {book}:"
    rprint("\n" + hdr + " " + chs)


def read_chapter(book: str, chap: int) -> None:
    chap = int(chap)
    if chap not in bible[book]:
        rprint("[red]Chapter not found.[/]" if USE_RICH else "Chapter not found.")
        return
    if USE_RICH:
        console.rule(f"[bold magenta]{book} {chap}")
    else:
        print(f"\n{book} {chap}")
    for v in sorted(bible[book][chap]):
        if USE_RICH:
            console.print(f"{v}. ", style="green", end="")
            console.print(bible[book][chap][v], markup=False)
        else:
            print(f"{v}. {bible[book][chap][v]}")


def next_chap(book: str, chap: int) -> Optional[int]:
    chs = sorted(bible[book]); ix = chs.index(chap)
    return chs[ix + 1] if ix + 1 < len(chs) else None


def prev_chap(book: str, chap: int) -> Optional[int]:
    chs = sorted(bible[book]); ix = chs.index(chap)
    return chs[ix - 1] if ix else None
# ──────────────────────────────────────────────────────────────────────────

# ─── AI helper ────────────────────────────────────────────────────────────

def ask_ai(context: str, model: str = DEFAULT_MODEL) -> None:
    if not context:
        rprint("[yellow]No context available.[/]" if USE_RICH else "No context available.")
        return
    q = input("Ask AI (blank to cancel): ").strip()
    if not q:
        return
    prompt = (
        "You are a helpful Bible study assistant.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {q}\n\nAnswer clearly and concisely."
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
        )
        ans = resp.choices[0].message.content.strip()
        rprint(
            f"\n[bold green]AI Answer:[/]\n{ans}\n" if USE_RICH else f"\nAI Answer:\n{ans}\n"
        )
        u = resp.usage; log_cost(model, u.prompt_tokens, u.completion_tokens)
    except Exception as e:
        rprint(f"[red]API error: {e}[/]" if USE_RICH else f"API error: {e}")
# ──────────────────────────────────────────────────────────────────────────

# ─── Model switcher ───────────────────────────────────────────────────────

def choose_model() -> Optional[str]:
    hdr = "[bold cyan]Available models:[/]" if USE_RICH else "Available models:"
    rprint("\n" + hdr)
    for i, m in enumerate(MODEL_PRICES, 1):
        p = MODEL_PRICES[m]
        rprint(f"{i}. {m} (in ${p['in']}/1k, out ${p['out']}/1k)")
    sel = input("Pick model name or #: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(MODEL_PRICES):
        return list(MODEL_PRICES)[int(sel) - 1]
    if sel in MODEL_PRICES:
        return sel
    rprint("[yellow]Invalid selection.[/]" if USE_RICH else "Invalid selection.")
    return None
# ──────────────────────────────────────────────────────────────────────────

# ─── FLEXIBLE SEARCH ──────────────────────────────────────────────────────

def _compile(body: str, cs: bool):
    return re.compile(body, 0 if cs else re.IGNORECASE)


def _token_to_regex(tok: str) -> str:
    if tok.startswith('"') and tok.endswith('"'):
        return re.escape(tok[1:-1])                    # phrase
    if tok.startswith("="):
        return rf"\b{re.escape(tok[1:])}\b"           # whole word
    return re.escape(tok)                              # plain substring


def search(query: str) -> Tuple[Optional[str], str]:
    """Return (book, chap) if user selects a verse, else (None, context)"""
    # case flags
    cs: Optional[bool] = None
    if query.endswith(":c"):
        cs, query = True, query[:-2]
    elif query.endswith(":i"):
        cs, query = False, query[:-2]

    # raw regex
    if query.startswith("/") and query.endswith("/") and len(query) >= 3:
        pattern = _compile(query[1:-1], cs or False)
        label = "regex"
    else:
        # Boolean modes
        if " & " in query and " | " in query:
            rprint("[yellow]Mixing & and | not allowed.[/]" if USE_RICH else "Cannot mix & and |.")
            return None, ""
        if " & " in query:                            # AND
            parts = query.split(" & ")
            regex = "".join(f"(?=.*{_token_to_regex(p.strip())})" for p in parts) + ".*"
            pattern = _compile(regex, cs or False)
            label = "AND"
        elif " | " in query:                          # OR
            parts = query.split(" | ")
            regex = "|".join(_token_to_regex(p.strip()) for p in parts)
            pattern = _compile(regex, cs or False)
            label = "OR"
        else:                                         # single token
            if query.startswith('"') and query.endswith('"'):
                body = re.escape(query[1:-1]); label = "phrase"
            elif query.startswith("="):
                body = rf"\b{re.escape(query[1:])}\b"; label = "whole-word"
            else:
                body = re.escape(query); label = "substring"
            pattern = _compile(body, cs or False)

    # perform search
    hits = [(r, t) for r, t in raw.items() if pattern.search(t)]
    if not hits:
        rprint("[red]No matches found.[/]" if USE_RICH else "No matches found.")
        return None, ""

    cs_note = "case-sensitive" if pattern.flags & re.IGNORECASE == 0 else "case-insensitive"
    hdr = f"\nFound {len(hits)} {cs_note} {label} result(s):"
    rprint(f"[bold cyan]{hdr}[/]" if USE_RICH else hdr)
    for i, (ref, verse) in enumerate(hits, 1):
        plain(f"{i}. {ref}: {verse}")

    ctx = "\n".join(f"{r}: {t}" for r, t in hits)
    choice = input("\nResult # | ai | Enter: ").strip()
    if choice.lower() == "ai":
        ask_ai(ctx)
        return None, ""
    if choice.isdigit() and 1 <= int(choice) <= len(hits):
        ref = hits[int(choice) - 1][0]
        bc, _ = ref.rsplit(":", 1)
        parts = bc.split()
        return " ".join(parts[:-1]), int(parts[-1])
    return None, ctx  # user cancelled, keep context
# ──────────────────────────────────────────────────────────────────────────

# ─── Main loop ────────────────────────────────────────────────────────────

def main() -> None:
    global DEFAULT_MODEL
    show_books_next = True  # whether to list books at the top of the next loop

    while True:
        if show_books_next:
            list_books()
        show_books_next = True  # reset; can be switched off by certain commands

        cmd = input("\nBook | search | searchguide | ai | model | exit: ").strip()
        cmd_lower = cmd.lower()

        # top‑level commands -------------------------------------------------
        if cmd_lower == "exit":
            break
        if cmd_lower == "searchguide":
            display_searchguide()
            show_books_next = False  # suppress book list on immediate return
            continue
        if cmd_lower == "ai":
            ask_ai("")
            continue
        if cmd_lower == "model":
            m = choose_model()
            if m:
                DEFAULT_MODEL = m
            continue
        if cmd_lower == "search":
            term = input("Search term: ").strip()
            b, c = search(term)
            if not b:
                continue
        elif cmd not in bible:
            rprint("[yellow]Book not found.[/]" if USE_RICH else "Book not found.")
            continue
        else:
            list_chapters(cmd)
            ch = input(f"Chapter in {cmd}: ").strip()
            if not ch.isdigit() or int(ch) not in bible[cmd]:
                rprint("[yellow]Invalid chapter.[/]" if USE_RICH else "Invalid chapter.")
                continue
            b, c = cmd, int(ch)

        # --------------------------------------------------------------
        # At this point we have a valid (book, chapter)
        last_ctx = ""
        while True:
            read_chapter(b, c)
            last_ctx = f"{b} {c}\n" + "\n".join(
                f"{v}. {bible[b][c][v]}" for v in sorted(bible[b][c])
            )
            choice = input("\n[n]ext [p]rev [ai] [model] [b]ooks [exit]: ").strip().lower()
            if choice == "n":
                nxt = next_chap(b, c)
                if nxt is not None:
                    c = nxt
                else:
                    rprint("[yellow]Last chapter in book.[/]" if USE_RICH else "Last chapter in book.")
            elif choice == "p":
                prv = prev_chap(b, c)
                if prv is not None:
                    c = prv
                else:
                    rprint("[yellow]First chapter in book.[/]" if USE_RICH else "First chapter in book.")
            elif choice == "ai":
                ask_ai(last_ctx, DEFAULT_MODEL)
            elif choice == "model":
                m = choose_model()
                if m:
                    DEFAULT_MODEL = m
            elif choice == "b":
                break
            elif choice == "exit":
                sys.exit()
            else:
                rprint("[yellow]Invalid command.[/]" if USE_RICH else "Invalid command.")
        # end inner chapter loop
    # end while True main loop
# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    rprint(
        f"[blue]Bible reader started – {ts}[/]" if USE_RICH else f"Bible reader started – {ts}"
    )
    main()
