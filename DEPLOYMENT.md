# Deployment Guide

## Pre-requisites
1. EC2 instance with Docker and Docker Compose installed
2. Neon PostgreSQL database configured
3. AWS S3 bucket created with proper permissions
4. Domain name (if using HTTPS)

## Deployment Steps

1. Clone the repository:
```bash
git clone https://github.com/Maitrii-Infotech/Genie_AI_Backend.git
cd Genie_AI_Backend
```

2. Set up environment variables:
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your production values
nano .env
```

3. Build and start the containers:
```bash
# For first time deployment
docker-compose -f docker-compose.prod.yml up --build -d

# For subsequent updates
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d
```

4. Verify the application:
```bash
# Check container status
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f app
```

## Important Notes

1. Database:
   - Ensure the Neon database URL in .env is correct
   - The database should be initialized with the product data

2. File Storage:
   - The /uploads directory is mounted as a volume
   - For production, configure S3 properly in .env

3. Security:
   - Update JWT_SECRET to a strong random value
   - Ensure all sensitive environment variables are properly set
   - Consider using AWS Secrets Manager for sensitive data

4. Monitoring:
   - Set up CloudWatch or similar monitoring
   - Configure proper logging
   - Set up alerts for critical errors

## Troubleshooting

1. If the application fails to start:
   - Check docker logs: `docker-compose -f docker-compose.prod.yml logs app`
   - Verify environment variables are set correctly
   - Check database connectivity
   - Verify S3 permissions

2. If products don't appear:
   - Check database connection string
   - Verify product data is imported
   - Check application logs for SQL errors

3. If image upload fails:
   - Verify S3 credentials and permissions
   - Check upload directory permissions
   - Verify network connectivity to S3

## Maintenance

1. Database Backups:
   - Neon handles automated backups
   - Consider additional backup strategies

2. Monitoring:
   - Set up CPU/Memory monitoring
   - Configure disk space alerts
   - Monitor application errors

3. Updates:
   - Regular security updates
   - Dependency updates
   - Database maintenance