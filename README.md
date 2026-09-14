# HintCode — AI-Powered Coding Platform

A full-stack competitive coding platform with an intelligent hint system, real code execution, community features, and analytics. Built with **Django + React**.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Django 5, Django REST Framework |
| Database | Supabase (PostgreSQL) |
| Auth | Clerk |
| Code Execution | Piston API (multi-language) |
| AI / Hints | OpenRouter API (LLM-backed) |
| Editor | Monaco Editor |

---

## Features

- 🧩 **1000+ Problems** across Arrays, Trees, Graphs, DP and more — organized by topic and difficulty
- 💡 **AI Hint System** — tiered, context-aware hints powered by an LLM; hints get progressively more detailed
- ▶️ **Live Code Execution** — run code in Python, JavaScript, C++, Java and 20+ languages via Piston
- 📋 **Problem Sheets** — curated lists (NeetCode 150, Top Interview, etc.)
- 📅 **Daily Problem** — a new problem released every day; solving it extends your streak 🔥
- 🏆 **Global Leaderboard** — ranked by score (Easy +10, Medium +25, Hard +50 pts)
- 💬 **Community Forum** — post questions and discuss problems per-problem or globally
- 📊 **User Dashboard** — solve rate, topic mastery, streak heatmap, score
- 🔧 **Admin Dashboard** — platform-wide analytics, popular problems, solve rates
- 🌙 **Dark / Light mode** — theme persisted per-user

---

## Project Structure

```
Coding_Platform/
├── backend/                    # Django backend
│   ├── hint_system/            # Django project settings & URLs
│   ├── hints/                  # Main app
│   │   ├── models.py           # All models (Problem, Attempt, Forum, Leaderboard…)
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # Hint generation views
│   │   ├── code_views.py       # Code run / submit / history
│   │   ├── analytics_views.py  # User & admin dashboards
│   │   ├── social_views.py     # Forum, Solutions, Leaderboard
│   │   ├── daily_views.py      # Problem of the Day
│   │   ├── sheet_views.py      # Problem sheets
│   │   ├── rag_service.py      # RAG-based hint retrieval
│   │   ├── execution_service.py# Piston API wrapper
│   │   └── management/         # Django management commands
│   │       └── commands/
│   │           ├── generate_daily_problem.py
│   │           └── seed_sheets.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .env                    # ← copy from .env.example
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx             # Routes
│   │   ├── components/
│   │   │   └── Navbar.jsx
│   │   ├── pages/
│   │   │   ├── TopicsHome.jsx          # Landing / topic browser
│   │   │   ├── ProblemList.jsx         # Full problem list with filters
│   │   │   ├── ProblemDetail.jsx       # Editor + hints + discuss tabs
│   │   │   ├── ProblemSheets.jsx       # Sheet listing
│   │   │   ├── SheetDetail.jsx         # Problems inside a sheet
│   │   │   ├── Leaderboard.jsx         # Global rankings
│   │   │   ├── Forum.jsx               # Community forum
│   │   │   ├── Solutions.jsx           # Community solutions for a problem
│   │   │   ├── UserAnalyticsDashboard.jsx
│   │   │   └── AdminDashboard.jsx
│   │   ├── services/
│   │   │   ├── apiClient.js    # Fetch wrapper with Clerk JWT auth
│   │   │   ├── problemService.js
│   │   │   ├── hintService.js
│   │   │   └── codeService.js
│   │   └── styles.css
│   ├── package.json
│   └── .env                    # ← copy from root .env.example
│
├── docs/                       # Reference docs (architecture, older notes)
├── .env.example                # Template for all required env vars
├── docker-compose.yml          # Redis for caching (optional)
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)
- A [Clerk](https://clerk.com) app (free tier works)
- An [OpenRouter](https://openrouter.ai) API key (for hints)

---

### 1. Clone & set up environment

```bash
git clone https://github.com/KMohnishM/Coding_Platform.git
cd Coding_Platform
```

**Backend `.env`** — copy and fill in:
```bash
cp .env.example backend/.env
```

Required variables:
```env
DATABASE_URL=postgresql://postgres.<ref>:<password>@<host>:6543/postgres
OPENROUTER_API_KEY=sk-or-...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

> ⚠️ If your Supabase password contains `@`, encode it as `%40` in the URL.

**Frontend `.env`** — create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

---

### 2. Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at **http://localhost:8000**

---

### 3. Load problems (first time only)

```bash
# From backend/ directory
python load_jsonl_problems.py   # loads problems from curated_problems_1k.jsonl
python manage.py seed_sheets    # creates default problem sheets
python manage.py generate_daily_problem  # sets today's daily problem
```

---

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## API Overview

All endpoints are prefixed with `/api/`.

| Prefix | Description |
|---|---|
| `/api/problems/` | Problem listing and detail |
| `/api/hints/` | Hint request / auto-trigger |
| `/api/code/run/` | Run code (Piston) |
| `/api/code/submit/` | Submit + grade + award score |
| `/api/code/history/` | Past submissions for a problem |
| `/api/daily/today/` | Today's problem of the day |
| `/api/sheets/` | Problem sheets |
| `/api/leaderboard/global_rankings/` | Top 100 users by score |
| `/api/forums/` | Forum posts (CRUD + upvote + comment) |
| `/api/solutions/` | Community solutions |
| `/api/analytics/user_dashboard/` | Authenticated user stats |
| `/api/analytics/admin_dashboard/` | Platform-wide stats |

Authentication: all endpoints (except `/api/problems/` and `/api/daily/`) require a **Clerk JWT** sent as `Authorization: Bearer <token>`.

---

## Scoring

| Difficulty | Points on first solve |
|---|---|
| Easy | +10 |
| Medium | +25 |
| Hard | +50 |

Points are awarded **once per problem**. Solving the Daily Problem extends your 🔥 streak.

---

## Useful Commands

```bash
# Run migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Create a superuser for Django admin
python manage.py createsuperuser

# Regenerate today's daily problem
python manage.py generate_daily_problem

# Re-seed sheets
python manage.py seed_sheets
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit with clear messages: `git commit -m "feat: add X"`
4. Push and open a Pull Request

Please keep PRs focused — one feature / fix per PR.

---

## Docs

Detailed reference docs live in [`/docs`](./docs/):

- [`BACKEND_INTERNALS.md`](./docs/BACKEND_INTERNALS.md) — Django app internals
- [`JSONL_LOADER_README.md`](./docs/JSONL_LOADER_README.md) — Problem loader script
- [`PLATFORM_STRUCTURE.md`](./docs/PLATFORM_STRUCTURE.md) — Architecture overview
- [`IMPLEMENTATION_SUMMARY.md`](./docs/IMPLEMENTATION_SUMMARY.md) — Feature implementation log

---

## License

MIT
