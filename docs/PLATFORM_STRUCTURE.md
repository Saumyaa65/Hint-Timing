# Coding Platform Structure & Data Flow

## 📁 Project Structure

```
Coding_Platform/
├── backend/
│   ├── hint_system/          # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── hints/                # Main Django app
│   │   ├── models.py         # Problem, Hint, Attempt, etc.
│   │   ├── serializers.py    # REST API serializers
│   │   ├── views.py          # Hint generation views
│   │   ├── problem_views.py  # Problem CRUD views
│   │   ├── code_views.py     # Code execution views
│   │   └── migrations/       # Database migrations
│   ├── problems_full.jsonl   # 🎯 YOUR PROBLEM DATA
│   ├── load_jsonl_problems.py # 🔧 Loader script
│   ├── init_db.py            # Old sample data loader
│   ├── manage.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/       # Reusable UI components
    │   │   ├── MonacoEditor.jsx
    │   │   ├── HintsPanel.jsx
    │   │   └── Navbar.jsx
    │   ├── pages/            # Main pages
    │   │   ├── ProblemList.jsx    # Browse problems
    │   │   └── ProblemDetail.jsx  # Solve problems
    │   ├── services/         # API clients
    │   │   ├── problemService.js
    │   │   ├── hintService.js
    │   │   └── codeService.js
    │   └── App.jsx
    └── package.json
```

## 🔄 Data Flow: JSONL → Database → Frontend

### Step 1: JSONL File Structure
```json
{
  "title": "Find the sum of all elements in an array",
  "slug": "find-the-sum-of-all-elements-in-an-array",
  "category": "Array",
  "difficulty": "beginner",
  "problem_explanation": "Given an array of integers...",
  "constraints": "* 1 <= N <= 1000...",
  "input_format": "The first line contains...",
  "output_format": "Print the sum...",
  "examples": [
    {"input": "5\n1 2 3 4 5", "output": "15"},
    {"input": "3\n-1 0 1", "output": "0"}
  ],
  "hints": [
    "Initialize a variable to store the sum",
    "Iterate through the array",
    "Add each element to the sum"
  ],
  "pseudocode": "FUNCTION calculate_sum(array):\n  sum = 0\n  FOR each element...",
  "story": "Alice is learning programming..."
}
```

### Step 2: Load into Django Database
```bash
cd backend
python manage.py shell < load_jsonl_problems.py
```

**What happens:**
1. Script reads `problems_full.jsonl` line by line
2. Parses each JSON object
3. Maps fields to Django models:
   - Creates `Problem` record
   - Creates multiple `Hint` records
4. Formats description with all sections

### Step 3: Django Models (Database Schema)

```python
# Problem Model
class Problem(models.Model):
    id = AutoField(primary_key=True)
    problem_id = CharField(max_length=50, unique=True)  # slug from JSONL
    title = CharField(max_length=200)
    description = TextField()  # Formatted from multiple JSONL fields
    difficulty = CharField(choices=['easy', 'medium', 'hard'])
    topic = CharField(max_length=100)  # category from JSONL
    created_at = DateTimeField(auto_now_add=True)

# Hint Model
class Hint(models.Model):
    problem = ForeignKey(Problem)
    content = TextField()
    level = IntegerField()  # 1, 2, 3...
    hint_type = CharField(choices=['conceptual', 'approach', 'implementation'])
```

### Step 4: REST API Endpoints

```
GET  /api/problems/                    # List all problems
GET  /api/problems/?topic=Array        # Filter by topic
GET  /api/problems/?difficulty=easy    # Filter by difficulty
GET  /api/problems/?search=sum         # Search by title
GET  /api/problems/{id}/               # Get problem details
GET  /api/problems/topics/             # Get all topics
POST /api/problems/{id}/submit/        # Submit code
GET  /api/problems/{id}/hints/         # Get hints
```

### Step 5: Frontend Services

```javascript
// problemService.js
const problemService = {
  getAllProblems: async (filters) => {
    // Calls: GET /api/problems/?topic=...&difficulty=...
    return apiClient.get('/problems/', { params: filters });
  },
  
  getProblemById: async (id) => {
    // Calls: GET /api/problems/{id}/
    return apiClient.get(`/problems/${id}/`);
  }
};
```

### Step 6: React Components

```jsx
// ProblemList.jsx - Browse problems
function ProblemList() {
  const [problems, setProblems] = useState([]);
  
  useEffect(() => {
    problemService.getAllProblems()
      .then(data => setProblems(data));
  }, []);
  
  return (
    <div>
      {problems.map(problem => (
        <ProblemCard 
          title={problem.title}
          difficulty={problem.difficulty}
          topic={problem.topic}
        />
      ))}
    </div>
  );
}

// ProblemDetail.jsx - Solve problem
function ProblemDetail() {
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');
  
  useEffect(() => {
    problemService.getProblemById(id)
      .then(data => {
        setProblem(data);
        setCode(data.starting_code);
      });
  }, [id]);
  
  return (
    <div>
      <ProblemDescription description={problem.description} />
      <MonacoEditor code={code} onChange={setCode} />
      <HintsPanel problemId={problem.id} />
    </div>
  );
}
```

## 🎯 Complete Flow Diagram

```
┌─────────────────────┐
│ problems_full.jsonl │
│  (Your data file)   │
└──────────┬──────────┘
           │
           │ python load_jsonl_problems.py
           ▼
┌─────────────────────┐
│  Django Database    │
│  ┌───────────────┐  │
│  │ Problem Table │  │
│  │ - id          │  │
│  │ - title       │  │
│  │ - description │  │
│  │ - difficulty  │  │
│  │ - topic       │  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │  Hint Table   │  │
│  │ - problem_id  │  │
│  │ - content     │  │
│  │ - level       │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           │ Django REST API
           ▼
┌─────────────────────┐
│   API Endpoints     │
│ /api/problems/      │
│ /api/problems/{id}/ │
│ /api/hints/         │
└──────────┬──────────┘
           │
           │ HTTP Requests
           ▼
┌─────────────────────┐
│  React Frontend     │
│  ┌───────────────┐  │
│  │ ProblemList   │  │
│  │ - Browse      │  │
│  │ - Filter      │  │
│  │ - Search      │  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ ProblemDetail │  │
│  │ - Description │  │
│  │ - Code Editor │  │
│  │ - Hints       │  │
│  │ - Submit      │  │
│  └───────────────┘  │
└─────────────────────┘
```

## 🚀 Quick Start Guide

### 1. Load Problems from JSONL
```bash
cd backend
python manage.py shell < load_jsonl_problems.py
```

### 2. Start Backend
```bash
cd backend
python manage.py runserver
# Runs on http://localhost:8000
```

### 3. Start Frontend
```bash
cd frontend
npm install  # First time only
npm run dev
# Runs on http://localhost:5173
```

### 4. Access Platform
- Open browser: http://localhost:5173
- Browse problems from your JSONL file
- Click on any problem to solve it
- Use the code editor to write solutions
- Get hints when stuck

## 📊 Data Mapping Reference

| JSONL Field | Django Model | Frontend Display |
|-------------|--------------|------------------|
| title | Problem.title | Problem card title |
| slug | Problem.problem_id | URL identifier |
| category | Problem.topic | Topic filter/badge |
| difficulty | Problem.difficulty | Difficulty badge |
| problem_explanation | Problem.description | Problem description |
| examples[].input | Serializer.tests | Test cases |
| examples[].output | Serializer.tests | Expected output |
| hints[] | Hint.content | Hints panel |
| story | Problem.description | Story section |
| constraints | Problem.description | Constraints section |
| pseudocode | Problem.description | Pseudocode section |

## 🔧 Customization Options

### Add More Fields to Problem Model
Edit `backend/hints/models.py`:
```python
class Problem(models.Model):
    # ... existing fields ...
    tags = models.JSONField(default=list, blank=True)
    companies = models.JSONField(default=list, blank=True)
    acceptance_rate = models.FloatField(default=0.0)
```

Then create and run migration:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Modify Description Format
Edit `backend/load_jsonl_problems.py`:
```python
def format_problem_description(problem_data):
    # Customize sections, order, formatting
    sections = []
    # Add your custom sections
    return "\n".join(sections)
```

### Change Frontend Display
Edit `frontend/src/pages/ProblemDetail.jsx`:
```jsx
// Customize how problem description is rendered
// Add syntax highlighting, collapsible sections, etc.
```

## 📝 Notes

- The JSONL file contains **rich problem data** with stories, examples, hints, and pseudocode
- The loader script **formats all this data** into a comprehensive description
- The frontend is **already configured** to display problems from the API
- You can **filter by topic and difficulty** on the frontend
- **Hints are stored separately** and can be revealed progressively
- The platform supports **code execution and submission** (backend logic in place)

## 🎓 Next Steps

1. ✅ Load your JSONL data
2. ✅ Start both servers
3. ✅ Browse and solve problems
4. 🔄 Customize the UI/UX as needed
5. 🔄 Add more features (leaderboard, user profiles, etc.)

