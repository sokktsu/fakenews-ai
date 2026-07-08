# AI Models Directory

## Structure

```
ai_models/
├── bert/
│   └── saved_model/        ← BERT fine-tuned model outputs here after training
├── roberta/
│   └── saved_model/        ← RoBERTa fine-tuned model outputs here after training
├── bert_multilingual/
│   └── saved_model/        ← Multilingual BERT fine-tuned model outputs here after training
├── lstm/
│   └── saved_model/        ← LSTM model + tokenizer.pkl outputs here
├── logistic_regression/
│   └── saved_model/        ← model.joblib + tfidf.joblib outputs here
├── data/
│   └── combined_dataset.csv ← Place your dataset here (text, label columns)
├── training/
│   ├── train_transformers.py  ← BERT / RoBERTa / Multilingual BERT (pass model key or "all")
│   ├── train_lstm.py
│   ├── train_logistic.py
│   └── retrain_pipeline.py
└── evaluation/
    └── evaluate_models.py
```

## Dataset Format

Your `data/combined_dataset.csv` should have:
```
text,label
"Article text here...",1
"Another article...",0
```

Where `1 = FAKE` and `0 = REAL`.

## Recommended Datasets (Free)

- **LIAR Dataset**: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip
- **FakeNewsNet**: https://github.com/KaiDMML/FakeNewsNet
- **WELFake**: https://zenodo.org/record/4561253
- **ISOT Fake News**: https://onlineacademiccommunity.uvic.ca/isot/

## Training Order

```bash
# 1. Fastest — train first
python ai_models/training/train_logistic.py

# 2. Medium — requires GPU for speed
python ai_models/training/train_lstm.py

# 3. Slowest — GPU strongly recommended (bert | roberta | multilingual | all)
python ai_models/training/train_transformers.py all

# 4. Evaluate all models
python ai_models/evaluation/evaluate_models.py
```

## Without Trained Models

The system will fall back to a keyword-based heuristic scorer if no trained
model files are found. This allows the API to function for demos and testing
without requiring training.
