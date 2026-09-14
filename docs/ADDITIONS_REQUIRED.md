# 🚀 HintCode Platform — Additions & Improvements Required

> Last updated: 2026-06-06
> Status: Development / Pre-production

---

## 🔴 Critical / Must-Have

### 1. Authentication — Replace Mock with Real Auth
**Current state:** `auth_views.py` generates random user IDs and mock tokens. No password hashing, no sessions, no JWT.

- [ ] Implement proper user registration with password hashing (bcrypt/argon2)
- [ ] Add JWT-based authentication (django-rest-framework-simplejwt)
- [ ] Add token refresh mechanism
- [ ] Protect all API endpoints with authentication middleware
- [ ] Add OAuth2 support (Google, GitHub login)
- [ ] Frontend: persist JWT in httpOnly cookies (not localStorage)
- [ ] Add email verification flow
- [ ] Add password reset / forgot password

### 2. Database & User Progress Tracking
**Current state:** `UserProgress` model exists but isn't wired up. Submissions are only stored in localStorage.

- [ ] Wire up `UserProgress` model to track per-problem attempts, completion, and hints used
- [ ] Create a `history` API endpoint to fetch user attempts from the DB
- [ ] Connect the frontend History tab to fetch past submissions via the new API instead of `localStorage`
- [ ] Add user profile page showing stats, heatmap, streak
- [ ] Add a proper "Solved" marker per problem in the problem lists
- [ ] Sync solved status from backend instead of localStorage

### 3. Code Execution Engine — Hardening
**Current state:** `execution_service.py` uses local subprocess fallback + Piston API.

- [ ] Set up a dedicated Piston instance or use Judge0 for production
- [ ] Add sandboxing / container isolation for local execution (never run untrusted code on host)
- [ ] Add execution time limits and memory limits per language
- [ ] Add rate limiting on code run/submit endpoints (prevent abuse)
- [ ] Support `stdin` input properly for all languages
- [ ] Add support for custom test cases (user-provided input/output)

---

## 🟡 High Priority — Feature Completeness

### 4. Problem Management
**Current state:** Problems loaded from DB via `loadProblems` management command. Only array-category problems exist.

- [ ] Add problems across ALL topics (Strings, Trees, Graphs, DP, Greedy, etc.)
- [ ] Add difficulty distribution balance (easy/medium/hard per topic)
- [ ] Admin panel to create/edit/delete problems (Django admin or custom)
- [ ] Add problem tags/categories (multiple tags per problem)
- [ ] Add editorial/solution tab per problem
- [ ] Add "Companies" tag (like LeetCode's company tags)
- [ ] Support for multiple problem formats (standard I/O, function-based, class-based)

### 5. Test Cases
**Current state:** Test cases are auto-extracted from problem description markdown. No custom test case input.

- [ ] Store test cases as structured data in the database (separate `TestCase` model)
- [ ] Let users add/edit custom test cases in the Console panel
- [ ] Show hidden vs visible test cases (visible for Run, all for Submit)
- [ ] Add test case generation scripts per problem

### 6. Hints System — AI Integration
**Current state:** `hint_chain.py` and `rag_service.py` exist but need API keys and vector store setup.

- [ ] Set up OpenAI / Gemini API key for hint generation
- [ ] Set up vector store (ChromaDB/Pinecone) for RAG-based hint retrieval
- [ ] Wire up progressive hint levels (conceptual → approach → implementation → debug)
- [ ] Add hint rate limiting (prevent hint spam)
- [ ] Track hint usage per user per problem for analytics

---

## 🟢 Medium Priority — Polish & UX

### 7. Frontend UI Enhancements
- [x] Add keyboard shortcuts (Ctrl+Enter to Run, Ctrl+Shift+Enter to Submit)
- [ ] Add a "Reset Code" confirmation modal
- [ ] Add code auto-save (debounced save to localStorage per problem+language)
- [ ] Add fullscreen mode for the editor
- [ ] Add split-pane memory (remember left panel width + console height in localStorage)
- [ ] Add problem navigation (Previous/Next problem arrows in workspace header)
- [ ] Add a "Discuss" tab on the left panel
- [x] Loading skeleton states for problem list / topic cards (instead of spinner)
- [ ] Add toast/notification system for success/error feedback
- [ ] Responsive mobile layout for problem detail (stacked panels)

### 8. Problem List & Discovery
- [ ] Add search functionality (search by problem title, ID, tags)
- [ ] Add pagination or infinite scroll for the problem list
- [ ] Add sorting (by difficulty, acceptance rate, frequency)
- [ ] Add filters (by status: solved/unsolved/attempted)
- [ ] Add a daily challenge / problem of the day feature
- [x] Add difficulty-based progress rings per topic card

### 9. Console / Output Panel
- [x] Add "Custom Input" tab — let users type their own stdin
- [ ] Add "Clear Console" button
- [x] Add colored diff for expected vs actual output
- [x] Add copy-to-clipboard for output
- [x] Syntax-highlight error messages (compilation errors)
- [ ] Show memory usage alongside runtime

### 10. Editor Improvements
- [ ] Add Vim/Emacs keybinding modes
- [ ] Add code templates per language per problem (smarter boilerplate)
- [ ] Add a "Format Code" button (auto-format)
- [ ] Add line count and character count in the status bar
- [x] Add editor font size slider

---

## 🔵 Low Priority — Nice to Have

### 11. Social & Competitive Features
- [ ] Global leaderboard
- [ ] User profiles (public profile with solve stats)
- [ ] Contests / weekly challenges
- [ ] Discussion forum per problem
- [ ] Solution sharing (post your solution after solving)
- [ ] Friends list / follow system

### 12. Analytics & Insights
- [ ] Admin dashboard — problem solve rates, error rates, popular problems
- [ ] User dashboard — personal stats, weak areas, improvement suggestions
- [ ] Problem difficulty calibration (auto-adjust based on solve rates)
- [ ] Time-to-solve analytics per problem

### 13. Infrastructure & DevOps
- [ ] Docker Compose setup for the full stack (frontend + backend + DB + Redis + Piston)
- [ ] CI/CD pipeline (GitHub Actions for lint, test, deploy)
- [ ] Production deployment guide (Nginx, Gunicorn, SSL)
- [ ] Database migrations strategy and backup plan
- [ ] Monitoring and logging (Sentry for errors, structured logging)
- [ ] CDN for static assets
- [ ] Environment-based config (.env files for dev/staging/prod)

### 14. Performance & Caching
- [ ] Redis caching is partially set up — expand to cache user progress, leaderboard
- [ ] Add database query optimization (select_related, prefetch_related)
- [ ] Lazy load Monaco editor (code split)
- [ ] Add service worker for offline problem viewing
- [ ] Optimize bundle size (tree-shake unused Tailwind classes)

### 15. Testing
- [ ] Backend unit tests for all API endpoints
- [ ] Backend integration tests for code execution pipeline
- [ ] Frontend component tests (React Testing Library)
- [ ] E2E tests (Playwright or Cypress)
- [ ] Load testing for code execution endpoints

---

## 📋 Recently Completed

- [x] Custom Monaco editor themes (hintcode-dark / hintcode-light) with rich syntax colors
- [x] Draggable console panel (vertical resize like LeetCode)
- [x] Collapsible left description panel with toggle
- [x] LeetCode-style viewport-locked layout (no outer scroll)
- [x] Premium Run/Submit buttons with animated loading states
- [x] Multi-language code execution (10 languages)
- [x] Light/Dark theme toggle with CSS variables
- [x] Backend caching layer (Django cache framework)
- [x] Resizable split panes (left description / right editor)
- [x] Local submission history with restore functionality

---

## 🏗️ Architecture Overview

```
Frontend (React + Vite + Tailwind)
├── Pages: TopicsHome, TopicProblems, ProblemList, ProblemDetail
├── Components: Navbar, SignIn, MonacoEditor, ThemeToggle
└── Services: apiClient, authService, codeService, hintService, problemService

Backend (Django + DRF)
├── Models: Problem, UserProgress, Attempt, Hint, HintDelivery, HintEvaluation
├── Views: AuthViewSet, ProblemViewSet, CodeViewSet, HintViewSet
├── Services: ExecutionService (Piston/local), HintChain (LangChain), RAGService
└── Infrastructure: SQLite (dev) → PostgreSQL (prod), Redis cache
```
