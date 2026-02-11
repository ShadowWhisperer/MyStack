# 🚀 MyStack - Quick Start Guide

## Upload to GitHub

1. **Extract the zip file** to a folder
2. **Create a new repository** on GitHub named `mystack`
3. **Upload files:**

```bash
cd mystack
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mystack.git
git push -u origin main
```

## GitHub Actions Will Automatically:

✅ Build Docker image  
✅ Push to GitHub Container Registry (ghcr.io)  
✅ Tag as `latest`, `main`, and commit SHA  

## Deploy the Container

### Method 1: Build Locally

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/mystack.git
cd mystack

# Setup credentials
cp .env.example .env
nano .env  # Add your username and password

# Start
docker-compose up -d

# Access at http://localhost:5000
```

### Method 2: Use Pre-built Image from GitHub

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/mystack.git
cd mystack

# Setup credentials
cp .env.example .env
nano .env

# Edit docker-compose.prod.yml - replace YOUR_GITHUB_USERNAME

# Start with pre-built image
docker-compose -f docker-compose.prod.yml up -d

# Access at http://localhost:5000
```

## Make Package Public (Optional)

After first build:
1. Go to your GitHub profile → Packages
2. Find `mystack` package
3. Package settings → Change to Public
4. Now anyone can pull without authentication!

## Default Credentials

- **Username**: `admin`
- **Password**: `changeme123`

⚠️ **Change these immediately in your `.env` file!**

## Files Included

```
mystack/
├── .github/
│   └── workflows/
│       └── docker-build.yml      # Auto-build Docker images
├── templates/                     # HTML templates
├── static/                        # CSS, JS, images
├── app.py                        # Main application
├── price_fetcher.py              # Price updates
├── Dockerfile                    # Docker build instructions
├── docker-compose.yml            # Local build
├── docker-compose.prod.yml       # Use pre-built image
├── requirements.txt              # Python dependencies
├── .env.example                  # Credentials template
├── .gitignore                    # Git ignore rules
├── README.md                     # Full documentation
├── DEPLOYMENT.md                 # Deployment guide
└── QUICKSTART.md                 # This file
```

## Next Steps

1. ✅ Upload to GitHub
2. ✅ Wait for Actions to build (check Actions tab)
3. ✅ Deploy using Method 1 or 2
4. ✅ Login and start tracking!

## Need Help?

- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
- See [README.md](README.md) for features and usage
- Open an issue on GitHub

---

**Enjoy tracking your precious metals! 💰**
