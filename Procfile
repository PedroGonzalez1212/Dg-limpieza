web: flask db upgrade && gunicorn -w 3 --threads 2 --timeout 60 --max-requests 1000 --max-requests-jitter 100 run:app
