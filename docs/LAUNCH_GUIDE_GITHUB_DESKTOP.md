# 🚀 FakeNews-AI — Launch & Deployment Guide (GitHub Desktop Edition)

> **Beginner edition** — every git/GitHub step is done through the **GitHub Desktop app** (buttons, not terminal commands).
> 100% free-tier resources. No credit card required for any phase.
>
> 📄 Prefer typing commands? See the terminal version: [`LAUNCH_GUIDE.md`](LAUNCH_GUIDE.md).

---

## 🧱 Stack Overview

| Layer | Technology | Hosted on | Cost |
|---|---|---|---|
| **Frontend** | Next.js | Vercel | Free |
| **Backend** | FastAPI + models | Hugging Face Spaces *(or Render)* | Free |
| **Database** | PostgreSQL | Supabase | Free |
| **AI models** | BERT · RoBERTa · mBERT · LSTM · LogReg | Hugging Face Hub | Free |

> [!IMPORTANT]
> **The one big constraint — RAM.** Render's free tier gives **512 MB RAM**; your three transformers are **~440 MB *each*** — they will **not** fit. **Hugging Face Spaces** free tier gives **16 GB RAM / 2 vCPU**, which fits all five models. That's why the backend goes to HF Spaces.

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

## 🛠️ Before you start — install GitHub Desktop

1. Download from <https://desktop.github.com> → install with defaults.
2. Open it → **File → Options → Accounts → Sign in** with your GitHub account (`gwproacc@gmail.com`).
3. Under **Options → Git**, set **Name** = your GitHub username, **Email** = your GitHub email.

---

## 📑 Table of Contents

- [🖥️ Run it locally first](#️-run-it-locally-first)
- [Phase 0 — Finish the models ✅](#phase-0--finish-the-models-)
- [Phase 1 — Clean-slate reset & publish (GitHub Desktop)](#phase-1--clean-slate-reset--publish-github-desktop)
- [Phase 2 — Database on Supabase](#phase-2--database-on-supabase)
- [Phase 3 — Upload models to Hugging Face Hub](#phase-3--upload-models-to-hugging-face-hub)
- [Phase 4 — Backend on Hugging Face Spaces](#phase-4--backend-on-hugging-face-spaces)
- [Phase 5 — Frontend on Vercel](#phase-5--frontend-on-vercel)
- [Phase 6 — Keep free tiers awake + monitoring](#phase-6--keep-free-tiers-awake--monitoring)
- [Phase 7 — Post-launch (pushing updates)](#phase-7--post-launch-pushing-updates)
- [📋 Free-tier limits cheat sheet](#-free-tier-limits-cheat-sheet)

---

## 🖥️ Run it locally first

Open **two** terminals:

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
> Backend API docs live at **http://localhost:8000/docs**. Submit a test article — the individual model scores (`bert_score`, etc.) should **differ**. If identical, models didn't load and it fell back to the heuristic.

---

## Phase 0 — Finish the models ✅

> [!NOTE]
> **Already complete** — all five models trained and evaluated. Steps kept for reproducibility/retraining. Run from the project root in a terminal.

### 0.1 — Build the dataset
```bash
python ai_models/data/runner_download_foreign.py   # once — WELFake + ISOT → datasets_foreign.csv
python ai_models/data/runner_scraper.py            # once, slow — Selenium PH fact-check
python ai_models/data/runner_rss.py                # daily/optional — PH real-news RSS
python ai_models/data/clean_scraped.py             # after scraping — removes junk rows
python ai_models/data/prepare_dataset.py           # ALWAYS run last — merges → combined_dataset.csv
```

Verify the dataset has **both** labels:
```bash
python -c "import pandas as pd; print(pd.read_csv('ai_models/data/combined_dataset.csv')['label'].value_counts())"
```
You want counts next to both `0` (real) and `1` (fake) — ideally no worse than a ~70/30 split.

> [!TIP]
> **Current status:** ✅ `combined_dataset.csv` = **80,257 samples** (36,174 fake / 44,083 real) — a healthy ~45/55 balance.

### 0.2 — Train (fastest first)
```bash
python ai_models/training/train_logistic.py
python ai_models/training/train_lstm.py
python ai_models/training/train_transformers.py all   # slow — hours, uses your GPU
python ai_models/evaluation/evaluate_models.py
```

### 0.3 — Check the ensemble
Open `ai_models/evaluation/results.json` — the **ensemble** accuracy should beat every individual model.

---

## Phase 1 — Clean-slate reset & publish (GitHub Desktop)

Use this when you want a **fresh git history** — no trace of earlier messy commits (e.g. the nested-repo mistake). It wipes the old history and republishes a clean single "Initial commit."

> [!WARNING]
> This **erases local git history**. Your **files are NOT deleted** — only the hidden `.git` history folder is. Make sure your latest work is saved first. (You already keep a backup — good.)

### 1.1 — Delete the OLD GitHub repo (website)
1. Go to `https://github.com/sokktsu/fakenews-ai`.
2. **Settings** tab → scroll to the red **Danger Zone**.
3. **Delete this repository** → type `sokktsu/fakenews-ai` to confirm → enter password/2FA.
4. The online repo is now gone. *(Your PC files are untouched.)*

### 1.2 — Confirm `.gitignore` exists (protects secrets)
In the project root, confirm a `.gitignore` file is present. It must contain at least:
```gitignore
.env
.env.*
!.env.example
backend/venv/
__pycache__/
*.pyc
backend/uploads/
frontend/node_modules/
frontend/.next/
frontend/next-env.d.ts
ai_models/*/saved_model/
ai_models/data/*.csv
ai_models/data/**/*.csv
logs/
*.log
.DS_Store
Thumbs.db
```
> [!CAUTION]
> If `.gitignore` is missing, **STOP and recreate it first** — otherwise the next commit could upload your `.env` secrets and 100+ MB of CSVs.

### 1.3 — Delete the local `.git` folder (File Explorer)
GitHub Desktop can't delete history, so do it manually:
1. Open the project folder in **File Explorer**: `C:\C Codes (Projects)\fakenews-ai`.
2. **View → Show → Hidden items** (so the `.git` folder becomes visible).
3. Delete the folder named **`.git`** (just that one folder — nothing else).

*(This removes all old commits and the old GitHub link. Your code stays.)*

### 1.4 — Remove the broken repo from GitHub Desktop
GitHub Desktop still lists the old repo. In the app:
- Right-click the repo in the top-left list → **Remove** → confirm.
  *(This only removes it from the app's list; it doesn't delete files.)*

### 1.5 — Re-add the folder as a brand-new repo
1. **File → Add local repository** → **Choose…** → select `C:\C Codes (Projects)\fakenews-ai`.
2. It will say *"This directory does not appear to be a Git repository"* → click **create a repository**.
3. On the create screen: **Name** `fakenews-ai`, leave **Git ignore** = None and **License** = None (you already have your own `.gitignore`). Click **Create repository**.

> [!NOTE]
> This does a clean `git init` **in place** — a fresh history with zero old commits.

### 1.6 — Safety check BEFORE committing
In the **Changes** tab (left), scan the file list. These must **NOT** appear:

| Must NOT appear | Why |
|---|---|
| `.env` · `backend/.env` · `frontend/.env.local` | Real secrets |
| `ai_models/data/**/*.csv` (incl. `isot/Fake.csv`, `True.csv`) | Large, rebuildable data |
| any `saved_model/` files | ~440 MB each — go to HF Hub |
| `__pycache__/`, `.pyc` | Generated cache |

✅ `.env.example` **should** appear — it's a safe template.

### 1.7 — Commit
Bottom-left: **Summary** = `Initial commit` → **Commit to main**.

### 1.8 — Publish to GitHub
1. **Publish repository** (top bar).
2. **Name:** `fakenews-ai`.
3. **Uncheck** ✅ *"Keep this code private"* → make it **Public**.
4. **Publish repository** — creates the GitHub repo + uploads in one step.

### 1.9 — Verify online
Open `https://github.com/sokktsu/fakenews-ai` → confirm code is there, and **no `.env`, no CSVs, no `saved_model/`**. History shows a single clean `Initial commit`. ✅

---

## Phase 2 — Database on Supabase

*Free tier: 500 MB. All website clicking.*

1. **2.1** Sign up at <https://supabase.com> (**Continue with GitHub**).
2. **2.2** New project → region **Singapore** (PH). Save the DB password (you can't see it again).
3. **2.3** **SQL Editor** → paste all of `database/schema.sql` → **Run**. `Success. No rows returned` = worked.
4. **2.4** **Project Settings → Database → Connection string → URI**.
   > [!IMPORTANT]
   > Pick **"Session pooler"** (port **5432**) — the direct connection is IPv6-only and fails from many hosts.
   ```
   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
   Save it for Phase 4.4.
5. **2.5** ⚠️ Supabase **pauses** projects after ~1 week idle. Fixed in Phase 6.

---

## Phase 3 — Upload models to Hugging Face Hub

> **Hugging Face Hub = "GitHub for AI models"** — no file-size limit. (GitHub Desktop is not involved; models don't go to GitHub.)

### 3.1 — Get a write token
<https://huggingface.co> → avatar → **Settings → Access Tokens → New token** → **WRITE** → copy (`hf_...`).

### 3.2 — Log in (terminal)
```bash
pip install huggingface_hub
huggingface-cli login
```

### 3.3 — Upload each model (replace `<you>`)
> [!TIP]
> `ignore_patterns=['checkpoint-*']` skips the training snapshots — they're useless for inference and **double** your upload size.

```bash
huggingface-cli repo create fakenews-bert
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/bert/saved_model', repo_id='<you>/fakenews-bert', ignore_patterns=['checkpoint-*'])"

huggingface-cli repo create fakenews-roberta
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/roberta/saved_model', repo_id='<you>/fakenews-roberta', ignore_patterns=['checkpoint-*'])"

huggingface-cli repo create fakenews-bert-multilingual
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/bert_multilingual/saved_model', repo_id='<you>/fakenews-bert-multilingual', ignore_patterns=['checkpoint-*'])"

huggingface-cli repo create fakenews-small-models
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/lstm/saved_model', repo_id='<you>/fakenews-small-models', path_in_repo='lstm')"
python -c "from huggingface_hub import upload_folder; upload_folder(folder_path='ai_models/logistic_regression/saved_model', repo_id='<you>/fakenews-small-models', path_in_repo='logistic_regression')"
```

---

## Phase 4 — Backend on Hugging Face Spaces

> A **"Space"** = a small free server (16 GB RAM, 2 vCPU) that runs your backend. It's its own git repo, separate from GitHub.

### 4.1 — Create the Space
huggingface.co → **+ New → Space**. Name: `fakenews-api`. SDK: **Docker → Blank**. Hardware: **CPU basic** (free). Create.

### 4.2 — Clone the Space & copy your backend in
```bash
git clone https://huggingface.co/spaces/<you>/fakenews-api
```
Copy everything from `backend/` (**except `venv/`**) into the cloned `fakenews-api` folder. Edit its `Dockerfile` last line to port **7860**:
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```
> [!TIP]
> **Using GitHub Desktop for the Space too:** **Add local repository** → pick the cloned `fakenews-api` folder. It already has an HF remote, so commit and **Push origin** to send it to Hugging Face. Do **not** click "Publish" (that targets GitHub).

### 4.3 — Make the Space download models on boot
Add near the top of `main.py` (before model paths are used), `<you>` replaced:
```python
from huggingface_hub import snapshot_download
snapshot_download("<you>/fakenews-bert",              local_dir="ai_models/bert/saved_model")
snapshot_download("<you>/fakenews-roberta",           local_dir="ai_models/roberta/saved_model")
snapshot_download("<you>/fakenews-bert-multilingual", local_dir="ai_models/bert_multilingual/saved_model")
snapshot_download("<you>/fakenews-small-models",      local_dir="ai_models")
```

### 4.4 — Set the secrets
Space page → **Settings → Variables and secrets** → add each as a **SECRET**:

| Name | Value |
|---|---|
| `DATABASE_URL` | Supabase pooler URI from 2.4 |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALLOWED_ORIGINS` | `https://<your-app>.vercel.app` *(come back after 5.4)* |
| `BERT_WEIGHT` | `0.30` |
| `ROBERTA_WEIGHT` | `0.25` |
| `BERT_MULTILINGUAL_WEIGHT` | `0.20` |
| `LSTM_WEIGHT` | `0.15` |
| `LOGISTIC_WEIGHT` | `0.10` |

*(Plus `SMTP_*`, `ADMIN_*`, `NEWS_API_KEY`, etc. — copy from your local `.env`.)*

### 4.5 — Push the Space
Commit + **Push origin** in GitHub Desktop. Wait for **Building… → Running**, then open:
```
https://<you>-fakenews-api.hf.space/docs
```
Try a prediction — scores should **differ**. If identical, models didn't load (check **Logs**).

### 4.6 — ⚠️ Free-tier gotcha
Spaces **sleep** after ~48 h idle; first request after sleeping takes **1–3 min**. Phase 6 fixes this.

---

## Phase 5 — Frontend on Vercel

*Free Hobby tier. All website clicking.*

1. **5.1** Sign up at <https://vercel.com> → **Continue with GitHub**.
2. **5.2** **Add New… → Project** → import `fakenews-ai`.
   > [!IMPORTANT]
   > **CRITICAL:** "Root Directory" → **Edit** → select **`frontend`**. Framework auto-detects as Next.js.
3. **5.3** Expand **Environment Variables**:
   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<you>-fakenews-api.hf.space` |
   | `NEXT_PUBLIC_APP_NAME` | `FakeNewsAI` |
   | `NEXT_PUBLIC_APP_URL` | `https://<your-app>.vercel.app` |
4. **5.4** **Deploy**. After ~2 min you get your live URL. Every future push auto-redeploys.
5. **5.5** Back in the HF Space (4.4), set `ALLOWED_ORIGINS` to exactly your Vercel URL — https, no trailing slash:
   ```
   https://fakenews-ai.vercel.app
   ```
   > [!CAUTION]
   > If it doesn't match **exactly**, every browser request fails with a **CORS** error.

---

## Phase 6 — Keep free tiers awake + monitoring

- **6.1 — UptimeRobot** (<https://uptimerobot.com>):
  - **Monitor 1:** HTTP(s) → `https://<you>-fakenews-api.hf.space/` every **5 min** → keeps the Space awake + alerts.
  - **Monitor 2:** your Vercel URL (alerts only).
- **6.2 — Supabase anti-pause:** point Monitor 1 at a `/health` route running `SELECT 1`. If missing, add it (~5 lines in `main.py`).
- **6.3 — End-to-end test FROM A PHONE:** open the Vercel site → submit an article → get an ensemble verdict → confirm the row appears in Supabase (**Table Editor**).

---

## Phase 7 — Post-launch (pushing updates)

Every future change is the same simple loop:

> ✏️ **Edit files** → **GitHub Desktop** → review **Changes** → **Summary** → **Commit to main** → **Push origin**.

Vercel auto-redeploys the frontend on every push.

- **7.1 — Retraining:** run `retrain_pipeline.py` (needs local GPU) when **≥ 50** verified feedback rows accumulate, then re-upload models (repeat 3.3). Restart the Space (**Settings → Restart Space**).
- **7.2 — Rate limiting:** verify `RATE_LIMIT_PER_MINUTE` is enforced before sharing publicly.
- **7.3 — Custom domain (optional, the only paid thing):** a `.com` is ~$10/yr. The `vercel.app` URL is fine for a thesis.
- **7.4 — Update the README:** add live URL + `results.json` metrics, then **commit + Push origin**.

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
train + evaluate (done) → clean-slate reset (delete old GitHub repo + local .git)
→ GitHub Desktop: create repo → commit → Publish (public)
→ Supabase (schema + pooler URI) → models to HF Hub → backend to HF Space
→ frontend to Vercel → wire CORS both ways → UptimeRobot pings → test on phone → share
```

> [!TIP]
> **Stuck?** Most failures are: (1) wrong folder, (2) a typo in an env var name, (3) `ALLOWED_ORIGINS` not matching the Vercel URL exactly, or (4) forgetting to delete the local `.git` before re-creating (leaves old history).
