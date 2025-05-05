# 1. Use Python 3.10 slim image as the base image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /usr/src/app

# 3. Copy the requirements.txt file into the container and install the required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application files into the container
COPY . .

# 5. Expose port 8080 (the default port for Cloud Run)
EXPOSE 8080

# 6. Run the FastAPI application with uvicorn, binding to all available IP addresses and port 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
