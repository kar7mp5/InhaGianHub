# Deploy

## Front-End

## Back-End

### Step 1: Upload Secret Manager

```bash
gcloud secrets create firebase-credentials \
  --data-file=firebase_credentials.json
```

### Step 2: Grant Cloud Run access to the secret

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 3: Build and push Docker image

```bash
docker build -t gcr.io/<PROJECT_ID>/fastapi-app .
docker push gcr.io/<PROJECT_ID>/fastapi-app
```

### Step 4: Mount the secret as an environment variable in Cloud Run

```bash
gcloud run deploy inhagianhubapi \
  --image gcr.io/<PROJECT_ID>/fastapi-app \
  --platform managed \
  --port 8080 \
  --region asia-northeast3 \
  --set-secrets FIREBASE_CREDENTIALS=firebase-credentials:latest
```
