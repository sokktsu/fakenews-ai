"""
prepare_dataset.py — Sole Merger
Merges all raw collector CSVs into combined_dataset.csv.

This is the ONLY script that writes combined_dataset.csv. It performs no
downloads and no scraping — each collector owns exactly one raw file:

  runner_download_foreign.py → datasets_foreign.csv              (WELFake + ISOT)
  runner_scraper.py          → datasets_scraped_ph_factcheck.csv (PH fact-check pairs)
  runner_rss.py              → datasets_rss_ph_real_news.csv     (PH real news RSS)

Run order (from fresh start):
  1. python ai_models/data/runner_download_foreign.py  (once — benchmarks)
  2. python ai_models/data/runner_scraper.py           (once — archive scrape)
  3. python ai_models/data/runner_rss.py               (daily RSS collection)
  4. python ai_models/data/clean_scraped.py            (drop junk from the scraped CSV)
  5. python ai_models/data/prepare_dataset.py          (this file — builds final dataset)

Usage: python ai_models/data/prepare_dataset.py
Output: ai_models/data/combined_dataset.csv
"""
import os
import re
import pandas as pd
from loguru import logger

OUTPUT_PATH = "ai_models/data/combined_dataset.csv"
os.makedirs("ai_models/data", exist_ok=True)

# (display name, csv path, command that produces it)
SOURCES = [
    ("Foreign (WELFake+ISOT)", "ai_models/data/datasets_foreign.csv",              "python ai_models/data/runner_download_foreign.py"),
    ("PH RSS",                 "ai_models/data/datasets_rss_ph_real_news.csv",     "python ai_models/data/runner_rss.py"),
    ("PH Fact-Check",          "ai_models/data/datasets_scraped_ph_factcheck.csv", "python ai_models/data/runner_scraper.py"),
]


def near_dup_signature(text: str, prefix_len: int = 150) -> str:
    """
    Cheap near-duplicate key: strip URLs, lowercase, drop everything but word
    characters, and keep the first `prefix_len` characters. Reworded reposts
    and articles that differ only in punctuation, casing, or trailing
    boilerplate collapse to the same signature, so exact-match dedup misses
    them but this catches them. Not a substitute for MinHash — just a fast
    first-pass guard.

    Uses a Unicode-aware \\w filter so non-Latin scripts (e.g. Filipino,
    Cyrillic, CJK) keep a meaningful signature instead of collapsing to empty
    — important for the multilingual model.
    """
    text = re.sub(r"http\S+|www\S+", "", text)
    norm = re.sub(r"[^\w]", "", text.lower(), flags=re.UNICODE)
    return norm[:prefix_len]


def load_source(name: str, path: str, producer: str) -> pd.DataFrame:
    """Load one raw collector CSV, keeping text + label and tagging each row
    with its origin (`source`) so downstream training can report accuracy per
    source — e.g. Filipino PH content vs. English foreign data."""
    if not os.path.exists(path):
        logger.info(f"{name}: {path} not found — skipping.")
        logger.info(f"  Produce it with: {producer}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)[["text", "label"]].dropna()
        df["label"] = pd.to_numeric(df["label"], errors="coerce")
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)
        df["source"] = name
        logger.info(f"{name}: {len(df)} samples loaded")
        return df
    except Exception as e:
        logger.warning(f"{name}: failed to load ({e})")
        return pd.DataFrame()


def prepare():
    logger.info("=" * 60)
    logger.info("DATASET PREPARATION (sole merger)")
    logger.info("=" * 60)

    frames      = []
    source_info = {}

    for name, path, producer in SOURCES:
        df = load_source(name, path, producer)
        if not df.empty:
            frames.append(df)
            source_info[name] = len(df)

    if not frames:
        logger.error("No raw datasets found. Run the collector scripts first (see docstring).")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["text", "label"])
    # Normalize to single-line text so every record is exactly one row /
    # two columns in any CSV viewer, then dedup on the normalized text.
    combined["text"]  = combined["text"].map(lambda t: re.sub(r"\s+", " ", str(t)).strip())

    # Conflicting duplicates: identical text labelled both REAL and FAKE.
    # Report before dedup silently keeps whichever copy comes first.
    conflicts = int(combined.groupby("text")["label"].nunique().gt(1).sum())
    if conflicts:
        logger.warning(f"{conflicts} identical texts carry BOTH labels — check collector quality.")

    exact_dups = int(combined["text"].duplicated().sum())
    combined = combined.drop_duplicates(subset=["text"])
    combined["label"] = combined["label"].astype(int)
    combined = combined[combined["text"].str.len() > 20]

    # Near-duplicates: exact dedup misses reworded reposts and articles that
    # differ only in casing/punctuation/boilerplate (e.g. wire-service
    # "Factbox" reposts). Drop them here so they can never straddle a
    # train/test split downstream.
    sig       = combined["text"].map(near_dup_signature)
    near_dups = int(sig.duplicated().sum())
    before_nd = len(combined)
    combined  = combined.loc[~sig.duplicated()]
    logger.info(f"Dedup: {exact_dups} exact + {near_dups} near-duplicates removed "
                f"(normalized 150-char prefix).")
    if near_dups > before_nd * 0.05:
        logger.warning(f"{near_dups} near-duplicates ({near_dups / before_nd:.1%} of data) — "
                       f"likely reposts/templated articles; check collectors for overlap.")

    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    combined.to_csv(OUTPUT_PATH, index=False)

    fake = (combined["label"] == 1).sum()
    real = (combined["label"] == 0).sum()

    logger.info("=" * 60)
    logger.info("DATASET SUMMARY")
    logger.info("=" * 60)
    for name, count in source_info.items():
        logger.info(f"  {name:<25} {count:>8} samples")
    logger.info("-" * 60)
    logger.info(f"  {'Total (after dedup)':<25} {len(combined):>8} samples")
    logger.info(f"  {'Fake (label=1)':<25} {fake:>8}")
    logger.info(f"  {'Real (label=0)':<25} {real:>8}")
    logger.info("=" * 60)
    logger.info(f"Saved to: {OUTPUT_PATH}")

    if fake == 0 or real == 0:
        logger.warning("WARNING: dataset contains only ONE class — training on this will fail or be meaningless.")
        logger.warning("Make sure datasets_foreign.csv (WELFake+ISOT) is present for FAKE samples.")

    # Class-balance guard (warn-only, non-destructive). Fake-news detectors
    # skew toward whichever class dominates, which erodes minority-class recall
    # (usually FAKE). This surfaces drift before training WITHOUT deleting any
    # data — the fix is to collect more of the minority class, not down-sample.
    total        = fake + real
    minority_pct = min(fake, real) / total if total else 0
    BALANCE_FLOOR = 0.40   # warn if the minority class falls below 40%
    if total and minority_pct < BALANCE_FLOOR:
        lean = "FAKE" if fake < real else "REAL"
        logger.warning(f"Class imbalance: minority class ({lean}) is only {minority_pct:.1%} "
                       f"of the data (threshold {BALANCE_FLOOR:.0%}).")
        logger.warning(f"  Collect more {lean} examples and watch FAKE recall in training reports.")
    else:
        logger.info(f"Class balance OK: minority class at {minority_pct:.1%} (threshold {BALANCE_FLOOR:.0%}).")


if __name__ == "__main__":
    prepare()
