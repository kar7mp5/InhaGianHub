# Deploy

## Front-End

### Step 1: Login Firebase

```bash
firebase login
```

### Step 2: Initialize Project

```bash
firebase init
```

### Step 3: Add the API path

```env
VITE_API_BASE_URL=https://your-cloudrun-backend.a.run.app
```

### Step 4: Build Front-end Project

```bash
yarn build
```

### Step 5: Depoly to Firebase

```bash
firebase deploy
```

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
  --allow-unauthenticated \
  --set-env-vars FRONTEND_ORIGIN=https://inhagianhub-14f8d.web.app \
  --set-secrets FIREBASE_CREDENTIALS=firebase-credentials:latest
```
