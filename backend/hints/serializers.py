from rest_framework import serializers
from .models import Problem, Attempt, Hint, HintDelivery

class ProblemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Problem model (list view).
    """
    description_preview = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ['id', 'problem_id', 'title', 'difficulty', 'topic', 'created_at', 'description_preview']

    def get_description_preview(self, obj):
        """Get a short preview of the description."""
        if not obj.description:
            return ""
        # Extract first paragraph or first 150 characters
        lines = obj.description.split('\n')
        fallback_line = ""
        for line in lines:
            line = line.strip()
            if line:
                if not line.startswith('#'):
                    # Remove markdown formatting
                    preview = line.replace('**', '').replace('*', '').replace('`', '')
                    return preview[:150] + '...' if len(preview) > 150 else preview
                elif not fallback_line:
                    # Capture stripped header as a fallback preview
                    fallback_line = line.lstrip('#').strip()
        
        if fallback_line:
            preview = fallback_line.replace('**', '').replace('*', '').replace('`', '')
            return preview[:150] + '...' if len(preview) > 150 else preview
        return ""

class ProblemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the Problem model (detail view).
    """
    tests = serializers.SerializerMethodField()
    starting_code = serializers.SerializerMethodField()
    topic = serializers.CharField(default='General')
    hints_available = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ['id', 'problem_id', 'title', 'description', 'difficulty',
                  'created_at', 'topic', 'tests', 'starting_code', 'hints_available']

    def get_tests(self, obj):
        """
        Get test cases for the problem.
        Extracts examples from the description if formatted properly.
        """
        tests = []

        # Try to extract examples from description
        if obj.description:
            lines = obj.description.split('\n')
            current_input = None
            current_output = None
            in_code_block = False
            code_block_content = []

            for i, line in enumerate(lines):
                # Detect code blocks
                if line.strip().startswith('```'):
                    if in_code_block:
                        # End of code block
                        content = '\n'.join(code_block_content).strip()
                        if current_input is None:
                            current_input = content
                        elif current_output is None:
                            current_output = content
                        code_block_content = []
                        in_code_block = False
                    else:
                        # Start of code block
                        in_code_block = True
                    continue

                if in_code_block:
                    code_block_content.append(line)
                    continue

                # Look for Input/Output markers
                if '**Input:**' in line or 'Input:' in line:
                    # Save previous test if complete
                    if current_input and current_output:
                        tests.append({
                            'input': current_input,
                            'expected': current_output,
                            'explanation': ''
                        })
                    current_input = None
                    current_output = None
                elif '**Output:**' in line or 'Output:' in line:
                    pass  # Just a marker

        # If no tests extracted, return default template
        if not tests:
            tests = [
                {
                    'input': '5\n1 2 3 4 5',
                    'expected': '15',
                    'explanation': 'Sum of all elements'
                }
            ]

        return tests[:10]  # Limit to 10 test cases

    def get_starting_code(self, obj):
        """
        Get starting code template for the problem.
        Returns language-specific templates based on problem type.
        """
        # Default JavaScript template
        template = """function solution(input) {
    // Read input
    const lines = input.trim().split('\\n');
    const n = parseInt(lines[0]);
    const arr = lines[1].split(' ').map(Number);

    // Your code here

    return result;
}"""
        return template

    def get_hints_available(self, obj):
        """Return the number of hints available for this problem."""
        return obj.hints.count()

class AttemptSerializer(serializers.ModelSerializer):
    """
    Serializer for the Attempt model.
    """
    class Meta:
        model = Attempt
        fields = ['id', 'user_id', 'problem', 'code', 'language', 'status', 'execution_time', 'evaluation_details', 'created_at']

class HintSerializer(serializers.ModelSerializer):
    """
    Serializer for the Hint model.
    """
    class Meta:
        model = Hint
        fields = ['id', 'problem', 'content', 'level', 'hint_type', 'created_at']

class HintDeliverySerializer(serializers.ModelSerializer):
    """
    Serializer for the HintDelivery model.
    """
    hint = HintSerializer()
    
    class Meta:
        model = HintDelivery
        fields = ['id', 'hint', 'user_id', 'is_auto_triggered', 'feedback', 'rating', 'created_at']

# --- Social Models Serializers ---
from .models import ForumPost, ForumComment, SolutionShare

class ForumCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ForumComment
        fields = ['id', 'post', 'user', 'username', 'content', 'upvotes', 'created_at', 'updated_at']
        read_only_fields = ['user', 'upvotes']

class ForumPostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    comments = ForumCommentSerializer(many=True, read_only=True)

    class Meta:
        model = ForumPost
        fields = ['id', 'user', 'username', 'problem', 'title', 'content', 'upvotes', 'comments', 'created_at', 'updated_at']
        read_only_fields = ['user', 'upvotes']

class SolutionShareSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SolutionShare
        fields = ['id', 'attempt', 'user', 'username', 'problem', 'title', 'explanation', 'upvotes', 'created_at']
        read_only_fields = ['user', 'upvotes']

# --- Problem Sheet & Daily Problem Serializers ---
from .models import ProblemSheet, SheetProblem, DailyProblem

class SheetProblemSerializer(serializers.ModelSerializer):
    problem = ProblemSerializer(read_only=True)
    
    class Meta:
        model = SheetProblem
        fields = ['id', 'problem', 'order']

class ProblemSheetSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    sheet_problems = SheetProblemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProblemSheet
        fields = ['id', 'title', 'description', 'author_name', 'is_public', 'sheet_problems', 'created_at']

class DailyProblemSerializer(serializers.ModelSerializer):
    problem = ProblemDetailSerializer(read_only=True)
    
    class Meta:
        model = DailyProblem
        fields = ['id', 'date', 'problem', 'created_at']