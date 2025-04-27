FROM python:3.10-slim

WORKDIR /app

# requirements 폴더 복사 (루트 기준)
COPY requirements/ ./requirements/

RUN pip install --no-cache-dir -r requirements/all-requirements.txt

# app 폴더 코드 복사
COPY app/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
