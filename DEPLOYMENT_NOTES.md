# Deployment Configuration

## Server Setup (AWS EC2)

### Nginx Configuration

**Issue Fixed:** HTTP 413 "Payload Too Large" error when uploading phone images

**Solution:** Increase Nginx upload limit

**File Modified:** `/etc/nginx/sites-available/default` (or `/etc/nginx/nginx.conf`)

**Change Made:**
```nginx
server {
    # Add this line
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Commands to Apply:**
```bash
sudo nano /etc/nginx/sites-available/default
# Add: client_max_body_size 20M;
sudo nginx -t
sudo systemctl reload nginx
```

**Date:** October 28, 2025
**Fixed By:** Backend Team
**Status:** ✅ Deployed and Working

---

## Application Details

- **Backend:** FastAPI
- **Port:** 8000
- **Database:** PostgreSQL (Neon)
- **File Storage:** AWS S3
- **Reverse Proxy:** Nginx
- **Max Upload Size:** 20MB per file

