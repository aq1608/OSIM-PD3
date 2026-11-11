"""OSIM — Test Yourself Quiz (Streamlit).

Run locally:  streamlit run app.py
Questions live in questions.json (see README.md for the format).
"""
import hashlib
import json
import random
import re
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="OSIM Test-Yourself Quiz", page_icon="🛡️", layout="centered")

DIFF_LABEL = {"E": "Easy", "M": "Medium", "H": "Hard"}
DIFF_ICON = {"E": "🟢", "M": "🟡", "H": "🔴"}
TYPE_LABEL = {"mc": "Multiple choice", "multi": "Select all that apply", "tf": "True / False", "sa": "Short answer"}


# ---------------------------------------------------------------- data
BANK_PATH = Path(__file__).parent / "questions.json"


@st.cache_data
def load_bank(bank_hash: str):
    """bank_hash is part of the cache key, so editing questions.json invalidates the cache.
    (Without it, Streamlit Cloud keeps serving the old questions after a push.)"""
    data = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    topics = data["topics"]
    labels = {t["id"]: t["label"] for t in topics}
    questions = []
    for q in data["questions"]:
        if q["t"] not in labels:
            continue
        qid = q["t"] + ":" + hashlib.md5(q["q"].encode("utf-8")).hexdigest()[:10]
        item = dict(q, id=qid)
        if "o" in q:
            item["type"] = "multi" if "m" in q else "mc"
            order = list(range(len(q["o"])))
            random.Random(int(hashlib.md5(qid.encode()).hexdigest(), 16)).shuffle(order)
            item["order"] = order                              # display position -> source index
            item["correct"] = sorted(q["m"]) if "m" in q else [0]  # correct option is listed first in the JSON
        elif "tf" in q:
            item["type"] = "tf"
        else:
            item["type"] = "sa"
        questions.append(item)
    return topics, labels, questions


TOPICS, LABELS, QUESTIONS = load_bank(hashlib.md5(BANK_PATH.read_bytes()).hexdigest())
BY_ID = {q["id"]: q for q in QUESTIONS}
LEC = [t["id"] for t in TOPICS if t["group"] == "Lecture slides"]
MAT = [t["id"] for t in TOPICS if t["group"] != "Lecture slides"]


def md(s: str) -> str:
    """Escape $ so Streamlit doesn't render it as LaTeX."""
    return str(s).replace("$", r"\$")


def md_literal(s: str) -> str:
    """Escape Markdown so a verbatim quote from the PDF renders exactly as written."""
    return re.sub(r"([\\`*_{}\[\]<>#+|~$])", r"\\\1", str(s))


def show_sources(q):
    """Render the source document, page and verbatim quote for a question."""
    srcs = q.get("src") or []
    if not srcs:
        return
    st.markdown("**📄 Source**")
    for s in srcs:
        st.markdown(f"*{md_literal(s['doc'])}* — **PDF page {s['page']}**  \n"
                    f":gray[`{s['path']}`]")
        st.markdown("> " + md_literal(s["quote"]))
    if q.get("src_note"):
        st.caption("ℹ️ " + md(q["src_note"]))


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def is_correct(q, ans) -> bool:
    if ans is None:
        return False
    if q["type"] == "tf":
        return ans == q["tf"]
    if q["type"] == "sa":
        return any(norm(a) == norm(ans) for a in q["sa"])
    return sorted(ans if isinstance(ans, list) else [ans]) == q["correct"]


def answer_text(q) -> str:
    if q["type"] == "tf":
        return "True" if q["tf"] else "False"
    if q["type"] == "sa":
        return q["sa"][0]
    return " · ".join(q["o"][i] for i in q["correct"])


def your_text(q, ans) -> str:
    if q["type"] == "tf":
        return "True" if ans else "False"
    if q["type"] == "sa":
        return str(ans)
    return " · ".join(q["o"][i] for i in (ans if isinstance(ans, list) else [ans]))


# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("answers", {})          # qid -> answer
ss.setdefault("pos", 0)
ss.setdefault("current_id", None)
ss.setdefault("seed", 1)
ss.setdefault("lec_sel", LEC)
ss.setdefault("mat_sel", MAT)
ss.setdefault("diff_sel", ["E", "M", "H"])


def set_all(key, values):
    ss[key] = values


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Filters")
    mode = st.radio("Mode", ["Quiz", "Review all"], horizontal=True)

    st.multiselect("Lecture slides", LEC, format_func=LABELS.get, key="lec_sel")
    c1, c2 = st.columns(2)
    c1.button("All lectures", on_click=set_all, args=("lec_sel", LEC), use_container_width=True)
    c2.button("No lectures", on_click=set_all, args=("lec_sel", []), use_container_width=True)

    st.multiselect("Other materials", MAT, format_func=LABELS.get, key="mat_sel")
    c1, c2 = st.columns(2)
    c1.button("All materials", on_click=set_all, args=("mat_sel", MAT), use_container_width=True)
    c2.button("No materials", on_click=set_all, args=("mat_sel", []), use_container_width=True)

    st.multiselect("Difficulty", ["E", "M", "H"], format_func=lambda d: f"{DIFF_ICON[d]} {DIFF_LABEL[d]}", key="diff_sel")

    shuffle = st.toggle("Shuffle question order")
    if shuffle and st.button("Reshuffle", use_container_width=True):
        ss.seed = random.randint(1, 10**9)
    wrong_only = st.toggle("Only unanswered / wrong")

    st.divider()
    with st.expander("Save / load progress"):
        st.caption("Progress lasts for this browser session. Download it to continue later.")
        st.download_button(
            "Download progress", json.dumps(ss.answers), file_name="osim-quiz-progress.json",
            mime="application/json", use_container_width=True,
        )
        up = st.file_uploader("Load progress file", type="json")
        if up is not None and st.button("Load", use_container_width=True):
            try:
                loaded = json.loads(up.read())
                ss.answers = {k: v for k, v in loaded.items() if k in BY_ID}
                st.success(f"Loaded {len(ss.answers)} answers.")
            except Exception:
                st.error("That file isn't a valid progress file.")

# ---------------------------------------------------------------- filtering
selected_topics = set(ss.lec_sel) | set(ss.mat_sel)
pool = [q for q in QUESTIONS if q["t"] in selected_topics and q["d"] in ss.diff_sel]
items = [q for q in pool if not (wrong_only and is_correct(q, ss.answers.get(q["id"])))]
if shuffle:
    items = items[:]
    random.Random(ss.seed).shuffle(items)

# keep the same question on screen when filters change, if it is still in the list
ids = [q["id"] for q in items]
if ss.current_id in ids:
    ss.pos = ids.index(ss.current_id)
ss.pos = max(0, min(ss.pos, len(items) - 1)) if items else 0

# ---------------------------------------------------------------- header + stats
st.title("🛡️ OSIM — Test Yourself")
st.caption("Operations Security & Incident Management · Lectures L01–L12 + NIST, ISO, CSA, CIS, DBIR, WEF & more")

answered = [q for q in pool if q["id"] in ss.answers]
correct = [q for q in answered if is_correct(q, ss.answers[q["id"]])]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Correct", len(correct))
m2.metric("Answered", len(answered))
m3.metric("In filter", len(pool))
m4.metric("Accuracy", f"{round(len(correct) / len(answered) * 100)}%" if answered else "–")
st.progress(len(answered) / len(pool) if pool else 0.0)

with st.sidebar:
    st.divider()
    if st.button("↻ Reset answers in current filter", use_container_width=True, type="secondary"):
        ss.confirm_reset = True
    if ss.get("confirm_reset"):
        st.warning(f"Clear your answers for the {len(pool)} questions in the current filter?")
        r1, r2 = st.columns(2)
        if r1.button("Yes, clear", use_container_width=True):
            for q in pool:
                ss.answers.pop(q["id"], None)
            ss.confirm_reset = False
            st.rerun()
        if r2.button("Cancel", use_container_width=True):
            ss.confirm_reset = False
            st.rerun()

if not items:
    if wrong_only and pool:
        st.success("🎉 Nothing left — everything in this filter is answered correctly.")
    else:
        st.info("No questions match the current filters.")
    st.stop()


# ---------------------------------------------------------------- review mode
if mode == "Review all":
    st.subheader(f"Review — {len(items)} questions")
    for i, q in enumerate(items, 1):
        ans = ss.answers.get(q["id"])
        status = "⬜" if ans is None else ("✅" if is_correct(q, ans) else "❌")
        with st.container(border=True):
            st.caption(f"{status} {LABELS[q['t']]} · {DIFF_LABEL[q['d']]}")
            st.markdown(f"**Q{i}.** {md(q['q'])}")
            st.markdown(f"**Answer:** {md(answer_text(q))}")
            st.markdown(f"*{md(q.get('e', ''))}*")
            if ans is not None and not is_correct(q, ans):
                st.markdown(f":red[Your answer: {md(your_text(q, ans))}]")
            show_sources(q)
    st.stop()


# ---------------------------------------------------------------- quiz mode
q = items[ss.pos]
ss.current_id = q["id"]
ans = ss.answers.get(q["id"])
done = ans is not None


def record(value):
    ss.answers[q["id"]] = value


with st.container(border=True):
    st.caption(f"QUESTION {ss.pos + 1} OF {len(items)} · {DIFF_ICON[q['d']]} {DIFF_LABEL[q['d']]} · {TYPE_LABEL[q['type']]}")
    st.caption(LABELS[q["t"]])
    st.markdown(f"#### {md(q['q'])}")

    if q["type"] == "mc":
        for pos, src in enumerate(q["order"]):
            text = md(q["o"][src])
            if not done:
                st.button(f"{pos + 1}. {text}", key=f"{q['id']}-o{src}", on_click=record, args=(src,),
                          use_container_width=True)
            elif src in q["correct"]:
                st.success(text, icon="✅")
            elif src == ans:
                st.error(text, icon="❌")
            else:
                st.markdown(f":gray[{pos + 1}. {text}]")

    elif q["type"] == "multi":
        if not done:
            with st.form(f"form-{q['id']}"):
                picks = [src for src in q["order"] if st.checkbox(md(q["o"][src]), key=f"{q['id']}-c{src}")]
                if st.form_submit_button("Submit", type="primary"):
                    if picks:
                        record(sorted(picks))
                        st.rerun()
                    else:
                        st.warning("Tick at least one option.")
        else:
            for src in q["order"]:
                text = md(q["o"][src])
                chosen, right = src in ans, src in q["correct"]
                if chosen and right:
                    st.success(text, icon="✅")
                elif right:
                    st.info(f"{text}  *(missed)*", icon="☑️")
                elif chosen:
                    st.error(text, icon="❌")
                else:
                    st.markdown(f":gray[{text}]")

    elif q["type"] == "tf":
        c1, c2 = st.columns(2)
        for col, val in ((c1, True), (c2, False)):
            label = "True" if val else "False"
            if not done:
                col.button(label, key=f"{q['id']}-{label}", on_click=record, args=(val,), use_container_width=True)
            elif val == q["tf"]:
                col.success(label, icon="✅")
            elif val == ans:
                col.error(label, icon="❌")
            else:
                col.markdown(f":gray[{label}]")

    else:  # short answer
        if not done:
            with st.form(f"form-{q['id']}"):
                typed = st.text_input("Your answer", key=f"{q['id']}-sa", placeholder="Type your answer…")
                if st.form_submit_button("Submit", type="primary") and typed.strip():
                    record(typed.strip())
                    st.rerun()
        else:
            st.text_input("Your answer", value=str(ans), disabled=True, key=f"{q['id']}-sa-done")

    if done:
        explanation = md(q.get("e", ""))
        if is_correct(q, ans):
            st.success(f"**✓ Correct.** {explanation}")
        else:
            st.error(f"**✗ Incorrect.** {explanation}\n\n**Answer:** {md(answer_text(q))}")
        show_sources(q)


def go(delta):
    ss.pos = max(0, min(len(items) - 1, ss.pos + delta))
    ss.current_id = items[ss.pos]["id"]


def jump():
    ss.pos = ss.jump_to - 1
    ss.current_id = items[ss.pos]["id"]


ss.jump_to = ss.pos + 1  # keep the jump box in sync with Prev/Next and filter changes
n1, n2, n3 = st.columns([1, 2, 1])
n1.button("← Prev", on_click=go, args=(-1,), disabled=ss.pos == 0, use_container_width=True)
n3.button("Next →", on_click=go, args=(1,), disabled=ss.pos >= len(items) - 1, use_container_width=True,
          type="primary" if done else "secondary")
with n2:
    st.number_input("Go to question", min_value=1, max_value=len(items), step=1, key="jump_to", on_change=jump, label_visibility="collapsed")

st.caption("Unofficial revision aid generated from the course notes — not guaranteed 100% accurate; "
           "check the source slides if something looks off.")
