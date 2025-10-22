# Deployment Guide for Coolify

This guide explains how to deploy the Job Tracker application to Coolify.

## Prerequisites

- A Coolify instance (self-hosted or cloud)
- GitHub repository connected to Coolify
- Domain name (optional, but recommended)

## Deployment Steps

### 1. Create New Application in Coolify

1. Log in to your Coolify dashboard
2. Click "New Resource" → "Docker Compose"
3. Connect your GitHub repository: `zmikicdroin/tracker-posl`
4. Select the `main` branch

### 2. Configure Environment Variables

In Coolify's environment variables section, add:

```
SECRET_KEY=your-very-long-random-secret-key-here
FLASK_ENV=production
```

**Important:** Generate a secure SECRET_KEY using:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Configure Domains

**Option A: Single Domain (Recommended)**
- Assign your domain (e.g., `tracker.yourdomain.com`) to the **frontend** service
- The backend will be accessed via `/api` proxy through nginx

**Option B: Separate Domains**
- Frontend: `tracker.yourdomain.com`
- Backend: `api.tracker.yourdomain.com`

### 4. Volume Configuration

Coolify will automatically handle the following volumes:
- `backend-data`: Stores uploaded CV files
- `database-data`: Stores SQLite database

**Important:** These volumes persist data across container restarts and redeployments.

### 5. Deploy

1. Click "Deploy" in Coolify
2. Wait for the build and deployment to complete
3. Check the logs for any errors

### 6. Verify Deployment

1. Visit your frontend domain
2. Try registering a new user
3. Test creating a job application
4. Verify file uploads work

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (Port 80)     │
│   Nginx + React │
└────────┬────────┘
         │
         │ /api → proxy
         │
┌────────▼────────┐
│   Backend       │
│   (Port 5000)   │
│   Flask API     │
└────────┬────────┘
         │
         │
    ┌────▼─────┐
    │ SQLite   │
    │ Database │
    └──────────┘
```

## Configuration Files

- `docker-compose.yml` - Main orchestration file
- `backend/Dockerfile` - Backend container configuration
- `frontend/Dockerfile` - Frontend container configuration
- `frontend/nginx.conf` - Nginx reverse proxy configuration
- `.env.example` - Environment variables template

## Troubleshooting

### Backend not accessible
- Check if backend container is running: View logs in Coolify
- Verify environment variables are set correctly
- Check SECRET_KEY is configured

### Database not persisting
- Ensure `database-data` volume is mounted
- Check volume permissions

### File uploads failing
- Verify `backend-data` volume is mounted
- Check disk space on your server
- Ensure upload directory has write permissions

### CORS errors
- Verify nginx proxy configuration is correct
- Check backend CORS settings in `app.py`

## Updating the Application

Coolify supports automatic deployments:

1. **Automatic**: Enable "Auto Deploy" in Coolify settings
   - Pushes to `main` branch will trigger automatic deployment

2. **Manual**: Click "Redeploy" button in Coolify dashboard

## Backup Strategy

### Database Backup
```bash
docker cp tracker-backend:/app/jobtracker.db ./backup/
```

### Uploaded Files Backup
```bash
docker cp tracker-backend:/app/uploads ./backup/
```

### Using Coolify Backups
- Coolify can automatically backup volumes
- Configure in Settings → Backups

## Security Recommendations

1. **Change SECRET_KEY**: Never use the default secret key
2. **Use HTTPS**: Configure SSL/TLS in Coolify
3. **Regular Backups**: Enable automatic backups
4. **Update Dependencies**: Regularly update packages
5. **Monitor Logs**: Check application logs regularly

## Performance Optimization

1. **Database**: Consider migrating to PostgreSQL for better performance
2. **File Storage**: Use object storage (S3, MinIO) for uploaded files
3. **Caching**: Add Redis for session management
4. **CDN**: Use a CDN for static assets

## Support

For issues specific to:
- **Application**: Open an issue on GitHub
- **Coolify**: Check Coolify documentation or Discord
- **Deployment**: Review logs in Coolify dashboard
