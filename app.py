"""OSIM — Test Yourself Quiz (Streamlit).

Run locally:  streamlit run app.py
Questions live in questions.json (shared with index.html; see README.md for the format).
"""
import hashlib
import html
import json
import random
import re
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="OSIM Test-Yourself Quiz", page_icon="🛡️", layout="centered",
                   initial_sidebar_state="expanded")

DIFF_LABEL = {"E": "Easy", "M": "Medium", "H": "Hard"}
TYPE_LABEL = {"multi": "Select all that apply", "mc": "Multiple choice", "tf": "True / False", "sa": "Short answer"}
TYPE_SHORT = {"multi": "Multi-select", "mc": "MCQ", "tf": "True / False", "sa": "Short answer"}
TYPE_ORDER = {"multi": 0, "mc": 1, "tf": 2, "sa": 3}   # multi-select questions are shown first
CIRCLED = "①②③④⑤⑥⑦⑧⑨"

# ---------------------------------------------------------------- look & feel (matches index.html)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;800&display=swap');
:root{--bg:#080c14;--s1:#0f1520;--s2:#161d2e;--bd:#1e2940;--ac:#00e5a0;--ac2:#00b4d8;--yl:#fbbf24;
      --rd:#f87171;--gn:#34d399;--pr:#c084fc;--tx:#dfe6f0;--tx2:#7b8aa4;
      --font:'Sora',system-ui,sans-serif;--mono:'DM Mono',ui-monospace,monospace}
.stApp{background:var(--bg);background-image:radial-gradient(ellipse at 30% 0%,rgba(0,229,160,.05),transparent 55%),
       radial-gradient(ellipse at 70% 100%,rgba(0,180,216,.05),transparent 55%);color:var(--tx)}
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp li{font-family:var(--font)}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:860px;padding-top:2rem}

/* header + stats */
.hd{text-align:center;padding:10px 0 6px}
.hd h1{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;letter-spacing:-.03em;margin:0 0 4px;padding:0;
       background:linear-gradient(135deg,var(--ac),var(--ac2));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.hd p{color:var(--tx2);font-size:.88rem;font-weight:300;margin:0}
.stats{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:18px 0 10px}
.stat{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:10px 16px;text-align:center;flex:1;min-width:90px;max-width:160px}
.stat .n{font-size:1.4rem;font-weight:800;color:var(--ac);font-family:var(--mono);line-height:1.3}
.stat .l{font-size:.6rem;text-transform:uppercase;letter-spacing:1.3px;color:var(--tx2)}
.pb{background:var(--s2);border-radius:20px;height:8px;margin:12px 0 4px;overflow:hidden}
.pf{height:100%;background:linear-gradient(90deg,var(--ac),var(--ac2));border-radius:20px}

/* sidebar: quiz setup */
section[data-testid="stSidebar"]{background:var(--s1);border-right:1px solid var(--bd)}
section[data-testid="stSidebar"] [data-testid="stExpander"] details{background:var(--s2);border:1px solid var(--bd);border-radius:10px}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary p{font-size:.85rem;font-weight:600}
.sb-h{font-weight:800;font-size:1.05rem;margin:0 0 2px}
.sb-pool{font-family:var(--mono);font-size:.78rem;color:var(--tx2);margin-bottom:4px} .sb-pool b{color:var(--ac);font-size:1.15rem}
.sb-sec{font-size:.6rem;text-transform:uppercase;letter-spacing:1.4px;color:var(--tx2);margin:14px 0 -4px 2px}
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] button{font-size:.72rem;border-radius:8px;background:var(--s1);border:1px solid var(--bd);color:var(--tx2)}
section[data-testid="stSidebar"] [data-testid="stButtonGroup"] button:hover{border-color:var(--ac);color:var(--tx)}
section[data-testid="stSidebar"] [data-testid="stBaseButton-pillsActive"]{border-color:var(--ac)!important;color:var(--ac)!important;background:rgba(0,229,160,.08)!important}
.st-key-diff_sel [data-testid="stBaseButton-pillsActive"]{border-color:var(--yl)!important;color:var(--yl)!important;background:rgba(251,191,36,.08)!important}
.st-key-type_sel [data-testid="stBaseButton-pillsActive"]{border-color:var(--pr)!important;color:var(--pr)!important;background:rgba(192,132,252,.08)!important}
[class*="st-key-lnk_"] button{background:none!important;border:1px solid var(--bd)!important;color:var(--ac2)!important;min-height:0;padding:2px 6px;font-size:.7rem}
.st-key-reset button{font-size:.76rem;background:var(--s2);border:1px solid var(--bd);color:var(--tx2)}
.st-key-reset button:hover{border-color:var(--rd);color:var(--rd)}

/* main: summary cards */
.mini{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 8px}
.mcard{background:var(--s1);border:1px solid var(--bd);border-radius:9px;padding:5px 10px;font-size:.72rem;color:var(--tx2);display:inline-flex;align-items:center;gap:6px}
.mcard b{color:var(--tx);font-weight:600}
.mcard.stat{font-family:var(--mono)} .mcard.stat b{color:var(--ac)}
.mcard.hint2{border-style:dashed;font-style:italic}
.hd{padding:0 0 4px} .hd h1{font-size:1.7rem} .hd p{font-size:.8rem}

/* mode / toggle buttons */
[class*="st-key-mode_"] button,[class*="st-key-tog_"] button,.st-key-reset button{font-size:.76rem;border-radius:8px;background:var(--s1);border:1px solid var(--bd);color:var(--tx2)}
[class*="st-key-mode_"] button:hover,[class*="st-key-tog_"] button:hover{border-color:var(--ac2);color:var(--ac2)}
[class*="st-key-mode_"] button[kind="primary"],[class*="st-key-tog_"] button[kind="primary"]{border-color:var(--ac2);color:var(--ac2);background:rgba(0,180,216,.1)}
.st-key-reset button:hover{border-color:var(--rd);color:var(--rd)}

/* question card */
.st-key-qcard{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:22px}
.qnum{font-size:.66rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--ac);font-weight:600;display:flex;align-items:center;flex-wrap:wrap;gap:6px}
.qtopic{font-size:.72rem;color:var(--tx2);margin:4px 0 10px}
.qtxt{font-size:1rem;line-height:1.65;margin-bottom:6px}
.tag{display:inline-block;font-size:.58rem;padding:2px 7px;border-radius:4px;letter-spacing:.5px}
.tag.E{background:rgba(52,211,153,.13);color:var(--gn)} .tag.M{background:rgba(251,191,36,.13);color:var(--yl)}
.tag.H{background:rgba(248,113,113,.13);color:var(--rd)} .tag.ty{background:rgba(192,132,252,.13);color:var(--pr)}
.hint{font-size:.72rem;color:var(--pr);margin:-2px 0 8px}

/* option rows: clickable (buttons) and answered (html) */
[class*="st-key-opt"] button,[class*="st-key-tf_"] button{width:100%;justify-content:flex-start;text-align:left;background:var(--s2);
   border:1px solid var(--bd);border-radius:8px;padding:10px 14px;color:var(--tx);min-height:46px}
[class*="st-key-opt"] button div,[class*="st-key-opt"] button p{justify-content:flex-start;text-align:left;font-size:.88rem;font-weight:400}
[class*="st-key-opt"] button:hover,[class*="st-key-tf_"] button:hover{border-color:var(--ac);color:var(--tx);background:var(--s2)}
[class*="st-key-tf_"] button{justify-content:center}
[class*="st-key-optsel_"] button{border-color:var(--ac)!important;background:rgba(0,229,160,.07)!important}
.st-key-submit button,.st-key-sa_submit button{background:linear-gradient(135deg,var(--ac),var(--ac2));color:#06110d;border:none;font-weight:700}
.st-key-submit button:disabled{opacity:.4}
.opt{background:var(--s2);border:1px solid var(--bd);border-radius:8px;padding:11px 14px;font-size:.88rem;line-height:1.45;
     display:flex;align-items:center;gap:10px;margin-bottom:8px}
.opt .mk{width:22px;height:22px;border-radius:50%;border:2px solid var(--bd);display:flex;align-items:center;justify-content:center;
     font-size:.68rem;font-weight:700;flex-shrink:0;font-family:var(--mono)}
.opt.sq .mk{border-radius:5px}
.opt.ok{border-color:var(--gn);background:rgba(52,211,153,.08)} .opt.ok .mk{border-color:var(--gn);background:var(--gn);color:var(--bg)}
.opt.no{border-color:var(--rd);background:rgba(248,113,113,.07)} .opt.no .mk{border-color:var(--rd);color:var(--rd)}
.opt.miss{border-color:var(--gn);border-style:dashed} .opt.miss .mk{border-color:var(--gn);color:var(--gn)}
.opt.dim{opacity:.55}
.opt .why{margin-left:auto;font-size:.66rem;color:var(--tx2);white-space:nowrap}

/* feedback + sources */
.fb{margin-top:6px;padding:12px 14px;border-radius:8px;font-size:.86rem;line-height:1.6}
.fb.ok{background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.25)} .fb.ok b.h{color:var(--gn)}
.fb.no{background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.25)} .fb.no b.h{color:var(--rd)}
.fb .ans{display:block;margin-top:4px;color:var(--tx2);font-size:.82rem}
.src{margin-top:12px;border:1px solid var(--bd);border-radius:8px;background:var(--s2);padding:12px 14px;font-size:.82rem;line-height:1.55}
.src-h{font-size:.62rem;text-transform:uppercase;letter-spacing:1.4px;color:var(--ac2);font-weight:600;margin-bottom:8px}
.src-item+.src-item{margin-top:10px;padding-top:10px;border-top:1px dashed var(--bd)}
.src-doc{font-weight:600}
.src-pg{font-family:var(--mono);font-size:.72rem;color:var(--ac);background:rgba(0,229,160,.08);border-radius:4px;padding:1px 6px;margin-left:6px;white-space:nowrap}
.src-path{display:block;font-family:var(--mono);font-size:.68rem;color:var(--tx2);margin-top:2px;word-break:break-all}
.src-q{margin-top:6px;padding-left:10px;border-left:3px solid var(--ac2);font-style:italic}
.src-note{margin-top:8px;color:var(--tx2);font-size:.76rem}

/* nav */
[class*="st-key-nav_"] button{background:var(--s1);border:1px solid var(--bd);color:var(--tx);border-radius:8px}
[class*="st-key-nav_"] button:hover:not(:disabled){border-color:var(--ac);color:var(--ac)}
.qcount{font-family:var(--mono);font-size:.85rem;color:var(--tx2);text-align:center;padding-top:8px}

/* review */
.rv{background:var(--s1);border:1px solid var(--bd);border-left:3px solid var(--bd);border-radius:10px;padding:14px 16px;margin-bottom:10px;font-size:.86rem;line-height:1.55}
.rv.ok{border-left-color:var(--gn)} .rv.no{border-left-color:var(--rd)}
.rv-meta{font-size:.66rem;color:var(--tx2);margin-bottom:4px} .rv-a{color:var(--tx2);margin-top:4px} .rv-a b{color:var(--tx)}
.foot{text-align:center;color:var(--tx2);font-size:.7rem;margin-top:26px;line-height:1.6}
</style>
""", unsafe_allow_html=True)


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
            item["order"] = order                                  # display position -> source index
            item["correct"] = sorted(q["m"]) if "m" in q else [0]  # correct option(s) listed first in the JSON
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
TYPES = [t for t in TYPE_ORDER if any(q["type"] == t for q in QUESTIONS)]


# ---------------------------------------------------------------- helpers
def h(s) -> str:
    """HTML-escape text, render **bold**/*italic*, and neutralise characters Markdown/LaTeX would eat."""
    s = html.escape(str(s))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    return s.replace("$", "&#36;").replace("*", "&#42;").replace("_", "&#95;").replace("`", "&#96;")


def plain(s) -> str:
    """For widget labels: strip markdown markers and escape $ (labels render Markdown)."""
    return re.sub(r"\*+", "", str(s)).replace("$", r"\$")


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


def answer_html(q) -> str:
    if q["type"] == "tf":
        return "True" if q["tf"] else "False"
    if q["type"] == "sa":
        return h(q["sa"][0])
    return " · ".join(h(q["o"][i]) for i in q["correct"])


def your_html(q, ans) -> str:
    if q["type"] == "tf":
        return "True" if ans else "False"
    if q["type"] == "sa":
        return h(ans)
    return " · ".join(h(q["o"][i]) for i in (ans if isinstance(ans, list) else [ans]))


def sources_html(q) -> str:
    srcs = q.get("src") or []
    if not srcs:
        return ""
    out = '<div class="src"><div class="src-h">📄 Source</div>'
    for s in srcs:
        out += (f'<div class="src-item"><span class="src-doc">{h(s["doc"])}</span>'
                f'<span class="src-pg">PDF p.{s["page"]}</span><span class="src-path">{h(s["path"])}</span>'
                f'<div class="src-q">“{h(s["quote"])}”</div></div>')
    if q.get("src_note"):
        out += f'<div class="src-note">ℹ️ {h(q["src_note"])}</div>'
    return out + "</div>"


def html_block(s: str):
    st.markdown(s, unsafe_allow_html=True)


# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("answers", {})       # qid -> answer
ss.setdefault("pending", {})       # qid -> ticked options of an unsubmitted multi-select
ss.setdefault("pos", 0)
ss.setdefault("current_id", None)
ss.setdefault("mode", "quiz")
ss.setdefault("shuffle", False)
ss.setdefault("wrong_only", False)
ss.setdefault("seed", 1)
ss.setdefault("lec_sel", LEC)
ss.setdefault("mat_sel", MAT)
ss.setdefault("diff_sel", ["E", "M", "H"])
ss.setdefault("type_sel", TYPES)


def set_sel(key, values):
    ss[key] = values


def set_mode(m):
    ss.mode = m


def toggle(key):
    ss[key] = not ss[key]
    if key == "shuffle":
        ss.seed = random.randint(1, 10**9)


# ---------------------------------------------------------------- summaries
def count(tid):
    return sum(1 for q in QUESTIONS if q["t"] == tid and q["d"] in ss.diff_sel and q["type"] in ss.type_sel)


def grp_summary(sel, ids):
    on = [i for i in ids if i in sel]
    if len(on) == len(ids):
        return f"All {len(ids)}"
    if not on:
        return "None"
    return LABELS[on[0]] if len(on) == 1 else f"{len(on)} of {len(ids)}"


def list_summary(sel, all_keys, labels, all_text):
    if len(sel) == len(all_keys):
        return all_text
    return ", ".join(labels[k] for k in all_keys if k in sel) or "None"


def new_seed():
    ss.seed = random.randint(1, 10**9)


# ---------------------------------------------------------------- sidebar: quiz setup
with st.sidebar:
    html_block('<div class="sb-h">⚙️ Quiz setup</div>')
    pool_slot = st.empty()

    def section(title, key, options, fmt, ids=None):
        with st.expander(title, expanded=False):      # fixed label, so it stays open while you click chips
            if ids:
                c1, c2 = st.columns(2)
                c1.button("Select all", key=f"lnk_all_{key}", on_click=set_sel, args=(key, ids), use_container_width=True)
                c2.button("Clear", key=f"lnk_none_{key}", on_click=set_sel, args=(key, []), use_container_width=True)
            st.pills(title, options, selection_mode="multi", format_func=fmt, key=key, label_visibility="collapsed")

    html_block('<div class="sb-sec">Topics</div>')
    section("📚 Lecture slides", "lec_sel", LEC, lambda t: f"{LABELS[t]} · {count(t)}", LEC)
    section("📄 Other materials", "mat_sel", MAT, lambda t: f"{LABELS[t]} · {count(t)}", MAT)
    html_block('<div class="sb-sec">Questions</div>')
    section("☑️ Question type", "type_sel", TYPES,
            lambda k: f"{TYPE_SHORT[k]} · {sum(1 for q in QUESTIONS if q['type'] == k)}")
    section("🎯 Difficulty", "diff_sel", ["E", "M", "H"],
            lambda d: f"{DIFF_LABEL[d]} · {sum(1 for q in QUESTIONS if q['d'] == d)}")

    html_block('<div class="sb-sec">Options</div>')
    st.toggle("⇄ Shuffle question order", key="shuffle", on_change=new_seed)
    st.toggle("✗ Only unanswered / wrong", key="wrong_only")
    reset_slot = st.container()
    progress_slot = st.container()

# ---------------------------------------------------------------- filtering
selected = set(ss.lec_sel) | set(ss.mat_sel)
pool = [q for q in QUESTIONS if q["t"] in selected and q["d"] in ss.diff_sel and q["type"] in ss.type_sel]
items = [q for q in pool if not (ss.wrong_only and is_correct(q, ss.answers.get(q["id"])))]
if ss.shuffle:
    items = items[:]
    random.Random(ss.seed).shuffle(items)
    items.sort(key=lambda q: TYPE_ORDER[q["type"]])   # stable: shuffled within each type, multi-select first
else:
    items = sorted(items, key=lambda q: TYPE_ORDER[q["type"]])  # stable: multi-select first, then topic order

ids = [q["id"] for q in items]
if ss.current_id in ids:
    ss.pos = ids.index(ss.current_id)
ss.pos = max(0, min(ss.pos, len(items) - 1)) if items else 0

answered = [q for q in pool if q["id"] in ss.answers]
correct = [q for q in answered if is_correct(q, ss.answers[q["id"]])]
acc = f"{round(len(correct) / len(answered) * 100)}%" if answered else "–"
pct = (len(answered) / len(pool) * 100) if pool else 0

pool_slot.markdown(f'<div class="sb-pool"><b>{len(items)}</b> questions selected</div>', unsafe_allow_html=True)

with reset_slot:
    if st.button("↻ Reset answers in this selection", key="reset", use_container_width=True):
        ss.confirm_reset = True
    if ss.get("confirm_reset"):
        st.warning(f"Clear your answers for the {len(pool)} selected questions?")
        r1, r2 = st.columns(2)
        if r1.button("Yes, clear", use_container_width=True):
            for q in pool:
                ss.answers.pop(q["id"], None)
            ss.confirm_reset = False
            st.rerun()
        if r2.button("Cancel", use_container_width=True):
            ss.confirm_reset = False
            st.rerun()

with progress_slot.expander("💾 Save / load progress"):
    st.caption("Progress lasts for this browser session. Download it to continue later.")
    st.download_button("Download progress", json.dumps(ss.answers), file_name="osim-quiz-progress.json",
                       mime="application/json", use_container_width=True)
    up = st.file_uploader("Load progress file", type="json")
    if up is not None and st.button("Load", use_container_width=True):
        try:
            loaded = json.loads(up.read())
            ss.answers = {k: v for k, v in loaded.items() if k in BY_ID}
            st.success(f"Loaded {len(ss.answers)} answers.")
        except Exception:
            st.error("That file isn't a valid progress file.")

# ---------------------------------------------------------------- main: header + summary cards
html_block('<div class="hd"><h1>OSIM — Test Yourself</h1>'
           '<p>Operations Security &amp; Incident Management · Lectures L01–L12 + NIST, ISO, CSA, CIS, DBIR, WEF &amp; more</p></div>')

opts = [o for o, on in (("Shuffled", ss.shuffle), ("Unanswered / wrong", ss.wrong_only)) if on]
lec_s, mat_s = grp_summary(ss.lec_sel, LEC), grp_summary(ss.mat_sel, MAT)
cards = [
    f"📚 <b>{'No lectures' if lec_s == 'None' else 'Lectures: ' + h(lec_s)}</b>",
    f"📄 <b>{'No materials' if mat_s == 'None' else 'Materials: ' + h(mat_s)}</b>",
    f"☑️ <b>{h(list_summary(ss.type_sel, TYPES, TYPE_SHORT, 'All types'))}</b>",
    f"🎯 <b>{h(list_summary(ss.diff_sel, ['E', 'M', 'H'], DIFF_LABEL, 'All difficulties'))}</b>",
]
html_block('<div class="mini">' + "".join(f'<span class="mcard">{c}</span>' for c in cards)
           + (f'<span class="mcard">{" · ".join(opts)}</span>' if opts else "")
           + f'<span class="mcard stat">✓ <b>{len(correct)}</b>/{len(answered)} · {acc}</span>'
           + '<span class="mcard hint2">change in the sidebar ←</span></div>'
           + f'<div class="pb"><div class="pf" style="width:{pct:.1f}%"></div></div>')

m1, m2, _ = st.columns([1, 1, 3])
m1.button("▶ Quiz", key="mode_quiz", on_click=set_mode, args=("quiz",),
          type="primary" if ss.mode == "quiz" else "secondary", use_container_width=True)
m2.button("☰ Review all", key="mode_review", on_click=set_mode, args=("review",),
          type="primary" if ss.mode == "review" else "secondary", use_container_width=True)

if not items:
    msg = ("🎉 Nothing left — everything in this selection is answered correctly."
           if ss.wrong_only and pool else "No questions match the current filters — adjust them in the sidebar.")
    html_block(f'<div class="rv"><p style="text-align:center;color:var(--tx2);padding:24px 0">{msg}</p></div>')
    st.stop()


# ---------------------------------------------------------------- review mode
if ss.mode == "review":
    html_block(f'<h3 style="color:var(--ac);font-size:1rem;margin:14px 0 10px">Review — {len(items)} questions</h3>')
    out = []
    for i, q in enumerate(items, 1):
        ans = ss.answers.get(q["id"])
        cls = "" if ans is None else ("ok" if is_correct(q, ans) else "no")
        status = ("— Not answered yet" if ans is None else
                  '<span style="color:var(--gn)">✓ You got this right</span>' if cls == "ok" else
                  f'<span style="color:var(--rd)">✗ Your answer: {your_html(q, ans)}</span>')
        out.append(f'<div class="rv {cls}"><div class="rv-meta">{h(LABELS[q["t"]])} · {DIFF_LABEL[q["d"]]} · {TYPE_SHORT[q["type"]]}</div>'
                   f'<div><b>Q{i}.</b> {h(q["q"])}</div><div class="rv-a">Answer: <b>{answer_html(q)}</b></div>'
                   f'<div class="rv-a"><i>{h(q.get("e", ""))}</i></div><div class="rv-a">{status}</div>{sources_html(q)}</div>')
    html_block("".join(out))
    st.stop()


# ---------------------------------------------------------------- quiz mode
q = items[ss.pos]
ss.current_id = q["id"]
ans = ss.answers.get(q["id"])
done = ans is not None


def record(qid, value):
    ss.answers[qid] = value
    ss.pending.pop(qid, None)


def tick(qid, src):
    cur = set(ss.pending.get(qid, []))
    cur ^= {src}
    ss.pending[qid] = sorted(cur)


def go(delta):
    ss.pos = max(0, min(len(items) - 1, ss.pos + delta))
    ss.current_id = items[ss.pos]["id"]


with st.container(key="qcard"):
    html_block(f'<div class="qnum">Question {ss.pos + 1} of {len(items)}'
               f'<span class="tag {q["d"]}">{DIFF_LABEL[q["d"]]}</span><span class="tag ty">{TYPE_LABEL[q["type"]]}</span></div>'
               f'<div class="qtopic">{h(LABELS[q["t"]])}</div><div class="qtxt">{h(q["q"])}</div>')

    if q["type"] in ("mc", "multi"):
        multi = q["type"] == "multi"
        if not done:
            picked = ss.pending.get(q["id"], [])
            if multi:
                html_block('<div class="hint">Tick every correct option, then press Submit.</div>')
            for pos, src in enumerate(q["order"]):
                if multi:
                    on = src in picked
                    st.button(f"{'☑' if on else '☐'}  {plain(q['o'][src])}",
                              key=f"{'optsel' if on else 'opt'}_{q['id']}_{src}",
                              on_click=tick, args=(q["id"], src), use_container_width=True)
                else:
                    st.button(f"{CIRCLED[pos]}  {plain(q['o'][src])}", key=f"opt_{q['id']}_{src}",
                              on_click=record, args=(q["id"], src), use_container_width=True)
            if multi:
                st.button(f"Submit ({len(picked)} selected)", key="submit", disabled=not picked,
                          on_click=record, args=(q["id"], sorted(picked)))
        else:
            chosen = ans if isinstance(ans, list) else [ans]
            rows = []
            for pos, src in enumerate(q["order"]):
                is_c, is_s = src in q["correct"], src in chosen
                if is_c and is_s:
                    cls, mk, why = "ok", "✓", ""
                elif is_c:
                    cls, mk, why = ("miss" if multi else "ok"), "✓", ("missed" if multi else "")
                elif is_s:
                    cls, mk, why = "no", "✗", ("wrongly ticked" if multi else "")
                else:
                    cls, mk, why = "dim", "·", ""
                rows.append(f'<div class="opt {cls}{" sq" if multi else ""}"><span class="mk">{mk}</span>'
                            f'<span>{h(q["o"][src])}</span>{f"<span class=why>{why}</span>" if why else ""}</div>')
            html_block("".join(rows))

    elif q["type"] == "tf":
        if not done:
            c1, c2 = st.columns(2)
            c1.button("True", key=f"tf_{q['id']}_t", on_click=record, args=(q["id"], True), use_container_width=True)
            c2.button("False", key=f"tf_{q['id']}_f", on_click=record, args=(q["id"], False), use_container_width=True)
        else:
            row = []
            for val in (True, False):
                cls = "ok" if val == q["tf"] else ("no" if val == ans else "dim")
                row.append(f'<div class="opt {cls}" style="flex:1;justify-content:center">{"True" if val else "False"}</div>')
            html_block(f'<div style="display:flex;gap:10px">{"".join(row)}</div>')

    else:  # short answer
        if not done:
            with st.form(f"form_{q['id']}", border=False):
                typed = st.text_input("Your answer", key=f"sa_{q['id']}", placeholder="Type your answer…",
                                      label_visibility="collapsed")
                if st.form_submit_button("Submit", key="sa_submit") and typed.strip():
                    record(q["id"], typed.strip())
                    st.rerun()
        else:
            html_block(f'<div class="opt {"ok" if is_correct(q, ans) else "no"}">Your answer: <b>{h(ans)}</b></div>')

    if done:
        ok = is_correct(q, ans)
        html_block(f'<div class="fb {"ok" if ok else "no"}"><b class="h">{"✓ Correct." if ok else "✗ Incorrect."}</b> '
                   f'{h(q.get("e", ""))}{"" if ok else f"<span class=ans>Answer: <b>{answer_html(q)}</b></span>"}</div>'
                   + sources_html(q))

n1, n2, n3 = st.columns([1, 2, 1])
n1.button("← Prev", key="nav_prev", on_click=go, args=(-1,), disabled=ss.pos == 0, use_container_width=True)
n2.markdown(f'<div class="qcount">{ss.pos + 1} / {len(items)}</div>', unsafe_allow_html=True)
n3.button("Next →", key="nav_next", on_click=go, args=(1,), disabled=ss.pos >= len(items) - 1, use_container_width=True)

html_block('<div class="foot">Unofficial revision aid generated from the course notes — not guaranteed 100% accurate; '
           'each answer shows the page it came from, so check the source if something looks off.</div>')
