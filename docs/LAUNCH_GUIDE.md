# 🚀 FakeNews-AI — Launch & Deployment Guide

> **Beginner edition** — every step explains *where* to type things and *what* they do.
> 100% free-tier resources. No credit card required for any phase.

---

## 🧱 Stack Overview

| Layer | Technology | Hosted on | Cost |
|---|---|---|---|
| **Frontend** | Next.js | Vercel | Free |
| **Backend** | FastAPI + models | Hugging Face Spaces *(or Render)* | Free |
| **Database** | PostgreSQL | Supabase | Free |
| **AI models** | BERT · RoBERTa · mBERT · LSTM · LogReg | Hugging Face Hub | Free |

> [!IMPORTANT]
> **The one big constraint — RAM.**
> Render's free tier gives **512 MB RAM**. Your three fine-tuned transformers are **~440 MB *each*** on disk (more in RAM) — they will **not** fit on Render free.
> **Hugging Face Spaces** free tier gives **16 GB RAM / 2 vCPU**, which fits all five models. That's why the backend goes to HF Spaces below.
> *(Render stays a fallback if you deploy **without** the transformers and rely on LSTM + LogReg + heuristic only.)*

---

## 📊 Project Status

| Phase | Status |
|---|---|
| **Phase 0** — Dataset, training, evaluation | ✅ **Complete** |
| Phase 1–7 — Deployment | ⏳ To do |

- **Dataset:** `combined_dataset.csv` → **80,257 samples** (36,174 fake / 44,083 real)
- **Models trained:** BERT · RoBERTa · Multilingual BERT · BiLSTM · Logistic Regression
- **Evaluation:** `ai_models/evaluation/results.json` present

---

## 📑 Table of Contents

- [🖥️ Run it locally first](#️-run-it-locally-first)
- [📖 The Basics (read once)](#-the-basics-read-once)
- [Phase 0 — Finish the models ✅](#phase-0--finish-the-models-)
- [Phase 1 — Prepare the repository](#phase-1--prepare-the-repository)
- [Phase 2 — Database on Supabase](#phase-2--database-on-supabase)
- [Phase 3 — Upload models to Hugging Face Hub](#phase-3--upload-models-to-hugging-face-hub)
- [Phase 4 — Backend on Hugging Face Spaces](#phase-4--backend-on-hugging-face-spaces)
- [Phase 5 — Frontend on Vercel](#phase-5--frontend-on-vercel)
- [Phase 6 — Keep free tiers awake + monitoring](#phase-6--keep-free-tiers-awake--monitoring)
- [Phase 7 — Post-launch](#phase-7--post-launch)
- [📋 Free-tier limits cheat sheet](#-free-tier-limits-cheat-sheet)
- [🗺️ Order of operations (TL;DR)](#️-order-of-operations-tldr)

---

## 🖥️ Run it locally first

Before deploying anywhere, confirm it runs on your machine. Open **two** terminals:

**Terminal 1 — Backend** (FastAPI → http://localhost:8000)
```powershell
cd "C:\C Codes (Projects)\fakenews-ai\backend"
venv\Scripts\activate
uvicorn main:app --reload
```

**Terminal 2 — Frontend** (Next.js → http://localhost:3000)
```powershell
cd "C:\C Codes (Projects)\fakenews-ai\frontend"
npm run dev
```

> [!TIP]
> Backend API docs (Swagger test page) live at **http://localhost:8000/docs** once the backend is running. Submit a test article there — the individual model scores (`bert_score`, etc.) should **differ** from each other. If they're all identical, the models didn't load and it fell back to the heuristic.

---

## 📖 The Basics (read once)

<details>
<summary><b>Click to expand — terminal, folders, git & file-editing gotchas</b></summary>

### What is "the terminal"?
A window where you type commands instead of clicking. On Windows you have Command Prompt (cmd), PowerShell, and Windows Terminal — any of them works here.

### Open a terminal *inside the project folder* (important!)
Almost every command must run while the terminal is "inside" the project root:
```
C:\C Codes (Projects)\fakenews-ai
```
*(Project root = the folder directly containing `backend/`, `frontend/`, `ai_models/`, `README.md`.)*

**Easiest ways:**
- **Option 1:** In File Explorer, right-click empty space inside the folder → **Open in Terminal**.
- **Option 2:** Click the File Explorer address bar, type `cmd`, press Enter.
- **Option 3:** In any terminal: `cd "C:\C Codes (Projects)\fakenews-ai"` *(quotes REQUIRED — the path has spaces)*.

**Check you're in the right place:** type `dir` — you should see `backend`, `frontend`, `ai_models`, `README.md`.

### One-time install checks
| Command | Expected output |
|---|---|
| `git --version` | `git version 2.x` |
| `python --version` | `Python 3.10` or newer |
| `node --version` | `v18` or newer |

If git is missing: install from https://git-scm.com/download/win (all defaults), then **close and reopen** the terminal.

### What is git / GitHub? (30 seconds)
- **git** = a program on your PC that tracks versions of your code.
- **GitHub** = a website storing a copy of your git-tracked code online. Vercel and Render deploy by reading your GitHub repo.

### Editing/creating text files (like `.gitignore`)
> [!WARNING]
> **Notepad gotcha:** Notepad may save `.gitignore` as `.gitignore.txt`, which git ignores (ironically). In the Save dialog set **Save as type: All Files (\*.\*)** and type the name exactly `.gitignore` — no `.txt`. Verify with `dir`: it must show `.gitignore`, not `.gitignore.txt`.

</details>

---

## Phase 0 — Finish the models ✅

> [!NOTE]
> **This phase is already complete** — all five models are trained and evaluated. The steps below are kept for **reproducibility and retraining**. All commands run from the project root.

### 0.1 — Build the dataset
Each collector writes its own raw CSV; only `prepare_dataset.py` merges them into `combined_dataset.csv`:

```bash
python ai_models/data/runner_download_foreign.py   # once — WELFake + ISOT → datasets_foreign.csv
python ai_models/data/runner_scraper.py            # once, slow — Selenium PH fact-check → datasets_scraped_ph_factcheck.csv
python ai_models/data/runner_rss.py                # daily/optional — PH real-news RSS → datasets_rss_ph_real_news.csv
python ai_models/data/clean_scraped.py             # after scraping — removes junk rows (keeps backup + audit)
python ai_models/data/prepare_dataset.py           # ALWAYS run last — merges all raw CSVs → combined_dataset.csv
```

Verify the dataset has **both** labels:
```bash
python -c "import pandas as pd; print(pd.read_csv('ai_models/data/combined_dataset.csv')['label'].value_counts())"
```
You want counts next to both `0` (real) and `1` (fake) — ideally no worse than a ~70/30 split.

> [!TIP]
> **Current status:** ✅ `combined_dataset.csv` = **80,257 samples** (36,174 fake / 44,083 real) — a healthy ~45/55 balance.

### 0.2 — Train (order = fastest first)
Each command trains one model into its `ai_models/<name>/saved_model/` folder:

```bash
python ai_models/training/train_logistic.py
python ai_models/training/train_lstm.py
python ai_models/training/train_transformers.py all   # slow — hours, uses your GPU
python ai_models/evaluation/evaluate_models.py
```

### 0.3 — Check the ensemble beats every single model
Open `ai_models/evaluation/results.json` — the **ensemble** accuracy should beat every individual model. Keep this file; it goes in your thesis and README.

---

## Phase 1 — Prepare the repository

*All commands in a terminal at the project root.*

### 1.1 — Turn the folder into a git repo
```bash
git init
git branch -M main
```
This creates a hidden `.git` folder and names your main line of work `main`. Nothing is uploaded yet.

**First time using git ever?** Tell git who you are (once, ever):
```bash
git config --global user.name "Your Name"
git config --global user.email "gwproacc@gmail.com"
```

### 1.2 — Create `.gitignore`
Create a file named `.gitignore` in the project root *(see Basics for the Notepad gotcha)*. Paste exactly:

```gitignore
.env
backend/venv/
frontend/node_modules/
frontend/.next/
__pycache__/
*.pyc
backend/uploads/
ai_models/*/saved_model/
ai_models/data/*.csv
logs/
```

| Entry | Why it's ignored |
|---|---|
| `.env` | Contains passwords / secret keys |
| `venv`, `node_modules`, `.next` | Giant auto-generated folders — rebuildable, don't belong online |
| `saved_model`, `*.csv` | GitHub blocks files > 100 MB. ISOT CSVs (60 + 52 MB) and transformers would break the upload — models go to HF Hub (Phase 3) |

### 1.3 — Double-check `.env` is ignored **before** uploading
```bash
git check-ignore .env
```
> [!CAUTION]
> If it prints `.env` → good, it's ignored. If it prints **nothing** → **STOP**, your `.gitignore` isn't being read (probably the `.txt` problem). If `.env` ever gets uploaded, **rotate** the `SECRET_KEY`, SMTP password, and admin password immediately.

### 1.4 — Create the GitHub repo and push
1. Go to https://github.com → sign up (free) if needed.
2. Click **+** (top right) → **New repository**. Name: `fakenews-ai`. **Public.** Do **NOT** tick "Add a README". Click **Create**.
3. In your terminal at project root, run one at a time (replace `<your-username>`):
   ```bash
   git add .
   git commit -m "Initial public release"
   git remote add origin https://github.com/<your-username>/fakenews-ai.git
   git push -u origin main
   ```
   | Command | What it does |
   |---|---|
   | `git add .` | Stage every (non-ignored) file |
   | `git commit` | Save a version snapshot on your PC |
   | `git remote add origin` | Tell git where your GitHub repo lives |
   | `git push` | Upload the snapshot to GitHub |
4. Refresh your repo page — your code should be there. **Confirm `.env` and the `ai_models` CSVs are NOT there.**

---

## Phase 2 — Database on Supabase

*Free tier: 500 MB — plenty. This phase is all website clicking, no terminal.*

1. **2.1** Sign up at https://supabase.com (use **Continue with GitHub**).
2. **2.2** New project → pick a region close to your users (**Singapore** for PH). It asks for a database password — **SAVE IT** somewhere safe (you can't see it again).
3. **2.3** Left sidebar → **SQL Editor**. Open `database/schema.sql` from your project, copy ALL of it, paste, click **Run**. `Success. No rows returned` = it worked.
4. **2.4** Get the connection string: **Project Settings (gear)** → **Database** → **Connection string** → **URI**.
   > [!IMPORTANT]
   > Pick the **"Session pooler"** option (port **5432**) — the direct connection is IPv6-only and fails from many hosts.
   ```
   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
   Replace `<password>` with the one from 2.2. Save the full string — you'll paste it in Phase 4.4.
5. **2.5** ⚠️ Free-tier gotcha: Supabase **pauses** projects after ~1 week with no traffic. Fixed in Phase 6.

---

## Phase 3 — Upload models to Hugging Face Hub

> **Hugging Face Hub = "GitHub for AI models"** — no file-size limit, so this is where your big model files live.

### 3.1 — Get a write token
Create an account at https://huggingface.co → avatar → **Settings** → **Access Tokens** → **New token** → type **WRITE** → create. Copy it (starts with `hf_`).

### 3.2 — Log in (terminal at project root)
```bash
pip install huggingface_hub
huggingface-cli login
```
> [!NOTE]
> Pasted tokens are **invisible** in the terminal — that's a security feature. Paste and press Enter.

### 3.3 — Upload each model
Replace `<you>` with your HF username. Run one at a time (~440 MB each for transformers):

```bash
# Transformers (one repo each)
huggingface-cli repo create fakenews-bert
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/bert/saved_model', repo_id='<you>/fakenews-bert')"

huggingface-cli repo create fakenews-roberta
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/roberta/saved_model', repo_id='<you>/fakenews-roberta')"

huggingface-cli repo create fakenews-bert-multilingual
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/bert_multilingual/saved_model', repo_id='<you>/fakenews-bert-multilingual')"

# LSTM + LogReg are small — share one repo
huggingface-cli repo create fakenews-small-models
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/lstm/saved_model', repo_id='<you>/fakenews-small-models', path_in_repo='lstm')"
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/logistic_regression/saved_model', repo_id='<you>/fakenews-small-models', path_in_repo='logistic_regression')"
```

> [!TIP]
> Public model repos are free and fine for a thesis. Private repos are also free — the Space in Phase 4 then needs your HF token to download them.

---

## Phase 4 — Backend on Hugging Face Spaces

> A **"Space"** = a small free server on Hugging Face that runs your code (16 GB RAM, 2 vCPU). Under the hood it's just another git repo that auto-runs itself.

### 4.1 — Create the Space
On huggingface.co: **+ New** → **Space**. Name: `fakenews-api`. SDK: **Docker** → **Blank**. Hardware: **CPU basic** (free). Create.

### 4.2 — Copy your backend into it
In a terminal (your Documents folder is fine — **NOT** inside `fakenews-ai`):
```bash
git clone https://huggingface.co/spaces/<you>/fakenews-api
```
Copy everything from your project's `backend/` folder (**except `venv/`**) into the new `fakenews-api` folder. Edit its `Dockerfile` so the last line listens on port **7860** (Spaces requires it):
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 4.3 — Make the Space download models on boot
Add near the top of `main.py` (before the model paths are used), with `<you>` replaced:
```python
from huggingface_hub import snapshot_download
snapshot_download("<you>/fakenews-bert",              local_dir="ai_models/bert/saved_model")
snapshot_download("<you>/fakenews-roberta",           local_dir="ai_models/roberta/saved_model")
snapshot_download("<you>/fakenews-bert-multilingual", local_dir="ai_models/bert_multilingual/saved_model")
snapshot_download("<you>/fakenews-small-models",      local_dir="ai_models")
```

### 4.4 — Set the secrets
On the Space's page: **Settings** → **Variables and secrets** → add each as a **SECRET**:

| Name | Value |
|---|---|
| `DATABASE_URL` | The Supabase pooler URI from step 2.4 |
| `SECRET_KEY` | A long random string → `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALLOWED_ORIGINS` | `https://<your-app>.vercel.app` *(from Phase 5 — come back after 5.4)* |
| `BERT_WEIGHT` | `0.30` |
| `ROBERTA_WEIGHT` | `0.25` |
| `BERT_MULTILINGUAL_WEIGHT` | `0.20` |
| `LSTM_WEIGHT` | `0.15` |
| `LOGISTIC_WEIGHT` | `0.10` |

*(Plus `SMTP_*`, `ADMIN_*`, `NEWS_API_KEY`, etc. — copy values from your local `.env`.)*

### 4.5 — Push the Space code (terminal inside `fakenews-api`)
```bash
git add .
git commit -m "FastAPI backend"
git push
```
The Space shows **Building...** — wait. When it says **Running**, open:
```
https://<you>-fakenews-api.hf.space/docs
```
You should see the Swagger page. Try a prediction — the individual model scores should **differ**. If all identical, the models didn't load (check the **Logs** tab).

### 4.6 — ⚠️ Free-tier gotcha
Spaces **sleep** after ~48 h idle; the first request after sleeping takes **1–3 min**. Phase 6 fixes this.

> [!NOTE]
> **Alternative (skip transformers):** Render free tier can host LSTM + LogReg + heuristic only, using the `render.yaml` already in the repo. Set the two transformer weights to `0` and re-balance the rest.

---

## Phase 5 — Frontend on Vercel

*Free Hobby tier. All website clicking, no terminal.*

1. **5.1** Sign up at https://vercel.com → **Continue with GitHub**.
2. **5.2** **Add New...** → **Project** → import your `fakenews-ai` repo.
   > [!IMPORTANT]
   > **CRITICAL SETTING:** "Root Directory" → **Edit** → select **`frontend`** (your Next.js app lives in the subfolder, not the repo root). Framework should auto-detect as Next.js.
3. **5.3** Expand **Environment Variables** and add:
   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<you>-fakenews-api.hf.space` |
   | `NEXT_PUBLIC_APP_NAME` | `FakeNewsAI` |
   | `NEXT_PUBLIC_APP_URL` | `https://<your-app>.vercel.app` |
4. **5.4** Click **Deploy**. After ~2 min you get your live URL. From now on, every `git push` auto-redeploys.
5. **5.5** Go **back** to the HF Space (4.4) and set `ALLOWED_ORIGINS` to exactly this Vercel URL — https, no trailing slash:
   ```
   https://fakenews-ai.vercel.app
   ```
   > [!CAUTION]
   > If this doesn't match **exactly**, every browser request fails with a **CORS** error (visible in the browser's F12 console).

---

## Phase 6 — Keep free tiers awake + monitoring

*All free.*

- **6.1 — UptimeRobot** (https://uptimerobot.com — visits your URLs every few minutes, emails if down):
  - **Monitor 1:** HTTP(s) → `https://<you>-fakenews-api.hf.space/` every **5 min** → keeps the Space awake **and** alerts you.
  - **Monitor 2:** your Vercel URL (never sleeps; alerts only).
- **6.2 — Supabase anti-pause:** something must touch the **database** at least weekly. Easiest: point Monitor 1 at a backend endpoint doing a tiny DB read (a `/health` route running `SELECT 1`). If missing, add it (~5 lines in `main.py`).
- **6.3 — Full end-to-end test FROM A PHONE** (not your dev PC — proves it works for the public): open the Vercel site → submit an article → get an ensemble verdict with individual scores → confirm the row appeared in Supabase (**Table Editor**).

---

## Phase 7 — Post-launch

- **7.1 — Retraining:** `retrain_pipeline.py` needs your local GPU, so run it on your PC when **≥ 50** verified feedback rows accumulate, then re-upload models (repeat 3.3 — same commands overwrite). Restart the Space (**Settings → Restart Space**) to download the fresh models.
- **7.2 — Rate limiting:** you have `RATE_LIMIT_PER_MINUTE` in `.env` — verify it's actually enforced before sharing publicly, or one bored user can eat your whole free CPU quota.
- **7.3 — Custom domain (optional, the only paid thing):** a `.com` is ~$10/yr; Vercel and HF Spaces both support custom domains on free plans. The `vercel.app` URL is perfectly fine for a thesis.
- **7.4 — Update the README:** put the live URL + the `results.json` metrics table in the root README, then `git add README.md && git commit -m "Add live demo" && git push` (Vercel redeploys automatically).

---

## 📋 Free-tier limits cheat sheet

| Service | Limits |
|---|---|
| **Vercel Hobby** | 100 GB bandwidth/mo, no sleep. Non-commercial only. |
| **HF Spaces** | 16 GB RAM, 2 vCPU, sleeps after ~48 h idle, cold start 1–3 min. Public. |
| **Supabase free** | 500 MB DB, 2 projects, pauses after ~1 wk inactivity. |
| **UptimeRobot** | 50 monitors, 5-min interval. |
| **GitHub free** | Unlimited public repos, 100 MB per-file hard limit. |
| **HF Hub** | Free unlimited public model/dataset storage. |

---

## 🗺️ Order of operations (TL;DR)

```
fix dataset → train → evaluate → git init + push (no models/CSVs/.env)
→ Supabase (schema + pooler URI) → models to HF Hub → backend to HF Space
→ frontend to Vercel → wire CORS both ways → UptimeRobot pings → test on phone → share
```

> [!TIP]
> **Stuck?** Copy the exact error message + the step number into Claude Code and ask. Most deploy failures are:
> 1. Wrong folder in the terminal
> 2. A typo in an env var name
> 3. `ALLOWED_ORIGINS` not matching the Vercel URL exactly
