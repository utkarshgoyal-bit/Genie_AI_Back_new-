# Nginx Configuration Files

## Deployment
Copy this file to the server:
```bash
sudo cp nginx/default /etc/nginx/sites-available/default
sudo nginx -t
sudo systemctl reload nginx
```

## Key Settings
- `client_max_body_size 20M;` - Allows large image uploads
