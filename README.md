# OSIM — Test Yourself Quiz

A revision quiz for **Operations Security & Incident Management**, available in two versions that share the same `questions.json`:

- **Streamlit:** `app.py`
- **Static HTML for GitHub Pages:** `index.html`

The quiz has 536 questions across 21 categories. 180 of them are select-all-that-apply, which both versions show first. The categories are one per lecture (L01–L12) and one each for the supporting materials (NIST SP 800-34 / 800-61r2, ISO 22301/22313, the CSA CCoP, the Counter-Ransomware Task Force report, CIS Controls v8.1, Verizon DBIR 2026, the WEF Global Risks Report 2026, BCBS/IMF operational risk, and the FEMA/DHS/SANS/SBF BCP guides).

It is unofficial and not guaranteed 100% accurate. If something looks off, check the source slides.

## Streamlit version: run locally

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder (`app.py`, `questions.json`, `requirements.txt`) to a GitHub repo.
2. At share.streamlit.io, choose **Create app**, pick the repo and branch, and set the main file to `app.py`.

## Static HTML version (GitHub Pages)

`index.html` loads `questions.json` from the same folder, so it needs no build step.

- **GitHub Pages:** in the repo, go to Settings → Pages → deploy from branch, root folder. The quiz is served at the Pages URL.
- **Locally:** browsers block `fetch` on `file://`, so serve the folder rather than double-clicking the file:

  ```bash
  python -m http.server 8000
  ```

  Then open http://localhost:8000.

The HTML version saves your progress in the browser's localStorage. It also supports keyboard shortcuts: `1`–`9`, `T`/`F`, `Enter`, `←`/`→`, and `Esc` to go back to the filters.

## Features

- Both versions share the same dark navy look. You can filter by lectures, other materials, question type and difficulty.
- **HTML layout:** you start on a setup screen with four compact filter cards. Click a card to expand its chips, then press **Start quiz**. During the quiz the filters shrink to a row of small summary cards above the question. Click a card, or press `Esc`, to change filters.
- **Streamlit layout:** the filters sit in the sidebar under collapsible sections, along with the options, reset and save/load. The quiz and **Review all** take up the main page, with your current selection summarised in small cards at the top.
- Four question types: select-all-that-apply, multiple choice, true/false, and short answer. Select-all questions are listed first. To practise only those, set the **Question type** filter to **Multi-select**.
- For select-all questions, tick each option you think is correct, then press **Submit**. Correct ticks, wrong ticks and options you missed are each marked.
- Each answer shows an explanation, and the options are shuffled for every question
- **Review all** mode, **Shuffle question order**, and **Only unanswered / wrong** for retrying mistakes
- Progress is kept for the browser session. Under **Save / load progress** you can download it as a JSON file and load it again later.

## Adding / editing questions

All questions are in `questions.json`:

```json
{"t": "L05", "d": "M", "q": "Question text", "o": ["Correct answer FIRST", "Wrong", "Wrong"], "e": "Explanation"}
{"t": "L05", "d": "E", "q": "Statement…", "tf": true, "e": "…"}
{"t": "L05", "d": "E", "q": "Question…", "sa": ["accepted", "alt answer"], "e": "…"}
{"t": "L05", "d": "M", "q": "Tick all…", "o": ["A", "B", "C", "D"], "m": [0, 2], "e": "…"}
```

- `t` is a topic id from the `topics` list at the top of the file, and `d` is the difficulty: `E`, `M` or `H`.
- Always put the correct MCQ option **first**. The app shuffles the options when it displays them.
- In a multi-select question, `m` lists the indices of the correct options.
- Text supports Markdown (`**bold**`, `*italic*`).

### Source references

Every question has a `src` list that points to where the answer comes from. After you answer a question (and in **Review all**), the app shows a **📄 Source** section with the document, the page and a word-for-word quote:

```json
"src": [{"doc": "L05 Disaster Recovery (slides)", "path": "week 5/L05-Disaster Recovery  v1 30Sep26.pdf", "page": 32, "quote": "Facility with bare minimum support i.e. space, electricity and connection. ..."}],
"src_note": "Optional caveat, e.g. when the detail is in a figure rather than the slide text"
```

- `page` is the PDF page number your PDF viewer shows, which for slides is the slide number. For standards and reports, it can differ from the page number printed on the page.
- `path` is relative to the course notes folder.
- Quotes are copied from the PDF text. Where a slide's layout splits a sentence, the pieces are joined with ` … `.
