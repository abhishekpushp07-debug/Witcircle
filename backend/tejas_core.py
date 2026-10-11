"""Source-aware, review-only PDF segmentation, deterministic scoring and complete reports."""

import re, uuid, html
import fitz
import numpy as np

RULES = {
    "minutes": 180,
    "correct": 4,
    "wrong": -1,
    "skipped": 0,
    "numeric_rule": "Exact integer value; signs and leading zeros accepted; up to 20 digits. No rounding.",
}


def validate_pdf(data):
    if len(data) > 50 * 1024 * 1024:
        raise ValueError("PDF exceeds 50 MB. Split it into smaller documents.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("Upload a valid PDF file, not a renamed document.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ValueError(
            "This PDF is damaged or cannot be read. Export a new unlocked PDF."
        )
    if doc.is_encrypted:
        raise ValueError(
            "Password-protected PDFs are not supported. Supply an unlocked copy."
        )
    if not 1 <= len(doc) <= 300:
        raise ValueError("PDF must contain 1–300 pages. Split larger documents.")
    if any(p.rect.width > 3000 or p.rect.height > 3000 for p in doc):
        raise ValueError(
            "PDF page dimensions are too large. Export standard-size pages."
        )
    return doc


def segment_pdf(data, solution=False):
    doc = validate_pdf(data)
    anchors, sections = [], []
    current_subject = ""
    for pi, page in enumerate(doc):
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width
        )
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if re.search(r"(SECTION|SOLUTIONS)", text) and re.match(
                    r"(MATHEMATICS|PHYSICS|CHEMISTRY)", text
                ):
                    current_subject = text.split(" ")[0].title()
                    sections.append((pi, line["bbox"][1]))
                m = re.match(r"^Q\s*(\d+)\.\s*(.*)", text)
                if (
                    not m
                    or (solution and not re.match(r"Answer\s*:", m[2], re.I))
                    or (not solution and re.match(r"Answer\s*:", m[2], re.I))
                ):
                    continue
                y = line["bbox"][1]
                # Find full-width whitespace above the stem; preserves elevated integrals and determinants.
                top = max(40, int(y) - 2)
                for row in range(int(y), max(39, int(y) - 36), -1):
                    if np.min(pixels[row, 40 : min(pix.width - 35, 560)]) > 245:
                        top = max(40, row - 2)
                        break
                anchors.append(
                    {
                        "number": int(m[1]),
                        "page": pi,
                        "top": top,
                        "header": text,
                        "subject": current_subject,
                    }
                )
    records = []
    for idx, a in enumerate(anchors):
        end = (
            anchors[idx + 1]
            if idx + 1 < len(anchors)
            else {"page": len(doc) - 1, "top": doc[-1].rect.height - 48}
        )
        refs = []
        texts = []
        for pi in range(a["page"], end["page"] + 1):
            page = doc[pi]
            top = a["top"] if pi == a["page"] else 48
            bottom = end["top"] - 1 if pi == end["page"] else page.rect.height - 48
            for sp, sy in sections:
                if sp == pi and top < sy < bottom:
                    bottom = sy - 8
            if bottom <= top + 2:
                continue
            clip = fitz.Rect(40, top, page.rect.width - 38, bottom)
            pix = page.get_pixmap(clip=clip, colorspace=fitz.csGRAY)
            ar = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width
            )
            rows = np.where(np.min(ar, axis=1) < 230)[0]
            if len(rows) == 0:
                continue
            clip.y1 = min(clip.y1, top + int(rows[-1]) + 5)
            refs.append({"page": pi + 1, "rect": [round(v, 2) for v in clip]})
            texts.append(page.get_text(clip=clip))
        text = "\n".join(texts).strip()
        key = (
            re.search(r"Answer:\s*\(?([\-+]?\d+)\)?", a["header"]) if solution else None
        )
        records.append(
            {**a, "refs": refs, "text": text, "answer": key[1] if key else ""}
        )
    return records


def build_questions(
    qdata, sdata, qfile="questions", sfile="solutions", known_tejas=False
):
    qs = segment_pdf(qdata)
    ss = segment_pdf(sdata, True)
    by_number = {}
    for s in ss:
        by_number.setdefault(s["number"], []).append(s)
    counts = {n: sum(q["number"] == n for q in qs) for n in {q["number"] for q in qs}}
    out = []
    for q in qs:
        matches = by_number.get(q["number"], [])
        # Require compatible sections if labels exist. No positional pairing.
        matches = [
            s
            for s in matches
            if not (q["subject"] and s["subject"]) or q["subject"] == s["subject"]
        ]
        s = matches[0] if len(matches) == 1 else {}
        number = q["number"]
        kind = "mcq" if re.search(r"\([1A]\)", q["text"]) else "integer"
        if known_tejas:
            kind = "mcq" if (number - 1) % 25 < 20 else "integer"
        subject = q["subject"] or (
            ["Mathematics", "Physics", "Chemistry"][min((number - 1) // 25, 2)]
            if known_tejas
            else ""
        )
        lines = s.get("text", "").splitlines()
        label = lines[1] if len(lines) > 1 else ""
        opts = {}
        if kind == "mcq":
            chunks = re.split(r"\(([1-4A-D])\)", q["text"])
            # Only a suggestion; source crops and reviewer verification remain mandatory.
            for j in range(1, len(chunks) - 1, 2):
                opts[chunks[j]] = chunks[j + 1].strip()
        issues = []
        if len(matches) != 1:
            issues.append("Missing or ambiguous solution match")
        if counts[number] > 1:
            issues.append("Duplicate question number; resolve section identity")
        if not s.get("answer"):
            issues.append("Answer key requires review")
        out.append(
            {
                "id": str(uuid.uuid4()),
                "number": number,
                "solution_number": s.get("number"),
                "section": subject,
                "subject": subject,
                "type": kind,
                "text": q["text"],
                "options": opts,
                "answer": s.get("answer", ""),
                "solution": s.get("text", ""),
                "topic": label.split(" — ")[0],
                "difficulty": label.split(" — ")[-1] if " — " in label else "",
                "render_mode": "source",
                "q_refs": [{**r, "file_id": qfile} for r in q["refs"]],
                "s_refs": [{**r, "file_id": sfile} for r in s.get("refs", [])],
                "approved": False,
                "issues": issues,
                "accessible_text": "",
                "solution_accessible_text": "",
                "review_note": "",
            }
        )
    return out


def public_question(q):
    return {
        k: q.get(k)
        for k in [
            "id",
            "number",
            "subject",
            "section",
            "type",
            "text",
            "options",
            "topic",
            "render_mode",
            "accessible_text",
            "q_refs",
        ]
    }


def normalize_answer(value, kind):
    value = str(value).strip()
    if not value:
        return ""
    if kind == "integer":
        if not re.fullmatch(r"[+-]?\d{1,20}", value):
            raise ValueError(
                "Enter an integer (up to 20 digits). Decimals and expressions are not accepted."
            )
        return str(int(value))
    return value


def score_attempt(attempt):
    rules = attempt["rules"]
    rows = []
    for q in attempt["questions"]:
        response = attempt.get("answers", {}).get(q["id"], {})
        value = response.get("value", "")
        correct = bool(value) and normalize_answer(
            value, q["type"]
        ) == normalize_answer(q["answer"], q["type"])
        state = "skipped" if not value else "correct" if correct else "incorrect"
        marks = (
            rules["skipped"]
            if state == "skipped"
            else rules["correct"] if correct else rules["wrong"]
        )
        rows.append(
            {
                **q,
                "response": value,
                "marked": response.get("marked", False),
                "outcome": state,
                "marks": marks,
            }
        )
    n = len(rows)
    c = sum(r["outcome"] == "correct" for r in rows)
    w = sum(r["outcome"] == "incorrect" for r in rows)
    tried = c + w
    summary = {
        "score": sum(r["marks"] for r in rows),
        "maximum": n * rules["correct"],
        "correct": c,
        "incorrect": w,
        "skipped": n - tried,
        "attempted": tried,
        "attempt_rate": round(100 * tried / n, 1) if n else 0,
        "accuracy": round(100 * c / tried, 1) if tried else None,
        "penalties": -w * min(0, rules["wrong"]),
        "total_seconds": max(
            0,
            round(
                attempt.get("submitted_at", attempt["started_at"])
                - attempt["started_at"]
            ),
        ),
    }
    for category in ["subject", "topic"]:
        groups = {}
        for r in rows:
            name = r.get(category) or "Unlabelled"
            g = groups.setdefault(
                name, {"count": 0, "correct": 0, "attempted": 0, "score": 0}
            )
            g["count"] += 1
            g["correct"] += int(r["outcome"] == "correct")
            g["attempted"] += int(r["outcome"] != "skipped")
            g["score"] += r["marks"]
        summary[category + "s"] = groups
    return {"summary": summary, "questions": rows}


def crop_png(data, ref, scale=2):
    doc = validate_pdf(data)
    p = ref["page"] - 1
    if p < 0 or p >= len(doc):
        raise ValueError("Source page is out of range.")
    rect = fitz.Rect(ref["rect"])
    if rect.is_empty or not doc[p].rect.contains(rect):
        raise ValueError("Source region is outside the page.")
    return (
        doc[p]
        .get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
        .tobytes("png")
    )


def generate_report(attempt, file_loader):
    result = score_attempt(attempt)
    out = fitz.open()
    blue = (0.145, 0.388, 0.922)
    navy = (0.043, 0.122, 0.227)

    def newpage(title):
        page = out.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(0, 0, 595, 8), color=blue, fill=blue)
        page.insert_text(
            (40, 39), "TEJAS / RESULTS & SOLUTIONS", fontsize=10, color=blue
        )
        page.insert_textbox(fitz.Rect(40, 55, 555, 100), title, fontsize=15, color=navy)
        return page

    p = newpage(attempt["title"])
    s = result["summary"]
    r = attempt["rules"]
    from datetime import datetime, timezone

    text = f"{attempt['exam']} | Nonofficial practice | Content version {attempt.get('version',1)}\nAttempt: {attempt['id']}\nStarted: {datetime.fromtimestamp(attempt['started_at'],timezone.utc).isoformat()}\nScore: {s['score']} / {s['maximum']}\nCorrect: {s['correct']} | Incorrect: {s['incorrect']} | Skipped: {s['skipped']}\nAttempt rate: {s['attempt_rate']}% | Accuracy: {str(s['accuracy'])+'%' if s['accuracy'] is not None else 'Not applicable (no attempts)'}\nAccuracy = correct / attempted. Penalties: {s['penalties']} marks\nElapsed: {s['total_seconds']} seconds\nRules: +{r['correct']} correct, {r['wrong']} wrong, {r['skipped']} unanswered\nNumerical: {r['numeric_rule']}\n\nComplete attempt: {len(result['questions'])} questions in original delivery order, including skipped questions.\nEach question is followed by its matched solution.\nPersonal study copy. Downloaded files are outside Tejas access controls.\nAttribution: {attempt.get('attribution','Owner-supplied content')}"
    p.insert_textbox(fitz.Rect(40, 115, 555, 760), text, fontsize=11, lineheight=1.65)
    for q in result["questions"]:
        p = newpage(f"Question {q['number']} | {q['subject']}")
        y = 108
        p.insert_text(
            (40, y),
            f"Your answer: {q['response'] or 'Unanswered'} | Correct: {q['answer']} | Marks: {q['marks']} | {q['outcome'].title()}",
            fontsize=10,
        )
        y += 24
        for label, refs, plain in [
            ("Question", q.get("q_refs", []), q["text"]),
            ("Matched solution", q.get("s_refs", []), q["solution"]),
        ]:
            if y > 730:
                p = newpage(f"Question {q['number']} continued")
                y = 110
            p.insert_text((40, y), label, fontsize=12, color=blue)
            y += 14
            if q.get("render_mode") == "source" and refs:
                for ref in refs:
                    raw = file_loader(ref["file_id"])
                    clip = fitz.Rect(ref["rect"])
                    scale = min(1, 515 / clip.width)
                    h = clip.height * scale
                    if y + h > 780:
                        p = newpage(f"Question {q['number']} | {label} continued")
                        y = 110
                    # Rasterized isolated crop: no hidden neighboring PDF content is embedded.
                    if h > 650:
                        scale = 650 / clip.height
                        h = 650
                    p.insert_image(
                        fitz.Rect(40, y, 40 + clip.width * scale, y + h),
                        stream=crop_png(raw, ref, 2),
                    )
                    y += h + 16
                    p.insert_text(
                        (40, y),
                        f"Source: {ref['file_id']} | page {ref['page']}",
                        fontsize=7,
                        color=(0.32, 0.38, 0.48),
                    )
                    y += 24
            else:
                if label == "Question" and q.get("type") == "mcq":
                    plain += "\n\n" + "\n".join(
                        f"({key}) {value}"
                        for key, value in q.get("options", {}).items()
                    )
                # Split long text into paragraph chunks, retaining all text and Unicode.
                for chunk in [plain[i : i + 1800] for i in range(0, len(plain), 1800)]:
                    if y > 400:
                        p = newpage(f"Question {q['number']} | {label} continued")
                        y = 110
                    spare, sc = p.insert_htmlbox(
                        fitz.Rect(40, y, 555, 775),
                        '<div style="font-size:11pt">'
                        + html.escape(chunk).replace("\n", "<br>")
                        + "</div>",
                    )
                    y = 775 - spare + 20
    total = len(out)
    for i, p in enumerate(out):
        p.insert_text(
            (40, 819),
            f"Private study report | {i+1} / {total}",
            fontsize=8,
            color=(0.32, 0.38, 0.48),
        )
    return out.tobytes(garbage=4, deflate=True)
