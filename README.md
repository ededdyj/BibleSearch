# Bible Search + AI Assistant

A versatile Bible study tool with both a terminal-based CLI and a Streamlit-powered web interface.

**Features**
- **CLI interface**: navigate by book/chapter, perform searches (substring, whole‑word, phrase, regex, Boolean AND/OR, case flags), built-in search cheat-sheet, AI Q&A, live model switching, cost tracking, rich console output.
- **Web interface (Streamlit)**: chapter and search views, AI assistant sidebar, search cheat-sheet expander, audio streaming from Internet Archive (kjvaudio), direct download URL and fallback streaming support.
- **Audio streaming**: stream or download KJV audio from Archive.org using `kjvaudio_metadata.json` and the included `audio/` folder.
- **JSON data support**: uses `verses-1769.json` for KJV verse data; drop in your own translation with the same key format.
- **Customization**: tweak search logic, output style, AI prompts, model pricing, or swap in your translation.

## Quick Start

```bash
git clone <repo-url>
cd BibleSearch
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### CLI Mode

```bash
export OPENAI_API_KEY="sk-..."
python bible_reader.py
```

### Web Mode (Streamlit)

```bash
export OPENAI_API_KEY="sk-..."
streamlit run streamlit_app.py
```

## CLI Usage

Run `python bible_reader.py` and use the interactive prompts:

```text
Bible reader started – YYYY-MM-DD HH:MM:SS
Books of the Bible:
1. Genesis
2. Exodus
...
Book | search | searchguide | ai | model | exit:
```

- **Book**: type a book name exactly (e.g., `Genesis`, `1 Samuel`)
- **search**: enter search mode (supports substring, whole-word, phrase, regex, AND/OR, case flags)
- **searchguide**: view the built-in search cheat-sheet
- **ai**: ask AI about the current context (chapter or search results)
- **model**: change the AI model and view cost info
- **exit**: quit the program

Inside a chapter view, you can use:

```text
[n]ext | [p]rev | [ai] | [model] | [b]ooks | exit
```

## Web Interface

The Streamlit app (`streamlit_app.py`) provides:

- Sidebar controls for book/chapter navigation and view selection (Chapter View vs Search Results)
- Embedded search cheat-sheet and search input
- AI assistant with model selection and cost display
- Audio streaming controls to play KJV audio from Archive.org
- Previous/Next audio chapter navigation buttons

Launch with `streamlit run streamlit_app.py` and open the provided local URL.

## Data Files

- `verses-1769.json`: KJV (1769) verse data in `{"Book Chap:Verse": "text"}` format.
- `kjvaudio_metadata.json`: cached metadata for KJV audio files (downloaded from Archive.org).
- `audio/`: optional folder to store downloaded MP3 files.

## Configuration

- **OPENAI_API_KEY**: environment variable for OpenAI API key (required for AI features).
- **MODEL_PRICES**: adjust pricing table in code to track AI costs.
- **Search Behavior**: tweak search logic in `bible_reader.py` or `streamlit_app.py`.
- **UI Style**: disable or customize Rich or Streamlit styles as needed.

## Contributing

Contributions welcome! Please open issues or pull requests for feature suggestions or bug fixes.

## License

Scripture data (`verses-1769.json`) is presumed public domain (KJV 1769). Code is provided without warranty; add a license if desired before publishing.
