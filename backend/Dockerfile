# 1. Use Python 3.10 slim image as the base image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /usr/src/app

# 3. Copy the requirements.txt file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application files into the container
COPY . .

# 5. Make sure Python can import from 'src'
ENV PYTHONPATH=/usr/src/app/src

# 6. Expose port 8080 (default for Cloud Run)
EXPOSE 8080

# 7. Run the FastAPI application using Uvicorn on port 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
