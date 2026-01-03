# Garden Genie Backend - Docker Deployment Guide

## 🎯 Quick Start (For EC2 Deployment)

### Prerequisites
- AWS EC2 instance (Ubuntu recommended)
- SSH access to the EC2 instance
- OpenAI API key

### Step 1: Upload Files to EC2

```bash
# On your local machine, zip the repository
cd Genie_AI_Backend
git add .
git commit -m "Prepare for docker deployment"
git push origin main

# On EC2, pull the latest code
cd ~/Genie_AI_Backend
git pull origin main
```

### Step 2: Create .env File

```bash
# Copy the production env template
cp .env.production .env

# Edit the .env file and add your OPENAI_API_KEY
nano .env

# Update this line:
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 3: Make Deploy Script Executable

```bash
chmod +x deploy.sh
```

### Step 4: Run Deployment

```bash
./deploy.sh
```

The script will:
- ✅ Install Docker and docker-compose (if needed)
- ✅ Stop old containers
- ✅ Build new Docker image
- ✅ Start the application
- ✅ Run health checks
- ✅ Test critical endpoints

### Step 5: Verify Deployment

```bash
# Check if container is running
docker ps

# View logs
docker-compose logs -f

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/products/
```

---

## 🔧 Configuration

### Environment Variables

All configuration is in the `.env` file:

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://...

# AWS S3 (for image storage)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=gardengenieimages

# OpenAI (REQUIRED - get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-...

# SMS/OTP Service
E2A_API_KEY=...
E2A_SENDER_ID=GENIAI

# JWT Authentication
JWT_SECRET=garden_genie
```

### Important Notes

1. **OPENAI_API_KEY is REQUIRED**
   - Get it from: https://platform.openai.com/api-keys
   - Without it, `/analyze` endpoints will fail

2. **Database Connection**
   - Using Neon PostgreSQL (external)
   - No local database container needed

3. **File Storage**
   - Images stored in AWS S3
   - YOLO model stored in container

---

## 🐛 Troubleshooting

### Problem: Container won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Missing OPENAI_API_KEY
# - Database connection issues
# - Port 8000 already in use
```

### Problem: /products endpoint returns empty

```bash
# Check if products were imported
docker-compose exec app python -c "from app.models import Product; from app.utils import SessionLocal; db = SessionLocal(); print(db.query(Product).count())"

# If count is 0, products weren't imported. Check logs for errors during startup.
```

### Problem: /history endpoint fails

```bash
# Check database connection
docker-compose logs | grep -i database

# Verify DATABASE_URL is correct in .env
```

### Problem: S3 upload fails

```bash
# Verify AWS credentials in .env
# Check S3 bucket permissions
# Test AWS credentials:
docker-compose exec app python -c "import boto3; print(boto3.client('s3').list_buckets())"
```

---

## 📊 Useful Commands

### Container Management

```bash
# View running containers
docker-compose ps

# View logs (follow mode)
docker-compose logs -f

# View logs for specific time period
docker-compose logs --since 10m

# Restart containers
docker-compose restart

# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Debugging

```bash
# Enter container shell
docker-compose exec app bash

# Run Python shell inside container
docker-compose exec app python

# Check environment variables inside container
docker-compose exec app env

# Test database connection inside container
docker-compose exec app python -c "from app.utils import engine; print(engine.execute('SELECT 1').fetchone())"
```

### Maintenance

```bash
# Clean up old images
docker image prune -a

# Clean up all unused Docker resources
docker system prune -a --volumes

# View disk usage
docker system df
```

---

## 🔄 Updating the Application

### Standard Update Process

```bash
# On your local machine
git add .
git commit -m "Update XYZ"
git push origin main

# On EC2
cd ~/Genie_AI_Backend
git pull origin main
./deploy.sh
```

### Quick Restart (no rebuild)

```bash
docker-compose restart
```

### Full Rebuild (after code changes)

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔒 Security Notes

### ⚠️ IMPORTANT: Rotate These Credentials

The credentials in this README are now **publicly exposed** on GitHub. You should:

1. **Rotate AWS credentials:**
   - Go to AWS IAM Console
   - Delete old access key: `AKIATG6YACNIW52IJPX6`
   - Create new access key
   - Update `.env` file

2. **Change JWT secret:**
   ```env
   JWT_SECRET=<generate-new-random-string>
   ```

3. **Change admin password:**
   ```env
   ADMIN_PASSWORD=<new-secure-password>
   ```

4. **Add .env to .gitignore:**
   ```bash
   echo ".env" >> .gitignore
   git add .gitignore
   git commit -m "Prevent .env from being committed"
   ```

---

## 📈 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-22T10:30:00",
  "database": "connected",
  "models_loaded": true
}
```

### Performance Monitoring

```bash
# View container resource usage
docker stats gardengenie-backend

# View detailed logs
docker-compose logs --tail=100 -f
```

---

## 🆘 Getting Help

If deployment fails:

1. Check logs: `docker-compose logs`
2. Verify .env file has all required variables
3. Ensure OPENAI_API_KEY is valid
4. Check database connectivity
5. Verify AWS S3 credentials

Common log patterns to search for:
- `ERROR` - Application errors
- `ConnectionError` - Database/API connection issues
- `KeyError` - Missing environment variables
- `ImportError` - Missing dependencies

---

## ✅ Post-Deployment Checklist

- [ ] Container is running: `docker ps`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Products endpoint works: `curl http://localhost:8000/products/`
- [ ] Can access API docs: `http://<EC2_IP>:8000/docs`
- [ ] Logs show no errors: `docker-compose logs --tail=50`
- [ ] All environment variables set correctly
- [ ] AWS credentials rotated (security)
- [ ] Monitoring set up
