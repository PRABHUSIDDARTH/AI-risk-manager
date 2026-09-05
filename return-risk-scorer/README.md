# Return Risk Scorer — AI-Powered E-Commerce Risk Console

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%205-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%201.4-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)

An enterprise-grade, real-time risk intelligence console for e-commerce merchant platforms. Evaluates the probability of return/refund abuse and Return-to-Origin (RTO) across orders, delivers plain-language causal reasoning via Google Gemini, executes policy-bounded risk mitigation actions, and records an immutable audit log for financial compliance.

---

## Table of Contents

- [Executive Overview](#executive-overview)
- [System Architecture](#system-architecture)
- [Key Engineering Highlights](#key-engineering-highlights)
  - [1. Cost-Sensitive Risk Optimization](#1-cost-sensitive-risk-optimization)
  - [2. Dual-Engine Inference (Deterministic ML + LLM Reasoning)](#2-dual-engine-inference-deterministic-ml--llm-reasoning)
  - [3. Streaming NDJSON Batch Engine](#3-streaming-ndjson-batch-engine)
  - [4. Immutable Relational Audit Trail](#4-immutable-relational-audit-trail)
  - [5. Ledger Console UX Design System](#5-ledger-console-ux-design-system)
- [ML Pipeline & Feature Engineering](#ml-pipeline--feature-engineering)
- [API Specification & Wire Contracts](#api-specification--wire-contracts)
- [Environment Configuration](#environment-configuration)
- [Quick Start Guide](#quick-start-guide)
  - [Local Development](#local-development)
  - [Docker & Containerized Deployment](#docker--containerized-deployment)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Repository Structure](#repository-structure)
- [Production Hardening & Compliance](#production-hardening--compliance)
- [License](#license)

---

## Executive Overview

Return-to-Origin (RTO) and fraudulent return abuse inflict devastating margin erosion on e-commerce merchants—particularly in Cash-on-Delivery (COD) heavy emerging markets:
- Reverse logistics and repackaging consume **15–30% of average gross transaction value**.
- Indiscriminate COD restrictions introduce checkout friction that destroys conversion for legitimate buyers.
- Opaque machine-learning scoring leaves operations teams unable to explain or defend merchant risk decisions.

**Return Risk Scorer** solves this by uniting high-speed gradient boosted decision trees, LLM-driven causal explanations, automated policy enforcement, and a trading-desk-inspired operations terminal:

| Risk Zone | Score Range | Default Policy Action | Business Impact |
|:---|:---:|:---|:---|
| **Low Risk** | `< 0.35` | `allow` | Order cleared for automated fulfillment with zero checkout friction |
| **Medium Risk** | `0.35 – 0.65` | `flag_for_verification` | Held for automated WhatsApp/SMS confirmation or manual operator review |
| **High Risk** | `> 0.65` | `block_cod` | Cash on Delivery disabled; customer offered prepaid or EMI checkout |

---

## System Architecture

```
                                  CLIENT TIER
                 ┌──────────────────────────────────────────────┐
                 │          React 18 + Vite SPA (:5173 / :3000) │
                 │      "Ledger Console" UI (IBM Plex Typography)│
                 │  - Inline Batch Controller   - Order Detail Modal│
                 │  - Streaming Ledger Table    - Real-Time Progress│
                 └──────────────────────┬───────────────────────┘
                                        │ HTTP / NDJSON Stream
                                        ▼
                                 GATEWAY / BACKEND
                 ┌──────────────────────────────────────────────┐
                 │             FastAPI Backend (:8000)          │
                 │  - Async ASGI Server (Uvicorn)               │
                 │  - CORS Middleware & Strict Pydantic v2      │
                 │  - Streaming NDJSON Generator                │
                 └───────┬──────────────────────┬───────────────┘
                         │                      │
       PREDICTION TIER   │                      │   EXPLAINABILITY TIER
 ┌───────────────────────▼────────┐   ┌─────────▼────────────────────────┐
 │  Scikit-Learn GBC Pipeline     │   │   Google Gemini                  │
 │  - Preprocessor (OneHot/Scale) │   │   - Structured JSON Reasoning    │
 │  - GradientBoostingClassifier  │   │   - Causal Feature Attribution   │
 │  - LRU-Cached Thread-Safe Load │   │   - Deterministic Fallback Engine│
 └───────────────┬────────────────┘   └─────────┬────────────────────────┘
                 │ Risk Score (0-1)             │ Explanation & Action
                 └───────────────┬──────────────┘
                                 ▼
                         PERSISTENCE & AUDIT
 ┌───────────────────────────────────────────────────────────────────────┐
 │                SQLAlchemy Relational Engine (SQLite / Postgres)       │
 │                                                                       │
 │   ┌──────────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────┐   │
 │   │    orders    │   │ predictions  │   │ actions  │   │audit_log │   │
 │   └──────────────┘   └──────────────┘   └──────────┘   └──────────┘   │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## Key Engineering Highlights

### 1. Cost-Sensitive Risk Optimization

Standard binary accuracy or F1-scores ignore the asymmetric financial cost of classification errors. In real operations:
- **False Positive (FP)**: Legitimate order flagged or blocked COD $\rightarrow$ friction cost $\approx \$2.00$.
- **False Negative (FN)**: Fraudulent/abusive return allowed $\rightarrow$ reverse transit + restock cost $\approx \$15.00$.

The evaluation engine calculates expected business loss across probability thresholds:

$$\text{Loss}(T) = \text{FP}(T) \times \$2.00 + \text{FN}(T) \times \$15.00$$

Evaluating against held-out test distributions demonstrates that **threshold $0.30$** achieves the global cost minimum ($2,237 vs $3,595 at standard 0.50), significantly protecting merchant cash flow.

### 2. Dual-Engine Inference (Deterministic ML + LLM Reasoning)

1. **Deterministic ML**: Scikit-Learn `GradientBoostingClassifier` calculates calibrated class probabilities in $<5\text{ms}$.
2. **Context-Aware Explanation**: Outputs are passed to Google Gemini with full order telemetry, requesting strict JSON responses isolating the driving features.
3. **Resilient Failover**: If `GEMINI_API_KEY` is not provided or network timeouts occur, the service switches to a deterministic heuristic engine without latency degradation, preserving 100% uptime.

### 3. Streaming NDJSON Batch Engine

Batch operations stream line-delimited JSON (`application/x-ndjson`) over standard HTTP:
- Allows operations teams to submit CSV files with thousands of records without server timeouts.
- Incremental yields enable the React frontend to display live progress and render rows as they finish inference, maintaining a flat memory profile on both client and server.

### 4. Immutable Relational Audit Trail

Every scoring event performs an atomic write across normalized SQLAlchemy entities:
- `Order`: Captures raw snapshot of features at order timestamp.
- `Prediction`: Model identifier, version string (`gbc-v1`), and computed probability.
- `Action`: Policy decision executed (`allow`, `flag_for_verification`, `block_cod`).
- `AuditLog`: Serialized feature payload, model version, timestamp, explanation, and action for compliance and dispute verification.

### 5. Ledger Console UX Design System

A UI designed specifically for financial and risk operators:
- **Zero Decorative Fluff**: No card shadows, gradients, or non-functional animations.
- **Strict Color Tokens**: Ink (`#12151C`), Paper (`#F7F6F3`), Slate (`#5B6472`), Ledger Blue (`#2B4C7E`), Allow Green (`#3F6B4C`), Flag Amber (`#B8792A`), Block Red (`#A83232`).
- **Tabular Numbers**: IBM Plex Mono across all IDs, currencies, percentages, and timestamps for scanning integrity.
- **Top-to-Bottom Stagger**: 35ms row ledger entry transition on batch ingestion.

---

## ML Pipeline & Feature Engineering

The feature vector captures customer history, catalog classification, logistics lead time, and checkout timing:

| Feature Name | Type | Processing | Description |
|:---|:---:|:---:|:---|
| `order_value` | Numeric | `StandardScaler` | Order gross total in INR (clipped 50–10,000) |
| `num_items` | Numeric | `StandardScaler` | Total quantity of line items (1–15) |
| `category` | Categorical | `OneHotEncoder` | `electronics`, `apparel`, `footwear`, `books`, `home`, `beauty` |
| `payment_method` | Categorical | `OneHotEncoder` | `cod` (Cash on Delivery), `prepaid`, `emi` |
| `customer_return_rate` | Numeric | `StandardScaler` | Historical return frequency of customer ($0.0 - 1.0$) |
| `days_to_deliver` | Numeric | `StandardScaler` | Estimated logistics window in days |
| `seller_rating` | Numeric | `StandardScaler` | Seller performance score ($1.0 - 5.0$) |
| `is_first_order` | Boolean | `Passthrough` | Binary indicator for first-time customer |
| `discount_pct` | Numeric | `StandardScaler` | Promotion discount proportion ($0.0 - 1.0$) |
| `pincode_return_rate` | Numeric | `StandardScaler` | Destination pincode historic return rate ($0.0 - 1.0$) |
| `hour_of_order` | Numeric | `StandardScaler` | Checkout hour in local time ($0 - 23$) |
| `device_type` | Categorical | `OneHotEncoder` | Client interface (`mobile`, `desktop`, `app`) |

### Top Predictive Features (GBC Feature Importances)

```text
customer_return_rate   ████████████████  15.6%
pincode_return_rate    ██████████████    14.1%
discount_pct           █████████████     12.6%
order_value            ████████████      12.1%
seller_rating          ███████████       10.9%
payment_method_cod     █████████          8.7%
hour_of_order          █████              5.2%
num_items              █████              5.0%
```

---

## API Specification & Wire Contracts

Base URLs:
- Backend: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 1. Health & Model Diagnostics
```http
GET /health
```
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": "gbc-v1"
}
```

### 2. Real-Time Single Order Scoring
```http
POST /api/score
Content-Type: application/json
```
**Request Body:**
```json
{
  "order_id": "ORD-98412",
  "order_value": 7500.0,
  "num_items": 3,
  "category": "electronics",
  "payment_method": "cod",
  "customer_return_rate": 0.65,
  "days_to_deliver": 9,
  "seller_rating": 3.1,
  "is_first_order": true,
  "discount_pct": 0.45,
  "pincode_return_rate": 0.52,
  "hour_of_order": 23,
  "device_type": "mobile"
}
```
**Response Body (200 OK):**
```json
{
  "order_id": "ORD-98412",
  "score": 0.9142,
  "action": "block_cod",
  "explanation": "This order has a 91.4% return probability, driven by: cash-on-delivery payment, high customer return history (65%), large discount (45%). These combined signals elevate the return risk.",
  "audit_id": 481,
  "model_version": "gbc-v1"
}
```

### 3. Streaming Batch Upload
```http
POST /api/batch
Content-Type: multipart/form-data
```
**Streamed Response (`application/x-ndjson`):**
```ndjson
{"order_id": "ORD-001", "score": 0.1241, "action": "allow", "explanation": "Low return risk. No significant risk factors.", "audit_id": 482, "model_version": "gbc-v1", "order_value": 350.0, "category": "books", "payment_method": "prepaid"}
{"order_id": "ORD-002", "score": 0.5218, "action": "flag_for_verification", "explanation": "Primary signal is cash-on-delivery payment.", "audit_id": 483, "model_version": "gbc-v1", "order_value": 1420.0, "category": "apparel", "payment_method": "cod"}
{"_summary": true, "total": 2, "allow_count": 1, "flag_count": 1, "block_count": 0, "avg_score": 0.3230}
```

### 4. Query Scored Orders
```http
GET /api/orders?page=1&limit=50
```
Returns chronological paginated orders including audit ID, score, and operational summary.

### 5. Single Order Audit Query
```http
GET /api/orders/{order_id}
```
Returns full feature payload snapshot, timestamp, model version, and exact reasoning logged at transaction time.

---

## Environment Configuration

Copy the example environment configuration:
```bash
cp return-risk-scorer/.env.example return-risk-scorer/.env
```

| Variable | Type | Default | Description |
|:---|:---:|:---|:---|
| `GEMINI_API_KEY` | `string` | `""` | Google AI Studio API key. If empty, triggers deterministic fallback |
| `MODEL_PATH` | `string` | `../ml/model.pkl` | Path to serialized Scikit-Learn pipeline |
| `MODEL_VERSION_PATH` | `string` | `../ml/model_version.txt` | Path to active model version identifier |
| `DATABASE_URL` | `string` | `sqlite:///./return_risk.db` | SQLAlchemy database connection URI |
| `SCORE_THRESHOLD_ALLOW` | `float` | `0.35` | Scores below this boundary execute `allow` |
| `SCORE_THRESHOLD_BLOCK` | `float` | `0.65` | Scores above this boundary execute `block_cod` |
| `DEBUG` | `bool` | `false` | Enable verbose ASGI server debug output |

---

## Quick Start Guide

### Local Development

#### 1. Setup Python Environment
```bash
cd return-risk-scorer

# Create and activate virtual environment (Bash/Zsh)
python3 -m venv .venv
source .venv/bin/activate

# Or in Fish shell:
# source .venv/bin/activate.fish

# Install production and development dependencies
pip install -r backend/requirements.txt
```

#### 2. Generate Synthetic Training Data & Train ML Pipeline
```bash
# Generate 5,000 synthetic orders with realistic e-commerce signal
python data/generate_synthetic_data.py

# Train GradientBoostingClassifier with 5-fold CV and save pipeline artifact
cd ml
python train.py

# Run held-out evaluation & cost matrix analysis
python evaluate.py
cd ..
```

#### 3. Start Backend API Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API runs at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

#### 4. Launch React Frontend
In a new terminal:
```bash
cd return-risk-scorer/frontend
npm install
npm run dev
```
Console runs at `http://localhost:5173`.

---

### Docker & Containerized Deployment

A production-ready `docker-compose.yml` orchestrates the multi-service architecture:

```bash
cd return-risk-scorer

# Ensure model is trained first
python data/generate_synthetic_data.py
python ml/train.py

# Launch containers
docker-compose up --build
```

- **Frontend Console**: `http://localhost:3000` (Reverse-proxied via Nginx)
- **Backend API**: `http://localhost:8000`
- **Health Endpoint**: `http://localhost:8000/health`

---

## Testing & Quality Assurance

Run the automated test suite using `pytest`:

```bash
cd return-risk-scorer
.venv/bin/python -m pytest backend/tests/ -v
```

The test harness covers:
- System health diagnostic checks (`GET /health`)
- Single-order valid schema scoring (`POST /api/score`)
- Pydantic field-level boundary and validation rejection (`422 Unprocessable Entity`)
- In-memory CSV streaming batch verification (`POST /api/batch`)

---

## Repository Structure

```text
return-risk-scorer/
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git tracking exemptions (venv, models, DBs)
├── Dockerfile.backend            # Python 3.11-slim production container
├── Dockerfile.frontend           # Multi-stage Node builder + Nginx Alpine host
├── docker-compose.yml            # Multi-container orchestration specification
│
├── data/
│   └── generate_synthetic_data.py# 5000-row synthetic e-commerce data generator
│
├── ml/
│   ├── features.py               # ColumnTransformer feature preprocessing pipeline
│   ├── train.py                  # Model training pipeline & 5-fold Stratified CV
│   └── evaluate.py               # Held-out testing & threshold loss estimation
│
├── backend/
│   ├── requirements.txt          # Production backend dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic-settings configuration loader
│   │   ├── main.py               # FastAPI application definition & CORS
│   │   ├── models/
│   │   │   ├── db.py             # SQLAlchemy engine & session dependency
│   │   │   ├── orm.py            # Order, Prediction, Action, AuditLog tables
│   │   │   └── schemas.py        # Pydantic v2 validation contracts
│   │   ├── services/
│   │   │   ├── scorer.py         # Thread-safe cached inference service
│   │   │   ├── gemini.py         # Google Gemini LLM explainability & fallback
│   │   │   └── audit.py          # Relational atomic audit logger
│   │   └── routers/
│   │       ├── score.py          # POST /api/score endpoint
│   │       ├── batch.py          # POST /api/batch NDJSON streaming endpoint
│   │       └── orders.py         # GET /api/orders & /api/audit endpoints
│   └── tests/
│       └── test_score.py         # Automated test cases
│
└── frontend/
    ├── package.json              # React 18 & Vite dependency manifest
    ├── vite.config.js            # Vite bundler configuration & /api proxy
    ├── tailwind.config.js        # Tailored theme tokens (risk colors, fonts)
    ├── nginx.conf                # Production SPA routing & unbuffered proxying
    └── src/
        ├── main.jsx              # DOM root mount
        ├── App.jsx               # Main operations console layout
        ├── index.css             # IBM Plex typography & color token CSS vars
        ├── api/
        │   └── client.js         # Axios client & NDJSON chunked stream parser
        └── components/
            ├── BatchRunner.jsx   # Inline CSV dropzone & streaming controller
            ├── OrderTable.jsx    # High-density ledger table with stagger animation
            ├── OrderDetailModal.jsx# Full-depth audit inspection modal
            └── ScoreBadge.jsx    # Compact risk category tag
```

---

## Production Hardening & Compliance

- **Zero Data Leakage**: Training data splits use strict stratification; test datasets (`data/test.csv`) are isolated exclusively for evaluation.
- **Fail-Safe Inference**: Failure or latency spikes from external LLM providers automatically trigger deterministic rule evaluation, ensuring zero checkout downtime.
- **Stateless Scoring**: Inference does not rely on transient server session memory; models are pre-warmed using LRU cache mechanisms.
- **Audit Immutability**: All decisions, input vectors, and outputs are written with UTC timestamps to persistent relational storage for historical review and dispute resolution.

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 PRABHUSIDDARTH AV. All rights reserved.
