# Create virtual environment
python3 -m venv venv

# require
pip install -r requirements.txt 

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run the Flask application
python3 app.py

# The backend will be available at: http://localhost:5000