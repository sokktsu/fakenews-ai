"""
runner_scraper.py — Fact-Check Page Scraper Runner
Runs per-site scrapers and saves results after EACH site finishes,
so a crash or Ctrl+C during one site never loses another site's data.

Usage:
    python ai_models/data/runner_scraper.py                     # all sites
    python ai_models/data/runner_scraper.py all                 # all sites
    python ai_models/data/runner_scraper.py rappler             # one site only
    python ai_models/data/runner_scraper.py tsekph
    python ai_models/data/runner_scraper.py verafiles           # English archive only
    python ai_models/data/runner_scraper.py verafiles_filipino  # Filipino archive only
    python ai_models/data/runner_scraper.py verafiles rappler   # several sites, in order

    # Re-scrape from scratch (deletes old rows first). --reset applies to
    # EVERY site named in the command; to reset one site but not another,
    # run two separate commands:
    python ai_models/data/runner_scraper.py verafiles --reset
    python ai_models/data/runner_scraper.py verafiles rappler --reset

    # Quick test (3 pages/clicks per site):
    # Set TEST_RUN = True below before running.

Output: ai_models/data/datasets_scraped_ph_factcheck.csv  (this file ONLY)
        Merging into combined_dataset.csv happens exclusively in
        prepare_dataset.py — run it after this script.
"""
import os, sys, time
import pandas as pd
from datetime import datetime
from loguru import logger

from shared_utils import get_selenium_driver

# ── Per-site scraper modules ───────────────────────────────────────────────────
from scrapers import scraper_rappler
from scrapers import scraper_tsekph
from scrapers import scraper_verafiles

OUTPUT_CSV = "ai_models/data/datasets_scraped_ph_factcheck.csv"

# ── Config ─────────────────────────────────────────────────────────────────────
# TEST_RUN = True  → 3 pages/clicks per site (fast sanity check)
# TEST_RUN = False → full archive run (default)
TEST_RUN = False

# INCREMENTAL = False → scrape everything from page 1 (initial collection)
# INCREMENTAL = True  → skip URLs already in datasets_scraped_ph_factcheck.csv (subsequent runs)
INCREMENTAL = True

# ── Scraper registry ───────────────────────────────────────────────────────────
# key → (module, display name, needs_selenium, source names in CSV rows,
#        extra kwargs passed to module.scrape())
SCRAPERS = {
    "rappler":            (scraper_rappler,   "Rappler FactCheck",    True,  ["Rappler FactCheck"],   {}),
    "tsekph":             (scraper_tsekph,    "Tsek.ph",              True,  ["Tsek.ph"],             {}),
    "verafiles":          (scraper_verafiles, "Vera Files (English)", False, ["Vera Files"],          {"section": "english"}),
    "verafiles_filipino": (scraper_verafiles, "Vera Files Filipino",  False, ["Vera Files Filipino"], {"section": "filipino"}),
}


def max_param(key: str) -> int:
    return 3 if TEST_RUN else SCRAPERS[key][0].MAX_PARAM


def save_to_csv(articles: list, output_path: str = OUTPUT_CSV) -> int:
    """Append articles to CSV, skipping duplicates by hash."""
    if not articles:
        return 0

    new_df = pd.DataFrame(articles)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        existing_df     = pd.read_csv(output_path)
        existing_hashes = set(existing_df["hash"].tolist())
        new_df          = new_df[~new_df["hash"].isin(existing_hashes)]
        combined        = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(output_path, index=False, encoding="utf-8-sig")
    return len(new_df)


def reset_site(key: str):
    """Delete one site's rows from the CSV so it can be re-scraped fresh."""
    if not os.path.exists(OUTPUT_CSV):
        logger.info(f"{OUTPUT_CSV} does not exist yet — nothing to reset.")
        return
    sources = SCRAPERS[key][3]
    df      = pd.read_csv(OUTPUT_CSV)
    before  = len(df)
    df      = df[~df["source"].isin(sources)]
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"Reset {SCRAPERS[key][1]}: removed {before - len(df)} rows "
                f"({len(df)} rows from other sites kept).")


def load_existing_urls() -> set:
    """URLs already in the CSV (used by incremental mode to skip re-scraping)."""
    if not (INCREMENTAL and os.path.exists(OUTPUT_CSV)):
        return set()
    try:
        ex_df = pd.read_csv(OUTPUT_CSV)
        if "url" in ex_df.columns:
            urls = set(ex_df["url"].dropna().tolist())
            logger.info(f"Incremental mode: {len(urls)} existing URLs loaded — "
                        "already-scraped articles will be skipped.")
            return urls
    except Exception as e:
        logger.warning(f"Could not load existing URLs: {e}")
    return set()


def print_summary(articles: list):
    if not articles:
        return
    df = pd.DataFrame(articles)
    logger.info("\n--- RESULTS BY SOURCE ---")
    logger.info(f"  {'Source':<30} {'FAKE':>6} {'REAL':>6} {'TOTAL':>7}")
    logger.info("  " + "-" * 52)
    for src, grp in df.groupby("source"):
        fake  = (grp["label"] == 1).sum()
        real  = (grp["label"] == 0).sum()
        logger.info(f"  {src:<30} {fake:>6} {real:>6} {len(grp):>7}")
    logger.info("  " + "-" * 52)
    logger.info(f"  {'TOTAL':<30} {(df['label']==1).sum():>6} {(df['label']==0).sum():>6} {len(df):>7}")

    if "pair_type" in df.columns:
        logger.info("\n--- PAIR TYPE BREAKDOWN ---")
        for pt, count in df["pair_type"].value_counts().items():
            dist = df[df["pair_type"] == pt]["label"].value_counts().to_dict()
            logger.info(f"  {pt:<22} {count:>5}  {dist}")


def run_site(key: str, driver, existing_urls: set) -> int:
    """Scrape one site and save its results to CSV immediately. Returns rows saved."""
    module, name, needs_selenium, _, kwargs = SCRAPERS[key]

    logger.info(f"\n{'='*50}")
    logger.info(f"[{name}]")
    if hasattr(module, "URL"):
        logger.info(f"  Page:  {module.URL}")
    elif hasattr(module, "BASE_URL"):
        logger.info(f"  Page:  {module.BASE_URL}")
    logger.info(f"  Max:   {max_param(key)} {module.PARAM_LABEL}")

    start    = time.time()
    articles = module.scrape(driver, max_param(key), existing_urls=existing_urls, **kwargs)
    elapsed  = round(time.time() - start, 1)

    # Deduplicate within this batch by hash
    seen, unique = set(), []
    for a in articles:
        h = a.get("hash")
        if h and h not in seen:
            seen.add(h)
            unique.append(a)

    saved = save_to_csv(unique)
    logger.info(f"  Done: {len(unique)} unique pairs in {elapsed}s — {saved} new rows saved to CSV.")
    print_summary(unique)
    return saved


def run(keys: list[str]):
    logger.info("=" * 70)
    logger.info("SCRAPER RUNNER — PH Fact-Check Archive Collection")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Sites:   {', '.join(SCRAPERS[k][1] for k in keys)}")
    logger.info(f"Mode:    {'INCREMENTAL (new articles only)' if INCREMENTAL else 'FULL (initial collection)'}")
    logger.info("=" * 70)

    existing_urls = load_existing_urls()
    total_saved   = 0

    # ── Selenium-based sites first (share one browser) ────────────────────────
    selenium_keys = [k for k in keys if SCRAPERS[k][2]]
    if selenium_keys:
        logger.info("\nStarting ChromeDriver for Selenium-based scrapers...")
        try:
            driver = get_selenium_driver(headless=True)
            logger.info("ChromeDriver ready.")
        except Exception as e:
            logger.error(f"ChromeDriver failed: {e}")
            logger.error("pip install selenium webdriver-manager")
            driver = None

        if driver:
            try:
                for key in selenium_keys:
                    total_saved += run_site(key, driver, existing_urls)
                    time.sleep(2)
            finally:
                driver.quit()
                logger.info("\nBrowser closed.")

    # ── requests-based sites ──────────────────────────────────────────────────
    for key in [k for k in keys if not SCRAPERS[k][2]]:
        total_saved += run_site(key, None, existing_urls)

    logger.info("\n" + "=" * 70)
    logger.info("SCRAPER RUNNER COMPLETE")
    logger.info(f"New unique rows saved this run: {total_saved}")
    logger.info(f"Output: {OUTPUT_CSV}")
    logger.info("Next step: python ai_models/data/prepare_dataset.py to merge into combined_dataset.csv")
    logger.info("=" * 70)


if __name__ == "__main__":
    args  = [a.lower() for a in sys.argv[1:]]
    reset = "--reset" in args
    names = [a for a in args if a != "--reset"] or ["all"]

    unknown = [n for n in names if n != "all" and n not in SCRAPERS]
    if unknown:
        logger.error(f"Unknown site(s): {unknown}. Choose from: {list(SCRAPERS.keys())} or 'all'.")
        sys.exit(1)

    if "all" in names:
        keys = list(SCRAPERS.keys())
        if reset:
            logger.error("--reset requires specific sites (e.g. 'verafiles rappler --reset'), "
                         "not 'all'. Delete the CSV manually to reset everything.")
            sys.exit(1)
    else:
        # Keep command order, drop accidental repeats
        keys = list(dict.fromkeys(names))
        if reset:
            for key in keys:
                reset_site(key)

    run(keys)
