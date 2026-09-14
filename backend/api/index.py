import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')

# Import Django
import django
django.setup()

# Import and create the WSGI application
from django.core.wsgi import get_wsgi_application

# Vercel expects the app variable
app = get_wsgi_application()
