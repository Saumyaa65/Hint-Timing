# Loading Problems from JSONL File

This guide explains how to load problems from the `problems_full.jsonl` file into your Django database.

## Overview

The `problems_full.jsonl` file contains coding problems with the following structure:
- **title**: Problem title
- **slug**: URL-friendly identifier
- **category**: Problem category (Array, String, etc.)
- **difficulty**: beginner/intermediate/advanced
- **problem_explanation**: Main problem description
- **constraints**: Problem constraints
- **input_format**: Expected input format
- **output_format**: Expected output format
- **examples**: Array of test cases with input/output
- **hints**: Array of hint strings
- **pseudocode**: Solution pseudocode
- **story**: Problem context/story

## How to Load Problems

### Method 1: Using Django Shell (Recommended)

```bash
cd backend
python manage.py shell < load_jsonl_problems.py
```

### Method 2: Run as Python Script

```bash
cd backend
python load_jsonl_problems.py
```

### Method 3: Load Limited Number (for testing)

Edit `load_jsonl_problems.py` and uncomment the limit parameter:

```python
# At the bottom of the file, change:
load_problems_from_jsonl(jsonl_path)  # Load all

# To:
load_problems_from_jsonl(jsonl_path, limit=10)  # Load only 10
```

## What the Script Does

1. **Clears existing problems** (optional - can be disabled)
2. **Parses JSONL file** line by line
3. **Maps fields** from JSONL to Django models:
   - `difficulty`: beginner → easy, intermediate → medium, advanced → hard
   - `category` → `topic`
   - `slug` → `problem_id`
4. **Creates Problem records** with formatted descriptions
5. **Creates Hint records** for each problem
6. **Formats descriptions** with sections:
   - Story
   - Problem explanation
   - Input/Output formats
   - Constraints
   - Examples
   - Pseudocode

## Database Schema Mapping

| JSONL Field | Django Model | Field Name |
|-------------|--------------|------------|
| title | Problem | title |
| slug | Problem | problem_id |
| category | Problem | topic |
| difficulty | Problem | difficulty |
| problem_explanation + more | Problem | description |
| hints[n] | Hint | content |

## Verifying the Load

After loading, verify in Django shell:

```bash
python manage.py shell
```

```python
from hints.models import Problem, Hint

# Check number of problems
print(f"Total problems: {Problem.objects.count()}")

# Check number of hints
print(f"Total hints: {Hint.objects.count()}")

# View a sample problem
problem = Problem.objects.first()
print(f"Title: {problem.title}")
print(f"Topic: {problem.topic}")
print(f"Difficulty: {problem.difficulty}")
print(f"Hints: {problem.hints.count()}")

# View hints for a problem
for hint in problem.hints.all():
    print(f"  Level {hint.level}: {hint.content[:50]}...")
```

## API Endpoints

After loading, the problems will be available via:

- **GET /api/problems/** - List all problems (with filters)
  - Query params: `?topic=Array&difficulty=easy&search=sum`
- **GET /api/problems/{id}/** - Get problem details
- **GET /api/problems/topics/** - Get all available topics

## Frontend Integration

The frontend is already configured to fetch from these endpoints:

1. **ProblemList.jsx** - Displays all problems with filters
2. **ProblemDetail.jsx** - Shows individual problem with code editor
3. **problemService.js** - Handles API calls

## Customization

### Modify Description Format

Edit the `format_problem_description()` function in `load_jsonl_problems.py`:

```python
def format_problem_description(problem_data):
    sections = []
    
    # Add or remove sections as needed
    if problem_data.get('story'):
        sections.append(f"## Story\n{problem_data['story']}\n")
    
    # ... customize other sections
    
    return "\n".join(sections)
```

### Change Difficulty Mapping

Edit the `map_difficulty()` function:

```python
def map_difficulty(jsonl_difficulty):
    difficulty_map = {
        'beginner': 'easy',
        'intermediate': 'medium',
        'advanced': 'hard'
    }
    return difficulty_map.get(jsonl_difficulty.lower(), 'medium')
```

### Keep Existing Problems

Comment out the delete line in `load_problems_from_jsonl()`:

```python
# Problem.objects.all().delete()  # Comment this out
```

## Troubleshooting

### File Not Found Error
```
Error: File problems_full.jsonl not found!
```
**Solution**: Make sure you're running the script from the `backend` directory.

### JSON Decode Error
```
Error parsing line X: ...
```
**Solution**: Check that line in the JSONL file for malformed JSON.

### Database Locked Error
```
database is locked
```
**Solution**: Make sure no other Django processes are running.

### Import Error
```
ModuleNotFoundError: No module named 'hints'
```
**Solution**: Make sure Django is properly set up and you're in the backend directory.

## Next Steps

After loading problems:

1. **Start the backend server**:
   ```bash
   python manage.py runserver
   ```

2. **Start the frontend**:
   ```bash
   cd ../frontend
   npm run dev
   ```

3. **Access the platform**:
   - Open http://localhost:5173
   - Browse problems
   - Click on a problem to view details
   - Try solving with the code editor

## Additional Features

The loader script can be extended to:
- Load test cases into a separate TestCase model
- Parse and store similar problems
- Extract and store code templates
- Import problem metadata (tags, companies, etc.)

