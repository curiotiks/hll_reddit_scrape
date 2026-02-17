#!/usr/bin/env python3
"""
Thematic analysis prep script.

Builds thematic analysis subsets, exports a labeled corpus for manual coding,
and writes a summary to outputs/analysis/thematic_summary.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import gensim
from gensim import corpora
from gensim.models.coherencemodel import CoherenceModel
from gensim.models.ldamodel import LdaModel
from gensim.models.phrases import Phrases, Phraser
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer


@dataclass
class ItemView:
    subset: str
    id: str
    type: str
    author: str
    score: Optional[float]
    hll: bool
    is_op: bool
    parent_id: str
    created_utc: Optional[float]
    text: str


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _percentile_threshold(values: Iterable[float], percentile: float) -> Optional[float]:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if percentile <= 0:
        return vals[0]
    if percentile >= 100:
        return vals[-1]
    k = (len(vals) - 1) * (percentile / 100.0)
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    if f == c:
        return vals[f]
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def _item_text(item: dict) -> str:
    if item.get("type") == "post":
        title = item.get("title") or ""
        body = item.get("body") or ""
        return (title + "\n\n" + body).strip()
    return (item.get("body") or "").strip()


def _is_direct_reply_to_op(item: dict) -> bool:
    if item.get("type") != "comment":
        return False
    parent_id = item.get("parent_id") or ""
    return parent_id.startswith("t3_") and item.get("is_op") is False


def _is_not_relevant(item: dict) -> bool:
    if item.get("not_relevant") is True:
        return True
    if item.get("exclude") is True:
        reason = (item.get("exclude_reason") or "").lower()
        if "not hll" in reason or "non-hll" in reason:
            return False
        return True
    return False


def _load_stopwords(filepath: Path) -> set[str]:
    with filepath.open("r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def _preprocess(text: str, extended_stop_words: set[str], lemmatizer: WordNetLemmatizer) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\d+", "", text)
    tokens = word_tokenize(text.lower())
    return [
        lemmatizer.lemmatize(word)
        for word in tokens
        if word.isalpha() and word not in extended_stop_words
    ]


def _compute_coherence(lda_model, texts, dictionary) -> float:
    coherence_model_lda = CoherenceModel(
        model=lda_model, texts=texts, dictionary=dictionary, coherence="c_v"
    )
    return coherence_model_lda.get_coherence()


def _tune_hyperparameters(corpus, dictionary, texts, topic_range, alpha_values, beta_values, log_file: Path):
    best_coherence = 0
    best_params = (None, None, None)
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(message)s")

    for num_topics in topic_range:
        for alpha in alpha_values:
            for beta in beta_values:
                lda_model = LdaModel(
                    corpus=corpus,
                    id2word=dictionary,
                    num_topics=num_topics,
                    passes=30,
                    alpha=alpha,
                    eta=beta,
                    random_state=1015,
                )
                coherence_lda = _compute_coherence(lda_model, texts, dictionary)
                logging.info(
                    f"num_topics: {num_topics}, alpha: {alpha}, beta: {beta}, coherence: {coherence_lda}"
                )
                if coherence_lda > best_coherence:
                    best_coherence = coherence_lda
                    best_params = (num_topics, alpha, beta)

    logging.info(
        f"Best parameters: num_topics: {best_params[0]}, alpha: {best_params[1]}, beta: {best_params[2]}, coherence: {best_coherence}"
    )
    return best_params


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "reddit_comments_replies_review.json"
    output_dir = project_root / "outputs" / "analysis"
    topic_dir = output_dir / "topics"
    lda_dir = topic_dir / "lda"
    bertopic_dir = topic_dir / "bertopic"
    output_dir.mkdir(parents=True, exist_ok=True)
    topic_dir.mkdir(parents=True, exist_ok=True)
    lda_dir.mkdir(parents=True, exist_ok=True)
    bertopic_dir.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Prepare thematic analysis subsets.")
    parser.add_argument(
        "--percentile",
        type=float,
        default=90.0,
        help="Percentile cutoff for top-voted items (e.g., 90 = top 10%%).",
    )
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Run hyperparameter tuning (slow).",
    )
    parser.add_argument(
        "--bertopic",
        action="store_true",
        help="Run BERTopic on the same eHLL corpus (requires bertopic).",
    )
    args = parser.parse_args()

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if not _is_not_relevant(item)]

    # Scores
    post_scores = [_to_float(i.get("score")) for i in data if i.get("type") == "post"]
    comment_scores = [
        _to_float(i.get("score"))
        for i in data
        if i.get("type") in ("comment", "reply")
    ]

    post_threshold = _percentile_threshold(post_scores, args.percentile)
    comment_threshold = _percentile_threshold(comment_scores, args.percentile)

    # Subsets
    top_posts = [
        i
        for i in data
        if i.get("type") == "post"
        and _to_float(i.get("score")) is not None
        and post_threshold is not None
        and _to_float(i.get("score")) >= post_threshold
    ]
    top_comments = [
        i
        for i in data
        if i.get("type") in ("comment", "reply")
        and _to_float(i.get("score")) is not None
        and comment_threshold is not None
        and _to_float(i.get("score")) >= comment_threshold
    ]
    ehll_posts = [
        i for i in data if i.get("type") == "post" and i.get("hll") is True
    ]
    direct_replies = [i for i in data if _is_direct_reply_to_op(i)]

    # Thematic analysis is driven by top-voted items (no thematic flag filter)

    # Build corpus
    corpus: list[ItemView] = []

    def add_items(items, subset_name):
        for i in items:
            corpus.append(
                ItemView(
                    subset=subset_name,
                    id=str(i.get("id") or ""),
                    type=str(i.get("type") or ""),
                    author=str(i.get("author") or ""),
                    score=_to_float(i.get("score")),
                    hll=bool(i.get("hll")),
                    is_op=bool(i.get("is_op")),
                    parent_id=str(i.get("parent_id") or ""),
                    created_utc=_to_float(i.get("created_utc")),
                    text=_item_text(i),
                )
            )

    add_items(top_posts, "top_voted_posts")
    add_items(top_comments, "top_voted_comments")
    add_items(ehll_posts, "ehll_posts")
    add_items(direct_replies, "direct_replies_to_op")

    # De-duplicate by (subset, id)
    seen = set()
    deduped = []
    for item in corpus:
        key = (item.subset, item.id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    # Write CSV
    csv_path = topic_dir / "thematic_corpus.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "subset",
                "id",
                "type",
                "author",
                "score",
                "hll",
                "is_op",
                "parent_id",
                "created_utc",
                "text",
            ],
        )
        writer.writeheader()
        for item in deduped:
            writer.writerow(item.__dict__)

    # Write Markdown table
    md_path = topic_dir / "thematic_corpus.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Thematic Analysis Corpus\n\n")
        f.write("| Subset | ID | Type | Author | Score | HLL | Text |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for item in deduped:
            text_preview = item.text.replace("\n", " ").strip()
            if len(text_preview) > 120:
                text_preview = text_preview[:117] + "..."
            f.write(
                f"| {item.subset} | {item.id} | {item.type} | {item.author} | {item.score} | {item.hll} | {text_preview} |\n"
            )

    # Summary
    summary_path = topic_dir / "thematic_summary.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("# Thematic Analysis Summary\n\n")
        f.write(f"- Source: `{data_path}`\n")
        f.write(f"- Generated: {now}\n")
        f.write(f"- Percentile cutoff: {args.percentile} (top {100 - args.percentile:.1f}%)\n\n")
        f.write("## Subset Counts\n\n")
        f.write("| Subset | Count |\n|---|---|\n")
        f.write(f"| Top-voted posts | {len(top_posts)} |\n")
        f.write(f"| Top-voted comments/replies | {len(top_comments)} |\n")
        f.write(f"| eHLL posts | {len(ehll_posts)} |\n")
        f.write(f"| Direct replies to OP | {len(direct_replies)} |\n\n")

        f.write("## Top Candidates by Score (Excerpts)\n\n")
        f.write("### Top-voted posts\n")
        for item in sorted(top_posts, key=lambda i: _to_float(i.get("score")) or 0, reverse=True)[:20]:
            text_preview = _item_text(item).replace("\n", " ").strip()
            if len(text_preview) > 200:
                text_preview = text_preview[:197] + "..."
            f.write(f"- ({item.get('score')}) {text_preview}\n")

        f.write("\n### Top-voted comments/replies\n")
        for item in sorted(top_comments, key=lambda i: _to_float(i.get("score")) or 0, reverse=True)[:20]:
            text_preview = _item_text(item).replace("\n", " ").strip()
            if len(text_preview) > 200:
                text_preview = text_preview[:197] + "..."
            f.write(f"- ({item.get('score')}) {text_preview}\n")

    # Topic modeling by cohorts
    post_weight = 3

    cohorts = {
        "all": data,
        "hll": [i for i in data if i.get("hll") is True],
        "non_hll": [i for i in data if i.get("non_hll") is True],
        "adoptee": [i for i in data if i.get("adoptee") is True],
    }

    stopwords_file = project_root / "04_analysis" / "stop_words.txt"
    additional_stopwords = _load_stopwords(stopwords_file)
    extended_stop_words = set(stopwords.words("english")).union(additional_stopwords)
    lemmatizer = WordNetLemmatizer()

    def build_weighted_texts(items: list[dict]) -> list[str]:
        texts = []
        for item in items:
            text = _item_text(item)
            if not text:
                continue
            if item.get("type") == "post":
                texts.extend([text] * post_weight)
            else:
                texts.append(text)
        return texts

    lda_results = {}
    for name, items in cohorts.items():
        lda_start = time.time()
        top_texts = build_weighted_texts(items)
        processed_texts = [
            _preprocess(text, extended_stop_words, lemmatizer) for text in top_texts if text
        ]
        processed_texts = [t for t in processed_texts if len(t) >= 5]

        if not processed_texts:
            lda_results[name] = {"skipped": "No texts after preprocessing", "topics_csv": None}
            continue

        bigram = Phrases(processed_texts, min_count=5, threshold=100)
        trigram = Phrases(bigram[processed_texts], threshold=100)
        bigram_mod = Phraser(bigram)
        trigram_mod = Phraser(trigram)

        processed_texts = [bigram_mod[doc] for doc in processed_texts]
        processed_texts = [trigram_mod[bigram_mod[doc]] for doc in processed_texts]

        dictionary = corpora.Dictionary(processed_texts)
        dictionary.filter_extremes(no_below=5, no_above=0.5)
        if len(dictionary) == 0:
            dictionary = corpora.Dictionary(processed_texts)
            dictionary.filter_extremes(no_below=1, no_above=0.9)
        if len(dictionary) == 0:
            lda_results[name] = {"skipped": "Dictionary empty after filtering", "topics_csv": None}
            continue

        corpus = [dictionary.doc2bow(text) for text in processed_texts]

        topic_range = range(2, 7)
        alpha_values = [a / 10.0 for a in range(1, 11)]
        beta_values = [b / 10.0 for b in range(1, 11)]
        log_file = lda_dir / "thematic_hyperparameter_log.txt"

        if args.tune:
            best_params = _tune_hyperparameters(
                corpus, dictionary, processed_texts, topic_range, alpha_values, beta_values, log_file
            )
            best_num_topics, _, _ = best_params
        else:
            best_num_topics = 4

        lda_model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=best_num_topics,
            passes=30,
            alpha="auto",
            eta="auto",
            random_state=1015,
        )
        final_coherence = _compute_coherence(lda_model, processed_texts, dictionary)

        topics_data = []
        for idx, topic in lda_model.show_topics(formatted=False):
            topic_words = ", ".join([f"{word} ({weight:.4f})" for word, weight in topic])
            topics_data.append({"Topic": idx, "Words": topic_words})

        topics_csv = lda_dir / f"thematic_topics_{name}.csv"
        with topics_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Topic", "Words"])
            writer.writeheader()
            writer.writerows(topics_data)

        lda_results[name] = {
            "skipped": None,
            "topics_csv": topics_csv,
            "coherence": final_coherence,
            "topics": best_num_topics,
            "duration_min": round((time.time() - lda_start) / 60, 3),
        }

    with summary_path.open("a", encoding="utf-8") as f:
        f.write("## Topic Model (LDA)\n\n")
        f.write("- Corpus: each cohort (posts weighted higher than comments/replies)\n")
        f.write(f"- Post weight multiplier: {post_weight}\n")
        f.write("- Alpha: auto\n")
        f.write("- Beta: auto\n\n")
        for name, result in lda_results.items():
            f.write(f"### Cohort: {name}\n")
            if result.get("skipped"):
                f.write(f"- Skipped: {result['skipped']}\n\n")
                continue
            f.write(f"- Topics: {result['topics']}\n")
            f.write(f"- Coherence (c_v): {result['coherence']:.4f}\n")
            f.write(f"- Topics CSV: `{result['topics_csv']}`\n")
            f.write(f"- Duration (min): {result['duration_min']}\n\n")
        f.write("## How to Interpret LDA Topics\n\n")
        f.write("- Each topic is a list of **words with weights**.\n")
        f.write("- The **weight** next to a word reflects its importance within that topic.\n")
        f.write("- Read the top 5–10 words and assign a **human label**.\n")
        f.write("- Topics are **algorithmic suggestions**, not final themes.\n")

    print(f"Wrote thematic summary to: {summary_path}")
    print(f"Wrote corpus CSV to: {csv_path}")
    print(f"Wrote corpus MD to: {md_path}")
    for name, result in lda_results.items():
        if result.get("topics_csv"):
            print(f"Wrote LDA topics CSV ({name}) to: {result['topics_csv']}")
        else:
            print(f"Skipped LDA for cohort {name}.")

    if args.bertopic:
        try:
            from bertopic import BERTopic
        except ImportError as exc:
            raise SystemExit(
                "BERTopic is not installed. Install bertopic and sentence-transformers to use --bertopic."
            ) from exc

        bertopic_results = {}
        # Stopwords for BERTopic vectorizer
        vectorizer_model = CountVectorizer(stop_words=sorted(extended_stop_words))

        def _build_bertopic_models(doc_count: int):
            try:
                from hdbscan import HDBSCAN
                from umap import UMAP
            except Exception:
                return None, None
            n_neighbors = min(15, max(2, doc_count - 1))
            min_cluster_size = min(5, max(2, doc_count // 2))
            min_samples = min(5, max(1, doc_count - 1))
            umap_model = UMAP(n_neighbors=n_neighbors, n_components=5, metric="cosine", random_state=42)
            hdbscan_model = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)
            return umap_model, hdbscan_model

        for name, items in cohorts.items():
            bertopic_docs = build_weighted_texts(items)
            if not bertopic_docs:
                bertopic_results[name] = {"skipped": "No documents", "topics_csv": None}
                continue

            # Drop short docs for BERTopic to reduce noise
            bertopic_docs = [d for d in bertopic_docs if len(d.split()) >= 50]
            if not bertopic_docs:
                bertopic_results[name] = {"skipped": "No documents after length filtering", "topics_csv": None}
                continue
            if len(bertopic_docs) < 5:
                bertopic_results[name] = {"skipped": "Too few documents for BERTopic (need >=5)", "topics_csv": None}
                continue

            umap_model, hdbscan_model = _build_bertopic_models(len(bertopic_docs))
            topic_model = BERTopic(
                verbose=False,
                vectorizer_model=vectorizer_model,
                min_topic_size=5,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
            )
            topics, _ = topic_model.fit_transform(bertopic_docs)

            bertopic_topics = topic_model.get_topic_info()
            bertopic_csv = bertopic_dir / f"thematic_topics_bertopic_{name}.csv"
            bertopic_topics.to_csv(bertopic_csv, index=False)
            bertopic_results[name] = {"skipped": None, "topics_csv": bertopic_csv}

        with summary_path.open("a", encoding="utf-8") as f:
            f.write("## Topic Model (BERTopic)\n\n")
            f.write("- Corpus: each cohort (posts weighted higher than comments/replies)\n")
            f.write(f"- Post weight multiplier: {post_weight}\n\n")
            for name, result in bertopic_results.items():
                f.write(f"### Cohort: {name}\n")
                if result.get("skipped"):
                    f.write(f"- Skipped: {result['skipped']}\n\n")
                    continue
                f.write(f"- Topics CSV: `{result['topics_csv']}`\n\n")

        for name, result in bertopic_results.items():
            if result.get("topics_csv"):
                print(f"Wrote BERTopic topics CSV ({name}) to: {result['topics_csv']}")
            else:
                print(f"Skipped BERTopic for cohort {name}.")


if __name__ == "__main__":
    main()
