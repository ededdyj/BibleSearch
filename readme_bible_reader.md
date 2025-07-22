# Bible Reader + OpenAI Assistant

A terminal Bible reader with a built‑in OpenAI helper. It lets you:

- Navigate by **book/chapter**
- Run **powerful searches** (substring, whole‑word, phrase, regex, Boolean AND/OR, case flags)
- Ask **AI questions** about a chapter or your search results
- **Switch models** on the fly and **track token cost**
- Enjoy **rich colour output** (via `rich`) while preserving `[bracketed]` text
- Pull up a built‑in **search cheat‑sheet** with the `searchguide` command

---

## 1. Quick Start

```bash
# 1) Clone / copy the repo files
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt  # (see below if you don’t have a requirements file)

# 2) Set your OpenAI key
export OPENAI_API_KEY="sk-..."   # PowerShell: $env:OPENAI_API_KEY="sk-..."

# 3) Run it
python bible_reader.py
```

You’ll see:

```
Bible reader started – 2025-07-22 13:37
Books of the Bible:
1. Genesis
2. Exodus
...

Book | search | searchguide | ai | model | exit:
```

Type `searchguide` to view the search cheat‑sheet.

---

## 2. Requirements

- **Python 3.9+** (tested on 3.11 but earlier 3.9+ should be fine)
- Packages:
  - `openai>=1.0.0`
  - `rich` (optional—pretty output)

If you don’t have a `requirements.txt`, create one:

```text
openai>=1.0.0
rich>=13.0.0
```

Then `pip install -r requirements.txt`.

---

## 3. Files

- `bible_reader.py` – the main script
- `verses-1769.json` – KJV (1769) verse data in `{"Book Chap:Verse": "text"}` format

> Drop your own translation by keeping the same key pattern (e.g., `"John 3:16"`).

---

## 4. Environment Setup

1. **OpenAI API key** – required for AI answers:

   - Set `OPENAI_API_KEY` in your environment (preferred), or
   - Let the script prompt you interactively the first run.

2. **Colours** – `rich` is optional. Without it, output is plain text.

---

## 5. Usage Flow

### Main Prompt

```
Book | search | searchguide | ai | model | exit:
```

- **Book** – type a book name *exactly* as listed (e.g. `Genesis`, `1 Samuel`)
- **search** – open the search input
- **searchguide** – display cheat‑sheet and return directly to prompt
- **ai** – ask the assistant about the *last* context (if any)
- **model** – change the model used for AI queries
- **exit** – quit

### Chapter View Prompt

```
[n]ext [p]rev [ai] [model] [b]ooks [exit]:
```

- **n** / **p** – move chapter forward/back
- **ai** – ask about the currently viewed chapter
- **model** – switch AI model
- **b** – back to main menu (books list)
- **exit** – quit immediately

---

## 6. Search Cheat‑Sheet

| Mode       | Example          | Meaning                            |                        |
| ---------- | ---------------- | ---------------------------------- | ---------------------- |
| substring  | `kingdom`        | Finds verses containing `kingdom`  |                        |
| whole‑word | `=love`          | Matches `love` as a whole word     |                        |
| phrase     | `"living water"` | Exact phrase                       |                        |
| regex      | `/grace.*faith/` | Raw Python regex (dotall not set)  |                        |
| AND        | `love & joy`     | Both terms must appear             |                        |
| OR         | \`mercy          | grace\`                            | Either term may appear |
| case flag  | `:c` / `:i`      | Force case sensitive / insensitive |                        |

**Case flags** append to the *entire query*. Example: `love & joy :c` (no space before `:c` in the code, but your query must end with `:c` or `:i`).

After results are shown you can:

- Enter a **result number** to jump to that verse’s chapter
- Type **ai** to ask questions about the full hit list
- Press **Enter** to cancel and keep the context

---

## 7. AI Q&A

- Context = either the **current chapter** or the **current search results** (hit list)
- Enter your question when prompted
- The model, temperature, and costs are shown after each call

### Switching Models

- `model` at any prompt → pick by name or number
- Default pricing table is defined in `MODEL_PRICES`
- Add your own models (i.e., `gpt-4.1-mini`) and cost values as needed

### Cost Tracking

- Each call reports **cost this call** and **cumulative** based on token usage and the table in `MODEL_PRICES`.

---

## 8. Customization Tips

- **Translations**: swap in a different JSON with the same key pattern
- **Search behaviour**: tweak `_token_to_regex` and `search()` logic
- **Output style**: adjust Rich colors or disable Rich entirely
- **Prompt text**: change the system instructions in `ask_ai()` for different AI behaviour
- **Budget model table**: edit `MODEL_PRICES`

---

## 9. Troubleshooting

| Problem                            | Fix / Hint                                           |
| ---------------------------------- | ---------------------------------------------------- |
| `ModuleNotFoundError: openai`      | `pip install openai`                                 |
| `openai.error.AuthenticationError` | Check `OPENAI_API_KEY` is set correctly              |
| `Could not parse reference: ...`   | Your verse JSON key didn’t match `"Book Chap:Verse"` |
| `No matches found.` on search      | Check regex/flags. Try a simpler query               |
| Colours look weird / escape codes  | Install `rich` or run without it (it falls back)     |

---

## 10. License / Data

- Scripture text file (`verses-1769.json`) is presumed public domain (KJV 1769). Verify licensing for any translation you add.
- Code is yours to use/modify. Add a formal license section if you plan to publish.

---

## 11. Roadmap Ideas

- Cross‑verse context (e.g., show a few verses before/after hits)
- Save/load last session state
- Export search results to a file (CSV/Markdown)
- Inline footnotes and cross‑references
- Batch AI queries (e.g., summarize each chapter)

---

Happy studying!

