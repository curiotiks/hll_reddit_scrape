#!/usr/bin/env python3
"""Generate APA-style LaTeX tables for affinity outputs.

Outputs standalone .tex files to outputs/analysis/affinity/apa_tables.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AFFINITY_SUMMARY = ROOT / "outputs" / "analysis" / "affinity" / "affinity_summary.md"
OUT_DIR = ROOT / "outputs" / "analysis" / "affinity" / "apa_tables"

THEMES = [
    ("1. Help Seeking in Chinese Learning", "19.7%"),
    ("2. Providing Support in Chinese Learning", "46.5%"),
    ("3. Dialect Preservation", "2.8%"),
    ("4. Linguistic Insecurity", "2.8%"),
    ("5. Coping and Emotion Regulation Suggestions", "14.1%"),
    ("6. Identity", "4.2%"),
    ("7. Lack of Parental Support", "7.0%"),
    ("8. The Use of English in Asian Countries", "15.5%"),
    ("9. Others", "19.7%"),
]


def parse_affinity_table() -> tuple[list[str], list[list[str]], list[str]]:
    text = AFFINITY_SUMMARY.read_text()
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("| Subreddit |"):
            start = i
            break
    if start is None:
        raise RuntimeError("Table 1 not found in affinity_summary.md")

    headers = [p.strip() for p in lines[start].strip("|").split("|")]
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        parts = [p.strip() for p in line.strip("|").split("|")]
        rows.append(parts)

    kept = []
    omitted = []
    for row in rows:
        hll_cell = row[3] if len(row) > 3 else ""
        match = re.match(r"(\d+)", hll_cell or "")
        hll_n = int(match.group(1)) if match else 0
        if hll_n == 0:
            omitted.append(row[0])
        else:
            kept.append(row)
    return headers, kept, omitted


def latex_escape(text: str) -> str:
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def make_table1_tex(headers: list[str], rows: list[list[str]], omitted: list[str]) -> str:
    col_spec = "l r r r r r r r r l"
    header_line = " & ".join(latex_escape(h) for h in headers) + " \\\\\n"
    body_lines = "".join(
        " & ".join(latex_escape(str(c)) for c in row) + " \\\\\n"
        for row in rows
    )
    note = ""
    if omitted:
        note = "Subreddits omitted due to 0 HLL posts: " + ", ".join(omitted) + "."
    note = latex_escape(note)

    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{threeparttable}}
\begin{{document}}
\begin{{table}}[ht]
\centering
\begin{{threeparttable}}
\caption{{Volume and Engagement by Subreddit (HLL-Matched Posts Only)}}
\vspace{{0.35em}}
\begin{{tabular}}{{{col_spec}}}
\toprule
{header_line}\midrule
{body_lines}\bottomrule
\end{{tabular}}
\begin{{tablenotes}}[flushleft]
\footnotesize
\item Note. {note}
\end{{tablenotes}}
\end{{threeparttable}}
\end{{table}}
\end{{document}}
"""


def make_themes_tex(themes: list[tuple[str, str]]) -> str:
    header_line = "Theme & Percent \\\\\n"
    body_lines = "".join(
        f"{latex_escape(theme)} & {latex_escape(pct)} \\\\\n" for theme, pct in themes
    )
    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\begin{{document}}
\begin{{table}}[ht]
\centering
\caption{{Themes and Percent of Posts}}
\vspace{{0.35em}}
\begin{{tabular}}{{p{{0.7\textwidth}} r}}
\toprule
{header_line}\midrule
{body_lines}\bottomrule
\end{{tabular}}
\end{{table}}
\end{{document}}
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    headers, rows, omitted = parse_affinity_table()

    table1_tex = make_table1_tex(headers, rows, omitted)
    themes_tex = make_themes_tex(THEMES)

    (OUT_DIR / "table1_volume_engagement_apa7.tex").write_text(table1_tex)
    (OUT_DIR / "themes_apa7.tex").write_text(themes_tex)

    print(f"Wrote: {OUT_DIR / 'table1_volume_engagement_apa7.tex'}")
    print(f"Wrote: {OUT_DIR / 'themes_apa7.tex'}")


if __name__ == "__main__":
    main()
