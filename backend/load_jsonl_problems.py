#!/usr/bin/env python
"""
Script to load problems from problems_full.jsonl into the database.
Run this script using:
python manage.py shell < load_jsonl_problems.py

Or run directly:
python load_jsonl_problems.py
"""

import json
import os
import sys
import django

# Setup Django environment if running directly
if __name__ == '__main__':
    # Add the backend directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')
    django.setup()

from hints.models import Problem, Hint

def clean_text(text):
    """Clean text by removing extra whitespace and newlines."""
    if not text:
        return ""
    return " ".join(text.split())

def map_difficulty(jsonl_difficulty):
    """Map JSONL difficulty to Django model choices."""
    difficulty_map = {
        'beginner': 'easy',
        'easy': 'easy',
        'intermediate': 'medium',
        'medium': 'medium',
        'advanced': 'hard',
        'hard': 'hard'
    }
    return difficulty_map.get(jsonl_difficulty.lower(), 'medium')

def format_problem_description(problem_data):
    """Format a comprehensive problem description from JSONL data."""
    sections = []
    
    # Story (if available)
    if problem_data.get('story'):
        sections.append(f"## Story\n{problem_data['story']}\n")
    
    # Problem Explanation
    if problem_data.get('problem_explanation'):
        sections.append(f"## Problem\n{problem_data['problem_explanation']}\n")
    
    # Input Format
    if problem_data.get('input_format'):
        sections.append(f"## Input Format\n{problem_data['input_format']}\n")
    
    # Output Format
    if problem_data.get('output_format'):
        sections.append(f"## Output Format\n{problem_data['output_format']}\n")
    
    # Constraints
    if problem_data.get('constraints'):
        sections.append(f"## Constraints\n{problem_data['constraints']}\n")
    
    # Examples
    if problem_data.get('examples'):
        sections.append("## Examples\n")
        for i, example in enumerate(problem_data['examples'][:5], 1):  # Limit to 5 examples
            sections.append(f"### Example {i}:\n")
            sections.append(f"**Input:**\n```\n{example.get('input', '')}\n```\n")
            sections.append(f"**Output:**\n```\n{example.get('output', '')}\n```\n")
            if example.get('explanation'):
                sections.append(f"**Explanation:** {example['explanation']}\n")
    
    # Pseudocode (if available)
    if problem_data.get('pseudocode'):
        sections.append(f"## Pseudocode\n```\n{problem_data['pseudocode']}\n```\n")
    
    return "\n".join(sections)

def load_problems_from_jsonl(file_path='curated_problems_1k.jsonl', limit=None):
    """
    Load problems from JSONL file into the database.
    
    Args:
        file_path: Path to the JSONL file
        limit: Optional limit on number of problems to load
    """
    # Check both relative and backend path
    if not os.path.exists(file_path):
        file_path = os.path.join(os.path.dirname(__file__), file_path)
        
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        return
    
    # Clear existing problems
    print("Clearing existing problems...")
    Problem.objects.all().delete()
    print("Cleared existing problems")
    
    problems_created = 0
    problems_skipped = 0
    hints_created = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if limit and problems_created >= limit:
                break

            try:
                problem_data = json.loads(line.strip())

                # Extract basic fields
                title = problem_data.get('title', f"Problem {line_num}")
                slug = problem_data.get('slug', f"problem-{line_num}")
                
                # Use our smarter curated roadmap category
                category = problem_data.get('roadmap_category', problem_data.get('category', 'General'))
                difficulty = map_difficulty(problem_data.get('difficulty', 'medium'))

                # Format comprehensive description
                description = format_problem_description(problem_data)

                # Create the problem
                problem = Problem.objects.create(
                    problem_id=slug,
                    title=title,
                    description=description,
                    difficulty=difficulty,
                    topic=category
                )

                problems_created += 1
                if problems_created % 50 == 0:  # Print progress every 50 problems
                    print(f"Created {problems_created} problems so far...")
                elif problems_created <= 10:  # Print first 10
                    print(f"Created problem {problems_created}: {title}")
                
                # Create hints for this problem
                if problem_data.get('hints'):
                    for level, hint_text in enumerate(problem_data['hints'], 1):
                        # Determine hint type based on level
                        if level == 1:
                            hint_type = 'conceptual'
                        elif level == 2:
                            hint_type = 'approach'
                        else:
                            hint_type = 'implementation'

                        Hint.objects.create(
                            problem=problem,
                            content=hint_text,
                            level=level,
                            hint_type=hint_type
                        )
                        hints_created += 1

                    if problems_created <= 10:  # Only print hint count for first 10
                        print(f"  Created {len(problem_data['hints'])} hints")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error creating problem from line {line_num}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully loaded {problems_created} NEW problems")
    print(f"✅ Successfully created {hints_created} hints")
    print(f"⏭️  Skipped {problems_skipped} duplicate problems")
    print(f"📊 Total unique problems in database: {Problem.objects.count()}")
    print(f"{'='*60}")

if __name__ == '__main__':
    # Get the file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jsonl_path = os.path.join(script_dir, 'problems_full.jsonl')
    
    # Load all problems (or specify a limit for testing)
    # load_problems_from_jsonl(jsonl_path, limit=10)  # Load only 10 for testing
    load_problems_from_jsonl(jsonl_path)  # Load all problems

