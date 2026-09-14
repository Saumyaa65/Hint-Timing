# 🚀 Quick Start: Load JSONL Problems into Your Coding Platform

## ✅ What I've Created for You

I've analyzed your coding platform and created a complete solution to load problems from your `problems_full.jsonl` file:

### 📦 New Files Created:

1. **`backend/load_jsonl_problems.py`** - Main loader script
2. **`backend/JSONL_LOADER_README.md`** - Detailed documentation
3. **`PLATFORM_STRUCTURE.md`** - Complete architecture overview
4. **`QUICK_START.md`** - This file!

### 🔧 Modified Files:

1. **`backend/hints/serializers.py`** - Enhanced to support JSONL data
   - Added `description_preview` for problem list
   - Improved test case extraction
   - Added `hints_available` count

## ✨ NEW: Enhanced Topic Display

I've added several enhancements to make topics more prominent:

1. **Topic View Mode**: Toggle between List View and Topic View
2. **Topic Statistics**: Interactive overview showing problem counts per topic
3. **Colorful Badges**: Each topic gets a unique color for easy identification
4. **Fixed Difficulty**: Properly handles "beginner/intermediate/advanced" from JSONL
5. **Topic Grouping**: See all problems organized by topic in Topic View

See `TOPIC_VIEW_ENHANCEMENTS.md` for detailed documentation.

## 🎯 Your JSONL Data Structure

Your `problems_full.jsonl` contains rich problem data:

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
    {"input": "5\n1 2 3 4 5", "output": "15"}
  ],
  "hints": [
    "Initialize a variable to store the sum",
    "Iterate through the array"
  ],
  "pseudocode": "FUNCTION calculate_sum...",
  "story": "Alice is learning programming..."
}
```

## 📋 Step-by-Step Instructions

### Step 1: Stop Any Running Servers

Make sure Django server is NOT running (database will be locked otherwise):

```bash
# If Django is running, press Ctrl+C to stop it
```

### Step 2: Load Problems from JSONL

```bash
cd backend
python load_jsonl_problems.py
```

**Expected Output:**
```
Clearing existing problems...
Cleared existing problems
Created problem 1: Find the sum of all elements in an array
  Created 3 hints
Created problem 2: Find the maximum element in an array
  Created 3 hints
...
============================================================
Successfully loaded 500 problems
Successfully created 1500 hints
============================================================
```

### Step 3: Verify the Load

```bash
python manage.py shell
```

Then in the shell:
```python
from hints.models import Problem, Hint

# Check counts
print(f"Total problems: {Problem.objects.count()}")
print(f"Total hints: {Hint.objects.count()}")

# View a sample problem
problem = Problem.objects.first()
print(f"\nTitle: {problem.title}")
print(f"Topic: {problem.topic}")
print(f"Difficulty: {problem.difficulty}")
print(f"Hints: {problem.hints.count()}")

# View the description (first 200 chars)
print(f"\nDescription preview:\n{problem.description[:200]}...")

# Exit shell
exit()
```

### Step 4: Start the Backend

```bash
python manage.py runserver
```

Backend will run on: http://localhost:8000

### Step 5: Start the Frontend

Open a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will run on: http://localhost:5173

### Step 6: Test the Platform

1. Open browser: http://localhost:5173
2. You should see all problems from your JSONL file
3. Use filters to browse by topic/difficulty
4. Click on any problem to view details and solve it

## 🎨 What You'll See

### Problem List Page
- All problems from your JSONL file
- Filter by topic (Array, String, etc.)
- Filter by difficulty (Easy, Medium, Hard)
- Search by title
- Each problem shows:
  - Title
  - Difficulty badge
  - Topic badge
  - Description preview

### Problem Detail Page
- Full problem description with:
  - Story section
  - Problem explanation
  - Input/Output formats
  - Constraints
  - Examples with test cases
  - Pseudocode
- Code editor (Monaco Editor)
- Hints panel (progressive hints from JSONL)
- Run/Submit buttons

## 🔄 Data Flow

```
problems_full.jsonl
        ↓
load_jsonl_problems.py
        ↓
Django Database (SQLite)
  - Problem table
  - Hint table
        ↓
Django REST API
  - /api/problems/
  - /api/problems/{id}/
        ↓
React Frontend
  - ProblemList.jsx
  - ProblemDetail.jsx
```

## 📊 Field Mapping

| JSONL Field | → | Django Model | → | Frontend Display |
|-------------|---|--------------|---|------------------|
| title | → | Problem.title | → | Problem card title |
| slug | → | Problem.problem_id | → | URL identifier |
| category | → | Problem.topic | → | Topic filter/badge |
| difficulty | → | Problem.difficulty | → | Difficulty badge (Easy/Medium/Hard) |
| problem_explanation | → | Problem.description | → | Problem description |
| story | → | Problem.description | → | Story section |
| constraints | → | Problem.description | → | Constraints section |
| examples[] | → | Problem.description | → | Test cases |
| hints[] | → | Hint.content | → | Hints panel |
| pseudocode | → | Problem.description | → | Pseudocode section |

## 🎛️ Customization Options

### Load Only Some Problems (for testing)

Edit `backend/load_jsonl_problems.py`, line ~180:

```python
# Change from:
load_problems_from_jsonl(jsonl_path)

# To:
load_problems_from_jsonl(jsonl_path, limit=10)  # Load only 10
```

### Keep Existing Problems

Edit `backend/load_jsonl_problems.py`, line ~95:

```python
# Comment out this line:
# Problem.objects.all().delete()
```

### Change Difficulty Mapping

Edit `backend/load_jsonl_problems.py`, line ~30:

```python
def map_difficulty(jsonl_difficulty):
    difficulty_map = {
        'beginner': 'easy',      # Customize these
        'intermediate': 'medium',
        'advanced': 'hard'
    }
    return difficulty_map.get(jsonl_difficulty.lower(), 'medium')
```

### Customize Description Format

Edit `backend/load_jsonl_problems.py`, line ~45:

```python
def format_problem_description(problem_data):
    sections = []
    
    # Add/remove/reorder sections as needed
    if problem_data.get('story'):
        sections.append(f"## Story\n{problem_data['story']}\n")
    
    # ... customize other sections
    
    return "\n".join(sections)
```

## 🐛 Troubleshooting

### Problem: Database is locked
**Solution:** Stop the Django server before running the loader

### Problem: File not found
**Solution:** Make sure you're in the `backend` directory

### Problem: No problems showing in frontend
**Solution:** 
1. Check backend is running: http://localhost:8000/api/problems/
2. Check browser console for errors
3. Verify problems loaded: `python manage.py shell` → `Problem.objects.count()`

### Problem: JSON decode error
**Solution:** Check the JSONL file for malformed JSON on that line

## 📈 Next Steps

After loading your problems:

1. ✅ **Browse Problems** - Use filters and search
2. ✅ **Solve Problems** - Use the code editor
3. ✅ **Get Hints** - Progressive hints from your JSONL
4. 🔄 **Customize UI** - Modify React components
5. 🔄 **Add Features** - User profiles, leaderboard, etc.

## 🎓 Understanding the Code

### Loader Script (`load_jsonl_problems.py`)

```python
# Main function
def load_problems_from_jsonl(file_path, limit=None):
    # 1. Clear existing problems (optional)
    Problem.objects.all().delete()
    
    # 2. Read JSONL file line by line
    with open(file_path, 'r') as f:
        for line in f:
            problem_data = json.loads(line)
            
            # 3. Create Problem record
            problem = Problem.objects.create(
                title=problem_data['title'],
                problem_id=problem_data['slug'],
                topic=problem_data['category'],
                difficulty=map_difficulty(problem_data['difficulty']),
                description=format_problem_description(problem_data)
            )
            
            # 4. Create Hint records
            for level, hint_text in enumerate(problem_data['hints'], 1):
                Hint.objects.create(
                    problem=problem,
                    content=hint_text,
                    level=level
                )
```

### API Endpoints

```python
# backend/hints/problem_views.py
class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Problem.objects.all()
    
    def get_queryset(self):
        # Supports filtering
        queryset = Problem.objects.all()
        
        if self.request.query_params.get('topic'):
            queryset = queryset.filter(topic=topic)
        
        if self.request.query_params.get('difficulty'):
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset
```

### Frontend Service

```javascript
// frontend/src/services/problemService.js
const problemService = {
  getAllProblems: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    return apiClient.get(`/problems/?${params}`);
  },
  
  getProblemById: async (id) => {
    return apiClient.get(`/problems/${id}/`);
  }
};
```

## 📚 Additional Resources

- **`PLATFORM_STRUCTURE.md`** - Complete architecture overview
- **`backend/JSONL_LOADER_README.md`** - Detailed loader documentation
- **Django REST Framework Docs** - https://www.django-rest-framework.org/
- **React Router Docs** - https://reactrouter.com/

## 💡 Tips

1. **Start Small**: Load 10-20 problems first to test
2. **Check API**: Visit http://localhost:8000/api/problems/ to see JSON
3. **Use Browser DevTools**: Check Network tab for API calls
4. **Read Logs**: Backend terminal shows all API requests
5. **Backup Database**: Copy `db.sqlite3` before major changes

## ✨ Features Already Working

- ✅ Problem browsing with filters
- ✅ Problem detail view
- ✅ Code editor (Monaco)
- ✅ Hint system
- ✅ Code execution (backend logic in place)
- ✅ User authentication
- ✅ Progress tracking

## 🎉 You're All Set!

Your coding platform is ready to use with all the problems from your JSONL file. The data flows seamlessly from the file → database → API → frontend.

Happy coding! 🚀

