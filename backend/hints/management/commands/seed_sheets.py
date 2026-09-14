from django.core.management.base import BaseCommand
from hints.models import Problem, ProblemSheet, SheetProblem
import random

class Command(BaseCommand):
    help = 'Seeds random problem sheets'

    def handle(self, *args, **kwargs):
        # Create some default sheets
        sheet_data = [
            {
                "title": "Top Interview 50",
                "description": "Must-do problems to ace your interviews.",
            },
            {
                "title": "Blind 75",
                "description": "The famous Blind 75 list covering core data structures.",
            },
            {
                "title": "Dynamic Programming Mastery",
                "description": "Advanced DP patterns and techniques.",
            }
        ]

        problems = list(Problem.objects.all())
        if not problems:
            self.stdout.write(self.style.WARNING("No problems in DB! Please load problems first."))
            return

        for data in sheet_data:
            sheet, created = ProblemSheet.objects.get_or_create(title=data['title'], defaults={'description': data['description']})
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created sheet: {sheet.title}"))
                # Pick random 5 problems for this sheet
                num_to_pick = min(5, len(problems))
                selected_problems = random.sample(problems, num_to_pick)
                
                for idx, prob in enumerate(selected_problems):
                    SheetProblem.objects.create(sheet=sheet, problem=prob, order=idx)
            else:
                self.stdout.write(self.style.WARNING(f"Sheet already exists: {sheet.title}"))
