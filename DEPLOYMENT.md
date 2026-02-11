# MyStack Deployment Guide

## Quick Start Options

### Option 1: Build Locally with Docker Compose (Recommended for Testing)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/mystack.git
cd mystack

# Create .env file
cp .env.example .env
nano .env  # Edit with your credentials

# Build and run
docker-compose up -d

# Access at http://localhost:5000
```

### Option 2: Use Pre-built Image from GitHub (Recommended for Production)

GitHub Actions automatically builds and publishes Docker images when you push to the main branch.

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/mystack.git
cd mystack

# Create .env file
cp .env.example .env
nano .env  # Edit with your credentials

# Edit docker-compose.prod.yml and replace YOUR_GITHUB_USERNAME

# Pull and run the pre-built image
docker-compose -f docker-compose.prod.yml up -d

# Access at http://localhost:5000
```

## GitHub Setup

### 1. Enable GitHub Container Registry

Your repository is automatically configured to push Docker images to GitHub Container Registry (ghcr.io).

### 2. Make Package Public (Optional)

After the first build:
1. Go to your GitHub profile → Packages
2. Find the `mystack` package
3. Click on it → Package settings
4. Change visibility to "Public" (so you don't need authentication to pull)

### 3. GitHub Actions Workflow

The `.github/workflows/docker-build.yml` file automatically:
- Builds Docker image on every push to main/master
- Tags images with branch name, commit SHA, and version tags
- Pushes to `ghcr.io/YOUR_USERNAME/mystack`

## Environment Variables

Required in `.env` file:

```bash
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Image Tags

GitHub Actions creates these tags:
- `latest` - Latest build from main branch
- `main` - Latest from main branch
- `sha-abc123` - Specific commit
- `v1.0.0` - Version tags (if you create GitHub releases)

## Production Deployment

### On a VPS/Server:

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone your repository
git clone https://github.com/YOUR_USERNAME/mystack.git
cd mystack

# Setup environment
cp .env.example .env
nano .env

# Edit docker-compose.prod.yml with your GitHub username

# Start the service
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop the service
docker-compose -f docker-compose.prod.yml down
```

### With Reverse Proxy (HTTPS with nginx):

1. Install nginx and certbot:
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

2. Configure nginx (`/etc/nginx/sites-available/mystack`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Enable and get SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/mystack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d yourdomain.com
```

## Updating

### Using Pre-built Image:
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Building Locally:
```bash
git pull
docker-compose up -d --build
```

## Backup

### Database and Images:
```bash
# Backup
tar -czf mystack-backup-$(date +%Y%m%d).tar.gz data/ static/images/

# Restore
tar -xzf mystack-backup-YYYYMMDD.tar.gz
```

## Troubleshooting

### View Logs:
```bash
docker-compose logs -f
```

### Restart Container:
```bash
docker-compose restart
```

### Rebuild Image:
```bash
docker-compose up -d --build
```

### Check Container Status:
```bash
docker-compose ps
```

### Access Container Shell:
```bash
docker-compose exec mystack /bin/bash
```

## Security Checklist

- [ ] Change default admin password in `.env`
- [ ] Use a strong SECRET_KEY (32+ characters)
- [ ] Keep `.env` file secure (never commit to git)
- [ ] Use HTTPS in production (with nginx + Let's Encrypt)
- [ ] Regularly update dependencies: `docker-compose pull`
- [ ] Backup data regularly
- [ ] Restrict port 5000 access (use nginx reverse proxy)
- [ ] Keep Docker and system packages updated

## Support

For issues or questions, please open an issue on GitHub.
