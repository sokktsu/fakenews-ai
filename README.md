# COMBATING FAKE NEWS WITH AI
## Natural Language Processing and Deep Learning

> A full-stack thesis project featuring BERT, LSTM, Logistic Regression ensemble model for fake news detection.

---

## 🏗️ Project Structure

```
fakenews-ai/
├── frontend/          # Next.js + TailwindCSS + Framer Motion
├── backend/           # FastAPI + Python AI pipeline
├── ai_models/         # BERT, LSTM, LogReg, Ensemble
├── database/          # Schema + migrations
├── docker/            # Docker configuration
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Tesseract OCR

### 1. Clone & Setup Environment

```bash
git clone <your-repo>
cd fakenews-ai
cp .env.example .env
# Fill in your environment variables
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 4. Database Setup

```bash
# PostgreSQL
psql -U postgres -c "CREATE DATABASE fakenews_db;"
psql -U postgres -d fakenews_db -f database/schema.sql
```

---

## 🌐 Deployment

### Frontend → Vercel
```bash
cd frontend
npx vercel --prod
```

### Backend → Render / Railway
- Connect GitHub repo
- Set environment variables
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Database → Supabase / Neon
- Create project at supabase.com
- Run `database/schema.sql` in SQL editor
- Copy connection string to `DATABASE_URL`

---

## 🤖 AI Models

### Ensemble Scoring
```
final_score = (BERT × 0.30) + (RoBERTa × 0.25) + (Multilingual BERT × 0.20)
            + (LSTM × 0.15) + (LogReg × 0.10)
```

### Training
```bash
cd ai_models
python training/train_transformers.py all   # BERT + RoBERTa + Multilingual BERT
python training/train_lstm.py
python training/train_logistic.py
```

### Evaluation
```bash
python evaluation/evaluate_models.py
```

---

## 🔑 Environment Variables

See `.env.example` for all required variables.

---

## 📚 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, Framer Motion |
| Backend | FastAPI, Python 3.10 |
| Database | PostgreSQL / Supabase |
| AI/NLP | HuggingFace, TensorFlow, PyTorch, scikit-learn |
| OCR | Tesseract, EasyOCR |
| Auth | JWT (jose) |
| Deployment | Vercel + Render + Supabase |

---

## 👥 Team

Update `frontend/src/app/team/page.tsx` with your team information.

---

## 📄 License

Thesis Project — All Rights Reserved
