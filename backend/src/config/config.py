import os

ENV = os.getenv("ENV", "development")

if ENV == "production":
    BASE_URL = "https://your-frontend.onrender.com"
else:
    BASE_URL = "http://localhost:8080"