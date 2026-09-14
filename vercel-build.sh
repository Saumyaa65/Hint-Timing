#!/bin/bash

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create a simple vercel_app.py file for Vercel
cat > vercel_app.py << 'EOF'
from hint_system.wsgi import application

# Vercel expects the app variable
app = application
EOF

echo "Build completed successfully!"
