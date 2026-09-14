from django.core.management.base import BaseCommand
from hints.models import Problem, DailyProblem
from django.utils import timezone
import random
import uuid

class Command(BaseCommand):
    help = 'Generates a new Daily Problem and assigns it as the POTD'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        # Check if today's POTD already exists
        if DailyProblem.objects.filter(date=today).exists():
            self.stdout.write(self.style.WARNING(f"A Problem of the Day already exists for {today}"))
            return

        # Generate a new unique problem
        unique_id = str(uuid.uuid4())[:8]
        
        # In a real app, this would use an LLM or an external API to generate a new problem.
        # For now, we will create a mock new problem.
        problem_data = {
            'problem_id': f"daily_{unique_id}",
            'title': f"Daily Challenge: {unique_id.upper()}",
            'description': f"This is the daily challenge for {today}.\n\nWrite a function to solve the mystery of {unique_id}.\n\n### Examples\n\n```javascript\nInput: '{unique_id}'\nOutput: 'solved'\n```",
            'difficulty': random.choice(['easy', 'medium', 'hard']),
            'topic': random.choice(['Arrays', 'Strings', 'Dynamic Programming', 'Graphs'])
        }
        
        problem = Problem.objects.create(**problem_data)
        
        # Assign it to today's POTD
        DailyProblem.objects.create(date=today, problem=problem)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created Daily Problem: {problem.title}"))
