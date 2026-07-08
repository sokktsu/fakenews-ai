"""
runner_download_foreign.py — Foreign Benchmark Dataset Collector
Downloads WELFake from Zenodo into one standardized raw CSV:

  WELFake (72,134 articles) ─→ ai_models/data/datasets_foreign.csv

NOTE ON ISOT: this runner previously also merged the ISOT dataset, but
verification showed ISOT is 100% contained inside WELFake (all 39,100
unique ISOT articles appear word-for-word with identical labels —
Reuters/ISOT is one of the corpora WELFake was built from). Loading it
added nothing after deduplication, so it was removed. The raw files in
ai_models/data/isot/ are no longer needed and may be deleted.

Columns: text, label, source ("welfake").

Text is normalized for Excel/Sheets so every record occupies exactly one row:
  - all newlines/extra whitespace collapsed to single spaces
  - truncated to 32,000 characters (Excel's hard cell limit is 32,767 —
    longer text physically cannot fit in one cell and spills into the next;
    no training loss: BERT reads only the first ~2,500 characters anyway)
Duplicate articles are dropped by text. Saved as UTF-8 with BOM
(encoding="utf-8-sig") so Excel detects the encoding and renders
non-English characters correctly instead of showing mojibake.

Merging into combined_dataset.csv happens exclusively in prepare_dataset.py —
run it after this script.

Run once from a fresh start. Re-run only after deleting datasets_foreign.csv.

Usage: python ai_models/data/runner_download_foreign.py
"""
import os
import io
import re
import pandas as pd
import requests
from loguru import logger

WELFAKE_URL = "https://zenodo.org/record/4561253/files/WELFake_Dataset.csv"
OUTPUT_CSV  = "ai_models/data/datasets_foreign.csv"

os.makedirs("ai_models/data", exist_ok=True)

# Excel's per-cell hard limit is 32,767 characters — anything longer spills
# into adjacent cells even in a perfectly valid CSV. Stay safely under it.
MAX_TEXT_CHARS = 32000


def clean_text(text: str) -> str:
    """One-line, Excel-safe text: collapse whitespace, cap length at a word boundary."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS].rsplit(" ", 1)[0]
    return text


def load_welfake() -> pd.DataFrame:
    """WELFake — 72,134 samples. Label: 0=Real, 1=Fake."""
    logger.info("Downloading WELFake from Zenodo (~230 MB, may take a while)...")
    try:
        resp = requests.get(WELFAKE_URL, timeout=300)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df = df[["title", "text", "label"]].copy()
        df["text"]  = df["title"].fillna("") + " " + df["text"].fillna("")
        df = df[["text", "label"]].dropna()
        df["label"]  = df["label"].astype(int)
        df["source"] = "welfake"
        logger.info(f"WELFake loaded: {len(df)} samples")
        return df
    except Exception as e:
        logger.error(f"WELFake download failed: {e}")
        return pd.DataFrame()


def run():
    logger.info("=" * 60)
    logger.info("FOREIGN BENCHMARK DATASET COLLECTOR (WELFake)")
    logger.info("=" * 60)

    if os.path.exists(OUTPUT_CSV):
        logger.info(f"{OUTPUT_CSV} already exists — skipping. "
                    "(Delete the file to force a rebuild.)")
        return

    combined = load_welfake()
    if combined.empty:
        logger.error("WELFake not loaded — nothing written.")
        return

    combined["text"] = combined["text"].map(clean_text)
    before = len(combined)
    combined = combined[combined["text"].str.len() > 20]
    combined = combined.drop_duplicates(subset=["text"]).reset_index(drop=True)

    # utf-8-sig = UTF-8 with BOM so Excel auto-detects the encoding
    combined.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    fake = (combined["label"] == 1).sum()
    real = (combined["label"] == 0).sum()
    logger.info("-" * 60)
    logger.info(f"Cleaned: {before} rows → {len(combined)} after cleaning + dedup")
    logger.info(f"  Fake (label=1): {fake} | Real (label=0): {real}")
    logger.info(f"Saved to: {OUTPUT_CSV}")
    logger.info("Next step: python ai_models/data/prepare_dataset.py to merge into combined_dataset.csv")


if __name__ == "__main__":
    run()
