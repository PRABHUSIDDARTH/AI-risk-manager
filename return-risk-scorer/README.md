# Return Risk Scorer 🎯
![Razorpay Buildathon](https://img.shields.io/badge/Razorpay-Buildathon-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![React](https://img.shields.io/badge/React-18-61dafb)

A real-time machine learning system to predict the likelihood of e-commerce returns (RTO - Return to Origin) and automatically recommend mitigating actions. Built with a FastAPI backend, a React frontend, and Google Gemini for dynamic explainability.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React + Vite Frontend (:3000)                 │
│  Dashboard │ Run Batch button │ Order table │ Detail modal        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP / NDJSON stream
┌─────────────────────▼───────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                         │
│  POST /api/score   → single order scoring                        │
│  POST /api/batch   → CSV batch (streaming NDJSON response)       │
│  GET  /api/orders  → paginated scored orders                     │
│  GET  /api/audit   → full audit log                              │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
   ┌───────▼──────┐          ┌────────▼────────┐
   │ sklearn GBC  │          │  Google Gemini  │
   │  model.pkl   │          │  1.5 Flash      │
   │  (risk score)│          │  (explanation + │
   └──────────────┘          │   action)       │
           │                 └─────────────────┘
   ┌───────▼──────┐
   │  SQLite DB   │
   │  orders      │
   │  predictions │
   │  actions     │
   │  audit_log   │
   └──────────────┘
```

## Features
- **Real-time Scoring**: Evaluate order risk on the fly via HTTP endpoints.
- **Batch Processing**: Stream CSV uploads containing multiple orders with real-time progress.
- **Explainable AI**: Google Gemini explains exactly *why* a particular risk score was given, making opaque ML models transparent.
- **Action Recommendations**: Automatically determines the best course of action (`allow`, `flag_for_verification`, `block_cod`) based on risk score bands.
- **Audit Logging**: Keeps a full history of all predictions, scores, and explanations for compliance.

## Setup — Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional for containerized setup)
- A Google Gemini API Key (Get one at [Google AI Studio](https://aistudio.google.com))

## Setup — Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd return-risk-scorer
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 2. Create Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
pip install scikit-learn pandas numpy joblib  # for data + ML scripts

# 3. Generate synthetic data
python data/generate_synthetic_data.py
# Output: data/orders.csv (5000 rows), data/train.csv (4000), data/test.csv (1000)

# 4. Train the model
python ml/train.py
# Output: ml/model.pkl, ml/model_version.txt

# 5. Evaluate on held-out test set
python ml/evaluate.py

# 6. Run backend
cd backend
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs

# 7. Run frontend (new terminal)
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

## Docker

```bash
# Make sure model is trained first (docker can't train)
python data/generate_synthetic_data.py
python ml/train.py

# Build and run everything
docker-compose up --build
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health + model status |
| POST | `/api/score` | Score a single order (JSON body) |
| POST | `/api/batch` | Score batch orders from CSV upload |
| GET | `/api/orders` | List all scored orders (paginated) |
| GET | `/api/orders/{id}` | Full order detail + audit entry |
| GET | `/api/audit` | Complete audit log |

## How to Reproduce Eval Numbers

```
Expected metrics (may vary slightly by run):
  ROC-AUC  : ~0.82
  F1 Score : ~0.72
  Precision: ~0.74
  Recall   : ~0.70

Reproduce:
  python data/generate_synthetic_data.py  # uses seed 42
  python ml/train.py
  python ml/evaluate.py
```

## Decision Logic

The system translates a continuous risk score (0.0 to 1.0) into discrete, actionable business decisions using configured thresholds:

- **`<0.35` — `allow`**: Green zone. Order proceeds normally.
- **`0.35-0.65` — `flag_for_verification`**: Amber zone. System requires additional manual or automated verification (e.g. OTP validation).
- **`>0.65` — `block_cod`**: Red zone. High probability of return. Cash on Delivery is disabled; requires prepaid.

## License
MIT License

