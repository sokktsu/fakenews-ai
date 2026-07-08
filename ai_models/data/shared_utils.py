"""
shared_utils.py
Shared helpers used across all collectors and scrapers.
"""
import re, hashlib, json, time
from datetime import datetime
from loguru import logger

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent":      USER_AGENT,
    "Accept":          "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

FAKE_VERDICT_WORDS = [
    "false", "fake", "misleading", "fabricated", "manipulated",
    "satire", "hoax", "disinformation", "misinformation",
    "out of context", "missing context", "lacks context",
    "partially false", "mostly false", "pants on fire",
    "hindi totoo", "maling impormasyon", "peke", "mali",
    "rating: false", "verdict: false", "verdict: fake", "altered", "partly false",
    # Regional-language verdicts used by Rappler fact-check headlines
    "indi matuod", "diri tinuod", "dili tinuod",       # Hiligaynon / Waray / Cebuano "not true"
    "kulang sa konteksto", "manipulado",               # Tagalog "missing context" / "manipulated"
    # VERA Files verdict wording. NOTE: "untrue" and "not true" must be in
    # the FAKE list — they contain "true" as a substring and would
    # otherwise match REAL.
    "untrue", "not true", "needs context", "incorrect", "inaccurate", "unproven",
]
REAL_VERDICT_WORDS = [
    "true", "verified", "accurate", "correct", "confirmed",
    "mostly true", "rating: true", "verdict: true",
    "totoong", "totoo", "napatunayan",
]

CLAIM_PATTERNS = [
    r"claim\s*[:\-\u2013]\s*", r"the claim\s*[:\-\u2013]\s*",
    r"viral claim\s*[:\-\u2013]\s*", r"what was claimed\s*[:\-\u2013]\s*",
    r"(?:viral )?(?:posts?|messages?|videos?) (?:claim|say|allege)",
    r"social media (?:posts?|users?) (?:claim|say|allege)",
    r"circulating (?:online|on social media)",
    r"ang claim\s*[:\-\u2013]\s*", r"sinasabi\s*[:\-\u2013]\s*",
    r"the post (?:claims?|says?|states?)\s*",
    r"being shared (?:online|on social media)\s*",
    r"(?:a |an )?(?:false|fake|fabricated|misleading) (?:post|image|video|article|claim)\s*",
    r"viral na (?:post|balita|mensahe)\s*",
    r"(?:nagsasabing|nagsabi)\s*",
    r"ayon sa (?:post|balita)\s*",
]
DEBUNK_PATTERNS = [
    r"fact\s*[:\-\u2013]\s*", r"verdict\s*[:\-\u2013]\s*", r"rating\s*[:\-\u2013]\s*",
    r"according to (?:official|verified|experts?)",
    r"there is no (?:evidence|proof|record)",
    r"(?:this )?(?:claim|post|image|video) (?:is|was) (?:false|fake|misleading)",
    r"(?:however|but|in fact|actually)[,\s]",
    r"(?:the )?(?:facts?|truth|reality)\s*[:\-\u2013]\s*",
    r"debunked?\s*[:\-\u2013]\s*", r"correction\s*[:\-\u2013]\s*",
    r"katotohanan\s*[:\-\u2013]\s*", r"hindi (?:totoo|tama)",
    r"what (?:actually|really) happened\s*",
    r"according to (?:official|verified|credible)\s*",
    r"(?:official )?(?:records?|data|documents?) show\s*",
    r"(?:experts?|officials?|authorities?) (?:confirmed?|said|stated)\s*",
    r"(?:this is )?(?:false|fake|misleading|inaccurate|incorrect|untrue)",
    r"mali (?:ito|ang)\s*", r"ayon sa (?:opisyal|datos)\s*", r"napatunayan\s*",
]

def fix_encoding(text: str) -> str:
    try:
        return text.encode("cp1252").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

def clean(text: str) -> str:
    text = fix_encoding(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

clean_html = clean

def get_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def _verdict_to_label(verdict: str) -> int:
    v = verdict.lower().strip()
    fake_verdicts = {
        "false","fake","misleading","mostly false","partly false",
        "partially false","altered","fabricated","manipulated",
        "satire","hoax","out of context","missing context",
        "pants on fire","incorrect","inaccurate","1","2",
    }
    real_verdicts = {"true","mostly true","verified","accurate","correct","confirmed","3","4","5"}
    if v in fake_verdicts: return 1
    if v in real_verdicts: return 0
    if any(w in v for w in ["false","fake","mislead","alter","satir","fabricat","manipul","hoax"]): return 1
    if any(w in v for w in ["true","verif","accurat","correct"]): return 0
    return -1

def detect_label(title: str, summary: str = "") -> int:
    combined = ((title or "") + " " + (summary or "")).lower()
    for kw in FAKE_VERDICT_WORDS:
        if kw in combined: return 1
    for kw in REAL_VERDICT_WORDS:
        if kw in combined: return 0
    return 0  # default REAL — safer for ambiguous fact-check titles

def detect_verdict(title: str, summary: str) -> tuple:
    combined = ((title or "") + " " + (summary or "")).lower()
    for kw in FAKE_VERDICT_WORDS:
        if kw in combined: return 1, f"verdict_fake:{kw}"
    for kw in REAL_VERDICT_WORDS:
        if kw in combined: return 0, f"verdict_real:{kw}"
    return 0, "default_real"

# Bumped on every 429 response. Enrichment loops compare this before/after
# each fetch to adaptively slow down while the server is pushing back.
RATE_LIMIT_COUNT = 0


def _fetch_html(url: str, session=None, retries: int = 3):
    import requests
    global RATE_LIMIT_COUNT
    s = session or requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    for attempt in range(retries):
        try:
            resp = s.get(url, timeout=20)
            if resp.status_code == 429:
                RATE_LIMIT_COUNT += 1
                # Honor the server's Retry-After header when present
                retry_after = resp.headers.get("Retry-After", "")
                wait = int(retry_after) if retry_after.isdigit() else 60 * (attempt + 1)
                wait = min(wait, 300)
                logger.warning(f"Rate limited {url}. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 404: return None
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt+1} failed for {url}: {e}")
            time.sleep(3)
    return None

def _extract_claimreview_jsonld(html: str):
    if not html: return None
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        html, re.IGNORECASE
    )
    # Some articles have a ClaimReview with a rating but an EMPTY
    # claimReviewed field. Keep that verdict as a fallback — the caller
    # can recover the claim text from the page title.
    verdict_only = None
    for block in blocks:
        try:
            data = json.loads(block.strip())
        except Exception:
            continue
        # Flatten top-level items AND items nested in "@graph" arrays —
        # Rappler (and other WordPress/Yoast sites) wrap everything in @graph.
        items = data if isinstance(data, list) else [data]
        flat  = []
        for item in items:
            if not isinstance(item, dict):
                continue
            flat.append(item)
            graph = item.get("@graph")
            if isinstance(graph, list):
                flat.extend(g for g in graph if isinstance(g, dict))
        for item in flat:
            # "@type" can be a string OR a list (e.g. ["Article", "ClaimReview"])
            itype = item.get("@type")
            types = itype if isinstance(itype, list) else [itype]
            if "ClaimReview" not in types:
                continue
            claim = (item.get("claimReviewed") or "").strip()
            rating = item.get("reviewRating", {}) or {}
            verdict = (rating.get("alternateName", "") or rating.get("ratingValue", ""))
            if isinstance(verdict, (int, float)): verdict = str(verdict)
            verdict = verdict.strip().lower()
            verdict_label = _verdict_to_label(verdict)
            if claim:
                return {"claim": claim, "verdict": verdict, "verdict_label": verdict_label}
            if verdict_only is None:
                # ClaimReview exists but claim (and possibly verdict) is
                # empty — return what we have; the caller recovers the
                # claim and/or verdict from the page title.
                verdict_only = {"claim": "", "verdict": verdict, "verdict_label": verdict_label}
    return verdict_only

def _extract_tsekph_verdict(html: str):
    if not html: return None
    from bs4 import BeautifulSoup
    sections = re.findall(r'"articleSection"\s*:\s*\[(.*?)\]', html)
    verdict = None
    verdict_label = -1
    for sec in sections:
        items = re.findall(r'"([^"]+)"', sec)
        for item in items:
            lbl = _verdict_to_label(item.lower())
            if lbl != -1:
                verdict = item.lower()
                verdict_label = lbl
                break
        if verdict: break
    if verdict is None: return None

    soup = BeautifulSoup(html, "html.parser")
    claim_text = None
    for tag in soup.find_all(["h2","h3","h4","p","div"]):
        t = tag.get_text(strip=True)
        if re.search(r'what was claimed', t, re.I) and len(t) < 50:
            nxt = tag.find_next_sibling()
            if nxt: claim_text = clean(nxt.get_text())
            break
    if not claim_text:
        h1 = soup.find("h1")
        if h1: claim_text = clean(h1.get_text())

    debunk_text = None
    content_div = soup.find("div", class_=re.compile(r"entry-content|post-content"))
    if content_div:
        paras = [clean(p.get_text()) for p in content_div.find_all("p") if len(clean(p.get_text())) > 30]
        if paras: debunk_text = " ".join(paras[:3])

    return {"verdict": verdict, "verdict_label": verdict_label, "claim": claim_text, "debunk": debunk_text}

def _extract_verafiles_claim_verdict(html: str):
    if not html: return None
    result = _extract_claimreview_jsonld(html)
    if result:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        debunk_text = None
        for tag in soup.find_all(["h2","h3","div"]):
            t = tag.get_text(strip=True)
            if re.search(r'our verdict', t, re.I) and len(t) < 30:
                nxt = tag.find_next_sibling()
                if nxt: debunk_text = clean(nxt.get_text())
                break
        result["debunk"] = debunk_text
        return result

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    claim_text = verdict_text = debunk_text = None
    for tag in soup.find_all(["h2","h3","div"]):
        t = tag.get_text(strip=True)
        if re.search(r'what was claimed', t, re.I) and len(t) < 50:
            nxt = tag.find_next_sibling()
            if nxt: claim_text = clean(nxt.get_text())
        if re.search(r'our verdict', t, re.I) and len(t) < 30:
            nxt = tag.find_next_sibling()
            if nxt:
                debunk_text = clean(nxt.get_text())
                verdict_text = debunk_text.split(":")[0].strip() if ":" in debunk_text else debunk_text[:30]
    if claim_text or debunk_text:
        vl = _verdict_to_label(verdict_text or "") if verdict_text else -1
        return {"claim": claim_text, "verdict": verdict_text, "verdict_label": vl, "debunk": debunk_text}
    return None

def _url_to_source(url: str) -> str:
    if "rappler.com" in url: return "Rappler FactCheck"
    if "tsek.ph" in url: return "Tsek.ph"
    if "verafiles.org" in url: return "Vera Files"
    return "Unknown"

def enrich_article_url(url: str, session=None, source: str = None) -> list:
    # `source` lets the caller override URL-based attribution — needed for
    # VERA Files, whose English and Filipino archives share the /articles/
    # path so the URL alone can't tell them apart. Defaults to _url_to_source.
    if not url or url == "#": return []
    html = _fetch_html(url, session)
    if not html: return []
    url_lower = url.lower()
    result = None
    if "rappler.com" in url_lower:
        result = _extract_claimreview_jsonld(html)
        if result: result["debunk"] = None
    elif "tsek.ph" in url_lower:
        result = _extract_tsekph_verdict(html)
    elif "verafiles.org" in url_lower:
        result = _extract_verafiles_claim_verdict(html)
        if not result:
            # Older VERA Files fact checks are prose-style — no ClaimReview,
            # no "What was claimed"/"Our verdict" sections. The headline
            # carries both claim and verdict, in one of two shapes:
            #   "VERA FILES FACT CHECK: <claim> untrue"     (prefix style)
            #   "<claim> needs context"                     (suffix style)
            # Anything without either marker (profiles, news, explainers
            # that the archive also lists) stays unextractable.
            m = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
            title = clean(m.group(1)).replace("​", "") if m else ""
            title = re.sub(r"\s*[-|–]\s*VERA Files\s*$", "", title, flags=re.IGNORECASE)
            m_pre = re.match(r"^\s*vera files fact check\s*[:\-–]\s*(.+)$", title, re.IGNORECASE)
            body  = m_pre.group(1).strip() if m_pre else title
            m_suf = re.search(
                r"[,:\s]\s*(not true|untrue|unproven|needs?(?: more)? context|false|"
                r"misleading|fake|(?:is )?(?:a )?satire|inaccurate|incorrect|no basis|"
                r"hindi totoo|walang basehan)\s*[.!]?\s*$",
                body, re.IGNORECASE)
            if m_pre or m_suf:
                # Verdict from the FULL title; claim text WITHOUT the verdict
                # wording so the label doesn't leak into the training text.
                label = detect_label(title)
                claim = body[:m_suf.start()].strip(" .,–-:") if m_suf else body
                if len(claim) > 15:
                    result = {"claim": claim, "verdict": "",
                              "verdict_label": label, "debunk": None}
            elif re.search(r"\b(NOT|NO|HINDI|WALANG|FALSE|UNTRUE|PEKE|MALI)\b", body) \
                    and body.upper() != body and len(body) > 15:
                # Third headline style: a bare correction statement with the
                # negation CAPITALIZED ("Pasalubong NOT prohibited in PH
                # airports", "HINDI nag-resign si BBM"). The headline itself
                # states the truth — store it as a REAL sample.
                result = {"claim": body, "verdict": "", "verdict_label": 0, "debunk": None}
    if not result: return []

    # Recover the claim from the page title when claimReviewed was empty —
    # fact-check headlines ARE the claim with a verdict prefix
    # ("FALSE: ABS-CBN got approval to go back on air").
    if not (result.get("claim") or "").strip():
        m = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
        title = clean(m.group(1)) if m else ""
        title = re.sub(r"\s*[-|–]\s*RAPPLER\s*$", "", title, flags=re.IGNORECASE)
        # A bare "CONTEXT:" prefix means missing-context (FAKE family) but the
        # word "context" alone is too common to put in the keyword lists —
        # detect it positionally here instead.
        if result.get("verdict_label", -1) == -1 and re.match(r"^\s*context\s*[:\-–]", title, re.IGNORECASE):
            result["verdict_label"] = 1
        # Strip the verdict prefix (longer phrases first) so the stored claim
        # doesn't leak its own label into the training text.
        title = re.sub(
            r"^\s*(kulang sa konteksto|manipuladong larawan|manipulated photo|"
            r"missing context|partly false|mostly false|fact check|indi matuod|"
            r"diri tinuod|dili tinuod|hindi totoo|misleading|no basis|altered|"
            r"context|false|fake|hoax|satire|true)\s*[:\-–]\s*",
            "", title, flags=re.IGNORECASE)
        if len(title) > 15:
            result["claim"] = title

    pairs = []
    now = datetime.now().isoformat()
    source = source or _url_to_source(url)
    verdict_label = result.get("verdict_label", -1)
    if verdict_label == -1:
        # No machine-readable rating (e.g. Rappler sometimes leaves the
        # JSON-LD alternateName empty). The page <title> usually carries
        # the verdict ("FALSE: ...", "MISLEADING: ...") — scan it first,
        # then the claim/debunk text.
        m = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
        page_title = clean(m.group(1)) if m else ""
        # Debunk-style headlines negate the claim ("FACT CHECK: No new pope
        # elected...", "No tsunami alert raised...") — when the article has
        # a ClaimReview, such a title means the stored claim is FAKE.
        if re.search(r"^\s*fact check\b.*\b(no|not|never|hindi|walang|resurfaces)\b",
                     page_title, re.IGNORECASE) or \
           re.match(r"^\s*(no|not|hindi|walang)\b", page_title, re.IGNORECASE):
            verdict_label = 1
        else:
            verdict_label = detect_label(
                page_title,
                (result.get("claim") or "") + " " + (result.get("debunk") or "")
            )

    claim = result.get("claim") or ""
    debunk = result.get("debunk") or ""
    if claim and len(claim) > 15:
        pairs.append({"text": claim, "label": verdict_label, "pair_type": "claim_article",
                      "source": source, "url": url, "hash": get_hash(claim), "collected_at": now})
    if debunk and len(debunk) > 15 and debunk != claim:
        pairs.append({"text": debunk, "label": 0, "pair_type": "debunk_article",
                      "source": source, "url": url, "hash": get_hash(debunk), "collected_at": now})
    return pairs

def extract_claim_debunk(title: str, summary: str, source: str, url: str = "") -> list:
    pairs = []
    combined = f"{title}. {summary}".strip()
    lower = combined.lower()
    claim_text = debunk_text = None

    for pat in CLAIM_PATTERNS:
        m = re.search(pat, lower)
        if m:
            start = m.end()
            chunk = combined[start:start+400]
            for dp in DEBUNK_PATTERNS:
                dm = re.search(dp, chunk.lower())
                if dm: chunk = chunk[:dm.start()]; break
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if len(chunk) > 25: claim_text = chunk; break

    for pat in DEBUNK_PATTERNS:
        m = re.search(pat, lower)
        if m:
            chunk = combined[m.start():m.start()+500]
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if len(chunk) > 25: debunk_text = chunk; break

    if claim_text: pairs.append({"text": claim_text, "label": 1, "pair_type": "claim"})
    if debunk_text: pairs.append({"text": debunk_text, "label": 0, "pair_type": "debunk"})

    if not pairs:
        title_c = clean(title)
        summ_c  = clean(summary)
        is_debunk_title = bool(re.search(
            r"fact check:.*\b(no|not|false|fake|misleading|fabricated|"
            r"altered|edited|manipulated|out of context|debunk)\b", title_c.lower()))
        if is_debunk_title:
            if len(summ_c) > 20: pairs.append({"text": summ_c,  "label": 1, "pair_type": "claim"})
            if len(title_c) > 20: pairs.append({"text": title_c, "label": 0, "pair_type": "debunk"})
        else:
            if len(title_c) > 20: pairs.append({"text": title_c, "label": detect_label(title_c), "pair_type": "title_as_claim"})
            if len(summ_c) > 20 and summ_c != title_c: pairs.append({"text": summ_c, "label": 0, "pair_type": "summary_as_debunk"})
        if not pairs and len(title_c) > 20:
            pairs.append({"text": title_c, "label": detect_label(title_c), "pair_type": "full_article"})

    now = datetime.now().isoformat()
    for p in pairs:
        p.update({"source": source, "url": url, "hash": get_hash(p["text"]), "collected_at": now})
    return pairs


def process_rss_entries(entries: list, source: str) -> list:
    all_pairs = []
    stats = {"claim": 0, "debunk": 0, "full": 0, "total": 0}
    for entry in entries:
        title = clean(entry.get("title", "")).strip()
        summary = clean(entry.get("summary", "")).strip()
        content_list = entry.get("content", [])
        content = clean(content_list[0].get("value", "") if content_list else "").strip()
        full_text = content if len(content) > len(summary) else summary
        if not title and not summary: continue
        stats["total"] += 1
        pairs = extract_claim_debunk(title, summary or full_text, source, entry.get("link", ""))
        for p in pairs:
            pt = p.get("pair_type", "")
            if "claim" in pt: stats["claim"] += 1
            elif "debunk" in pt: stats["debunk"] += 1
            else: stats["full"] += 1
        all_pairs.extend(pairs)
    logger.info(f"  {source}: {stats['total']} articles → {stats['claim']} claims + {stats['debunk']} debunks + {stats['full']} full")
    return all_pairs


def extract_articles_from_html(html: str, source: str, page_url: str) -> list:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    cards = (
        soup.find_all("article") or
        soup.find_all(class_=re.compile(r"post|card|entry|article|story|item|result", re.I))
    )
    if not cards: cards = soup.find_all(["h2","h3","h4"])
    seen_titles = set()
    for card in cards:
        title_el = (card.find(["h2","h3","h4"]) if card.name not in ["h2","h3","h4"] else card)
        if not title_el: continue
        title = clean(title_el.get_text())
        if len(title) < 10 or title in seen_titles: continue
        seen_titles.add(title)
        link_el = title_el.find("a") or card.find("a")
        url = link_el["href"] if link_el and link_el.get("href") else page_url
        summ_el = card.find("p") if card.name != "p" else None
        summary = clean(summ_el.get_text()) if summ_el else ""
        pairs = extract_claim_debunk(title, summary, source, url)
        for p in pairs: p["enrichment"] = "listing_page"
        articles.extend(pairs)
    return articles


def get_selenium_driver(headless: bool = True):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    opts = Options()
    if headless: opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"--user-agent={USER_AGENT}")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)
