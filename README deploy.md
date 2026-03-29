# Public Web Bundle Deployment

Local run:

pip install -r requirements.txt
python app.py

Render build command:

pip install -r requirements.txt

Render start command:

gunicorn --bind 0.0.0.0:$PORT app:app
