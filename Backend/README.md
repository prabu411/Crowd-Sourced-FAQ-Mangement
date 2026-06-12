# Crowd FAQs - Backend REST API & Database Engine

Welcome to the backend repository for the **Crowd FAQs** platform. This module contains the foundational database systems, REST API routing, dynamic voting score engines, and auto-clustering mock hooks.

It is designed as the core integration hub for the **Crowd FAQs development sprint**.

---

## 🏗️ Backend Architecture Overview
Developed specifically to satisfy the backend system requirements, this repository contains the database schema, data validation layers, REST API routes, and a premium visual testing hub.

### File Structure
```text
/Crowd FAQs
│
├── /backend
│   ├── __init__.py
│   ├── database.py         # SQLite tables, seeding, and dynamic priority scoring logic
│   ├── schemas.py          # Pydantic request/response payload validation
│   ├── clustering_mock.py  # Stage 2 NLP simulated clustering (Jaccard token matching)
│   └── main.py             # Main FastAPI routing and static mount settings
│
├── /static
│   ├── index.html          # Interactive REST Tester Dashboard
│   ├── styles.css          # Sleek dark-theme glassmorphism CSS
│   └── app.js              # State manager and async API fetch drivers
│
├── requirements.txt        # Backend dependencies
├── run.py                  # Single-command environment checker & startup script
├── test_backend.py         # Automated verification tests for QA verification
└── README.md               # You are here!
```

---

## 💾 1. Relational Database Schema (`database.py`)
The platform uses **SQLite** (`crowd_faqs.db`) with active foreign key checking (`PRAGMA foreign_keys = ON;`). 

### Relational Schema Diagram
```
  ┌───────────────┐          ┌───────────────┐
  │     USERS     │          │   CLUSTERS    │
  ├───────────────┤          ├───────────────┤
  │ id (PK)       │          │ id (PK)       │
  │ username      │◀┐        │ rep_question  │
  │ role          │ │        │ answer_text   │
  │ created_at    │ │        │ ai_draft_text │
  └───────────────┘ │        │ priority_score│
          ▲         │        │ created_at    │
          │         │        └───────────────┘
          │         │          ▲           ▲
          │         │          │           │
  ┌───────┴───────┐ │        ┌─┴─────────┐ │
  │   QUESTIONS   │ │        │   VOTES   │ │
  ├───────────────┤ │        ├───────────┤ │
  │ id (PK)       │ │        │ id (PK)   │ │
  │ question_text │ │        │ cluster_id│─┘
  │ category      │ │        │ user_id   │──┘
  │ cluster_id    │─┘        │ created_at│
  │ user_id       │          └───────────┘
  │ status        │
  │ created_at    │
  └───────────────┘
```

---

## 📈 2. Stage 3: Dynamic Upvote & Priority Logic
To prevent spam and surface the most important questions, a dynamic ranking algorithm runs on each new upvote:

$$\text{Priority Score} = (\text{Total Votes} \times 10.0) + \text{Category Weight} - (\text{Hours Elapsed since Cluster Creation} \times 0.1)$$

### Category Relevance Weights:
* 🔴 **Bug**: `+5.0`
* 🟣 **Feature Request**: `+3.0`
* 🔵 **Account**: `+2.0`
* ⚪ **General**: `+0.0`

---

## 📡 3. REST API Endpoints Specification

### Questions API

#### 1. Submit Question
* **`POST /api/questions`**
* **Payload**:
```json
{
  "question_text": "How can I reset my account password?",
  "category": "Account",
  "user_identifier": "dev_warish_user"
}
```
* **Behavior**: Passes question text to `clustering_mock.py`. If it matches an existing query with $\ge 35\%$ token overlap, it merges into the existing cluster (`status = 'pending'`). Otherwise, creates a new cluster and triggers an initial AI draft response.

#### 2. Get Grouped Questions Feed
* **`GET /api/questions`**
* **Query Parameters**:
  * `category` (optional) - Filter by tag.
  * `status` (optional) - Filter questions by status (`pending`, `approved`, `rejected`).
* **Response Payload (Array)**:
```json
[
  {
    "id": 1,
    "representative_question_id": 1,
    "representative_text": "How can I reset my forgotten account password?",
    "category": "Account",
    "answer_text": "To reset your password, click on the 'Forgot Password' link on the login page.",
    "ai_draft_text": "AI Draft: You can reset password by email.",
    "priority_score": 25.0,
    "created_at": "2026-05-29 12:00:00",
    "votes_count": 3,
    "questions": [
      {
        "id": 1,
        "question_text": "I forgot my password, how to reset it?",
        "category": "Account",
        "cluster_id": 1,
        "user_identifier": "user_1",
        "status": "approved",
        "created_at": "2026-05-29 12:00:00"
      }
    ]
  }
]
```

### Voting API

#### 1. Cast Upvote
* **`POST /api/votes`**
* **Payload**:
```json
{
  "cluster_id": 1,
  "user_identifier": "dev_warish_user"
}
```
* **Behavior**: Validates cluster existance, enforces unique voting per user, inserts vote, and recalculates the cluster priority score dynamically.

---

## 🤝 4. Developer Integration Guide (For Team Members)

### 🎨 For Frontend Devs (Ganeshprabu, Chaitanya, Ritzy)
* Host is `http://127.0.0.1:8000`. Full CORS is enabled for separate development servers.
* Use `POST /api/questions` to submit user inputs.
* Use `POST /api/votes` with the browser cookie or user profile ID as `user_identifier` to trigger real-time, animated ranking re-orders on the feed.

### 🧠 For AI/NLP Engineers (Tejeswara, Nekha)
* Open [clustering_mock.py](file:///c:/Users/mohdw/OneDrive/Desktop/Crowd%20FAQs/backend/clustering_mock.py).
* Replace `find_cluster_for_question()` with your **sentence-transformers / FAISS similarity search code**.
* Your algorithm can match questions against the representative question list using dense Cosine Similarity > `0.85`. No rest API structure changes are needed!

### 🤖 For AI Answers Engineers (Abhishek, Aryan)
* The `POST /api/questions` endpoint has a placeholder where `ai_draft_text` is created inside the new cluster branch. 
* Hook your LLM completion requests (Claude/GPT) directly there before database commit to populate realistic high-fidelity responses.

---

## ⚡ 5. Startup & Automated Verification

### QA Automated Verification
Verify the backend code, database constraints, Jaccard groupings, and scoring metrics:
```bash
python test_backend.py
```

### Running the Platform
To install required dependencies (FastAPI, Uvicorn, Pydantic) and boot up hot-reloading:
```bash
python run.py
```

* **Interactive testing console:** Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.
* **API Documentation Explorer:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
