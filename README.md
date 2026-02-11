# 💰 MyStack

A Flask-based web application for tracking precious metals, coins, and goldbacks with real-time price updates and comprehensive analytics.

## ✨ Features

- **Track Multiple Asset Types**: Manage metals, coins, and goldbacks
- **Real-Time Pricing**: Automatic gold and silver price updates
- **Visual Analytics**: Interactive charts showing portfolio breakdown and value
- **Image Management**: Upload and display images for each item
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Secure Authentication**: Password-protected access
- **Docker Support**: Easy deployment with Docker Compose

## 🚀 Quick Start with Docker

### Prerequisites
- Docker
- Docker Compose

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/mystack.git
cd mystack
```

2. **Create environment file:**
```bash
cp .env.example .env
```

3. **Edit `.env` and set your credentials:**
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env file
nano .env
```

Update these values:
- `SECRET_KEY`: Use the generated key above
- `ADMIN_USERNAME`: Your desired username
- `ADMIN_PASSWORD`: Your secure password

4. **Start the application:**
```bash
docker-compose up -d
```

5. **Access the application:**
Open your browser and navigate to `http://localhost:5000`

Login with the credentials you set in `.env`

### Stopping the Application

```bash
docker-compose down
```

### Viewing Logs

```bash
docker-compose logs -f
```

## 🛠️ Manual Installation (Without Docker)

### Prerequisites
- Python 3.9+
- pip

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/mystack.git
cd mystack
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set environment variables:**
```bash
export SECRET_KEY="your-secret-key-here"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-password-here"
```

5. **Run the application:**
```bash
python app.py
```

6. **Access at:** `http://localhost:5000`

## 📁 Project Structure

```
mystack/
├── app.py                 # Main Flask application
├── price_fetcher.py       # Price update service
├── templates/             # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── metals.html
│   ├── coins.html
│   ├── goldbacks.html
│   └── login.html
├── static/               
│   ├── css/
│   │   └── style.css     # Application styles
│   ├── js/
│   │   └── app.js        # Frontend JavaScript
│   └── images/           # Uploaded images (gitignored)
│       ├── metals/
│       ├── coins/
│       └── goldbacks/
├── data/                 # Database (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔐 Security

### Important Security Notes

1. **Never commit `.env` to Git** - it contains sensitive credentials
2. **Change default credentials** immediately after first deployment
3. **Use strong passwords** - minimum 12 characters with mixed case, numbers, and symbols
4. **Use HTTPS in production** - consider using a reverse proxy like nginx with Let's Encrypt
5. **Keep dependencies updated** - regularly run `pip install --upgrade -r requirements.txt`

### Generating a Secure Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 📊 Features Overview

### Dashboard
- Portfolio allocation donut chart
- Top items by worth (Coins and Goldbacks)
- Value breakdown charts (Gold vs Silver)
- Overall portfolio statistics

### Metals
- Track gold and silver in various forms (bars, rounds, coins)
- Automatic value calculation based on live prices
- Weight tracking in troy ounces

### Coins
- Detailed coin information (country, year, denomination)
- KM catalog number integration
- Gain/loss tracking

### Goldbacks
- State-specific goldback tracking
- Denomination tracking (1, 5, 10, 25, 50, 100, 1000)
- Alpha and serial number recording

## 🔄 Automatic Price Updates

The application automatically fetches current gold and silver prices every 5 minutes from reliable market APIs. Manual refresh is available via the dashboard.

## 💾 Data Persistence

- **Database**: SQLite database stored in `data/precious_metals.db`
- **Images**: Stored in `static/images/` subdirectories
- **Docker Volumes**: Both database and images persist across container restarts

## 🐛 Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Permission Issues
If you encounter permission issues with volumes:
```bash
sudo chown -R $USER:$USER data/ static/images/
```

### Database Locked
If you see "database is locked" errors:
```bash
docker-compose restart
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Gold price data from various market APIs
- Built with Flask, SQLAlchemy, and Chart.js
- Icons and UI inspired by modern design principles

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This application is for personal portfolio tracking only. Price data is for informational purposes and should not be used for trading decisions. Always verify current market prices before making financial decisions.

## 📦 Automated Docker Builds

This repository is configured with GitHub Actions to automatically build and publish Docker images.

### How it Works

1. **Push to GitHub**: Every push to `main` triggers an automated build
2. **Docker Image**: Built and pushed to GitHub Container Registry (ghcr.io)
3. **Deploy Anywhere**: Pull and run the pre-built image on any server

### Using Pre-built Images

```bash
# Pull the latest image
docker pull ghcr.io/YOUR_USERNAME/mystack:latest

# Or use docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.
