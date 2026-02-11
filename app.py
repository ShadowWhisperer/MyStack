from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import threading
import time
from price_fetcher import price_fetcher
import os
from werkzeug.utils import secure_filename
import uuid
from functools import wraps

# Disable __pycache__ creation (only works if set before Python starts - use run.sh)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

app = Flask(__name__)

# Secret key for sessions (from environment variable or default for dev)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Authentication credentials from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')

# Save database in data directory (for Docker volume)
basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "precious_metals.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# No max file size limit

# Create upload directories if they don't exist
for category in ['metals', 'coins', 'goldbacks']:
    os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)

db = SQLAlchemy(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Custom Jinja filter to remove trailing zeros
@app.template_filter('trim_zeros')
def trim_zeros(value):
    """Remove trailing zeros from decimal numbers (max 2 decimal places)"""
    if value is None:
        return '0'
    # Format with max 2 decimals, then strip trailing zeros
    formatted = f'{value:,.2f}'
    # Remove trailing zeros after decimal point
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    return formatted

@app.template_filter('format_percent')
def format_percent(value):
    """Format percentage: no decimals if >= 100%, otherwise show decimals"""
    if value is None:
        return '0'
    # If 100% or more, show no decimals
    if abs(value) >= 100:
        return f'{int(value):,}'
    # Otherwise use trim_zeros logic
    formatted = f'{value:.2f}'
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    return formatted

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload_file(file, category='metals'):
    """Save uploaded file and return the relative path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Save to category folder
        filepath = os.path.join(UPLOAD_FOLDER, category, filename)
        file.save(filepath)
        
        # Return relative path for database
        return f"{category}/{filename}"
    return None

# Background task for updating metal prices
def update_prices_periodically():
    """Background thread to update metal prices every 30 minutes"""
    # Fetch prices immediately on first run
    try:
        print("[PRICES] Fetching initial prices...")
        start = time.time()
        price_fetcher.fetch_all_prices()
        print(f"[PRICES] Initial fetch completed in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"[PRICES] Error on initial fetch: {e}")
    
    while True:
        # Wait 30 minutes (1800 seconds)
        time.sleep(1800)
        
        try:
            print("[PRICES] Updating prices...")
            price_fetcher.fetch_all_prices()
        except Exception as e:
            print(f"[PRICES] Error updating prices: {e}")

# Start background thread
def start_price_updater():
    """Start the price update background thread"""
    # Start background thread (will fetch immediately, then every 30 min)
    thread = threading.Thread(target=update_prices_periodically, daemon=True)
    thread.start()
    print("[PRICES] Price updater thread started (non-blocking)")

# Models
class Metal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metal = db.Column(db.String(50), nullable=False)  # Gold, Silver, Copper
    form = db.Column(db.String(50), nullable=False)  # Bar, Round, Coin, Other
    count = db.Column(db.Integer, default=1)
    weight_oz = db.Column(db.Float, nullable=False)
    purity = db.Column(db.String(20), nullable=False)  # .999, .9999, etc.
    year = db.Column(db.String(10))  # Year
    total_cost = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0.0)
    brand = db.Column(db.String(50))  # Brand name
    notes = db.Column(db.Text)
    image_filename = db.Column(db.String(255))  # Image filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def weight_display(self):
        """Convert decimal weight to fraction for common values"""
        if not self.weight_oz:
            return '-'
        
        # Common fraction mappings
        fractions = {
            0.005: '1/200',
            0.01: '1/100',
            0.02: '1/50',
            0.05: '1/20',
            0.1: '1/10',
            0.25: '1/4',
            0.5: '1/2'
        }
        
        # Check if weight matches a common fraction (with small tolerance for float precision)
        for decimal, fraction in fractions.items():
            if abs(self.weight_oz - decimal) < 0.0001:
                return fraction
        
        # For whole numbers, display without decimals
        if self.weight_oz == int(self.weight_oz):
            return str(int(self.weight_oz))
        
        # For other decimals, use trim_zeros equivalent
        formatted = f'{self.weight_oz:.6f}'.rstrip('0').rstrip('.')
        return formatted
    
    @property
    def gain_loss(self):
        return self.current_value - self.total_cost
    
    @property
    def gain_loss_percent(self):
        if self.total_cost == 0 or self.total_cost is None:
            return 0.0
        return ((self.current_value - self.total_cost) / self.total_cost) * 100

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.String(50))  # Gold, Silver, Copper, etc.
    country = db.Column(db.String(100))  # Country of origin
    year = db.Column(db.String(10))  # Year
    weight = db.Column(db.String(50))  # Weight (any format)
    denomination = db.Column(db.String(50))  # Face value/denomination
    quantity = db.Column(db.Integer, default=1)
    total_cost = db.Column(db.Float, default=0.0)
    worth = db.Column(db.Float, default=0.0)  # Current worth
    worth_updated = db.Column(db.String(50))  # When worth was last updated
    km = db.Column(db.String(50))  # KM catalog number (e.g., "131")
    km_url = db.Column(db.String(500))  # URL to numista or other reference
    notes = db.Column(db.Text)
    image_filename = db.Column(db.String(255))  # Image filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def gain_loss(self):
        return self.worth - self.total_cost

class Goldback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(50))  # State
    denomination = db.Column(db.Float)  # Can be 1, 5, 10, 25, 50, 0.5, 0.25, etc.
    year = db.Column(db.String(10))  # Year
    count = db.Column(db.Integer, default=1)
    alpha = db.Column(db.String(10), default='No')  # Yes/No
    serial = db.Column(db.String(100))  # Serial number
    cost = db.Column(db.Float, default=0.0)
    circulated = db.Column(db.String(10), default='No')  # Yes/No
    notes = db.Column(db.Text)
    image_filename = db.Column(db.String(255))  # Image filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def gb_total(self):
        """Total goldbacks for this entry (denomination × count)"""
        if self.denomination:
            return self.denomination * self.count
        return 0.0
    
    @property
    def denomination_display(self):
        """Convert decimal to fraction for display"""
        if self.denomination == 0.5:
            return '1/2'
        elif self.denomination == 0.25:
            return '1/4'
        elif self.denomination and self.denomination == int(self.denomination):
            return str(int(self.denomination))
        else:
            return str(self.denomination) if self.denomination else '-'
    
    @property
    def worth(self):
        """Calculate worth based on current gold price with 2x premium
        Formula: (denomination / 1000) × gold_price × 2 × count
        Each Goldback contains denomination/1000 oz of gold
        Premium multiplier of 2x reflects market pricing
        """
        if self.denomination:
            # Get current gold price
            gold_price = price_fetcher.get_price('gold')
            if gold_price:
                # Gold content in oz: denomination / 1000
                # Market value: spot × 2 (100% premium)
                gold_content_oz = self.denomination / 1000.0
                return gold_content_oz * gold_price * 2.0 * self.count
            return 0.0
        return 0.0
    
    @property
    def gain_loss(self):
        return self.worth - self.cost

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get all data
    metals_list = Metal.query.all()
    coins_list = Coin.query.all()
    goldbacks_list = Goldback.query.all()
    
    # Calculate individual category stats
    metals_cost = sum(m.total_cost for m in metals_list)
    metals_value = sum(m.current_value for m in metals_list)
    metals_gain = metals_value - metals_cost
    
    coins_cost = sum(c.total_cost for c in coins_list)
    coins_value = sum(c.worth for c in coins_list)
    coins_gain = coins_value - coins_cost
    
    goldbacks_cost = sum(g.cost for g in goldbacks_list)
    goldbacks_value = sum(g.worth for g in goldbacks_list)
    goldbacks_gain = goldbacks_value - goldbacks_cost
    goldbacks_total_gb = sum(g.gb_total for g in goldbacks_list)
    
    # Calculate overall totals
    total_cost = metals_cost + coins_cost + goldbacks_cost
    total_value = metals_value + coins_value + goldbacks_value
    total_gain = total_value - total_cost
    total_gain_percent = ((total_gain / total_cost) * 100) if total_cost > 0 else 0
    
    # Overall stats
    overall_stats = {
        'cost_basis': total_cost,
        'current_value': total_value,
        'gain_loss': total_gain,
        'gain_loss_percent': total_gain_percent
    }
    
    # Category breakdowns (as list for sorting)
    categories = [
        {
            'key': 'coins',
            'name': 'Coins',
            'count': len(coins_list),
            'cost': coins_cost,
            'value': coins_value,
            'gain': coins_gain,
            'gain_percent': ((coins_gain / coins_cost) * 100) if coins_cost > 0 else 0
        },
        {
            'key': 'goldbacks',
            'name': 'Goldbacks',
            'count': len(goldbacks_list),
            'cost': goldbacks_cost,
            'value': goldbacks_value,
            'gain': goldbacks_gain,
            'gain_percent': ((goldbacks_gain / goldbacks_cost) * 100) if goldbacks_cost > 0 else 0,
            'gb_total': goldbacks_total_gb,
            'total_oz': sum((g.denomination / 1000.0) * g.count for g in goldbacks_list if g.denomination)
        },
        {
            'key': 'metals',
            'name': 'Metals',
            'count': len(metals_list),
            'cost': metals_cost,
            'value': metals_value,
            'gain': metals_gain,
            'gain_percent': ((metals_gain / metals_cost) * 100) if metals_cost > 0 else 0,
            'total_oz': sum((m.weight_oz or 0) * (m.count or 0) for m in metals_list),
            'gold_oz': sum((m.weight_oz or 0) * (m.count or 0) for m in metals_list if m.metal and m.metal.lower() == 'gold'),
            'silver_oz': sum((m.weight_oz or 0) * (m.count or 0) for m in metals_list if m.metal and m.metal.lower() == 'silver')
        }
    ]
    
    # Sort alphabetically by name
    categories.sort(key=lambda x: x['name'])
    
    # Calculate Gold vs Silver breakdown
    gold_value = 0.0
    gold_oz = 0.0
    silver_value = 0.0
    silver_oz = 0.0
    
    # Metals-only tracking
    gold_value_metals_only = 0.0
    gold_oz_metals_only = 0.0
    silver_value_metals_only = 0.0
    silver_oz_metals_only = 0.0
    
    # From Metals table
    for metal in metals_list:
        if metal.metal and metal.metal.lower() == 'gold':
            gold_value += metal.current_value
            gold_oz += (metal.weight_oz * metal.count) if metal.weight_oz else 0
            gold_value_metals_only += metal.current_value
            gold_oz_metals_only += (metal.weight_oz * metal.count) if metal.weight_oz else 0
        elif metal.metal and metal.metal.lower() == 'silver':
            silver_value += metal.current_value
            silver_oz += (metal.weight_oz * metal.count) if metal.weight_oz else 0
            silver_value_metals_only += metal.current_value
            silver_oz_metals_only += (metal.weight_oz * metal.count) if metal.weight_oz else 0
    
    # From Coins table (if material is specified)
    for coin in coins_list:
        if coin.material and coin.material.lower() == 'gold':
            gold_value += coin.worth
            # Coins don't have standardized oz weight, so we skip oz calculation
        elif coin.material and coin.material.lower() == 'silver':
            silver_value += coin.worth
    
    # From Goldbacks (all gold-based)
    for goldback in goldbacks_list:
        gold_value += goldback.worth
        # Each Goldback contains denomination/1000 oz of gold
        if goldback.denomination:
            gold_oz += (goldback.denomination / 1000.0) * goldback.count
    
    metal_breakdown = {
        'gold_value': gold_value,
        'gold_oz': gold_oz,
        'silver_value': silver_value,
        'silver_oz': silver_oz,
        'gold_value_metals_only': gold_value_metals_only,
        'gold_oz_metals_only': gold_oz_metals_only,
        'silver_value_metals_only': silver_value_metals_only,
        'silver_oz_metals_only': silver_oz_metals_only
    }
    
    # Calculate form breakdown for metals only
    form_breakdown = {}
    for metal in metals_list:
        form = metal.form if metal.form else 'Other'
        if form not in form_breakdown:
            form_breakdown[form] = 0
        form_breakdown[form] += (metal.weight_oz or 0) * (metal.count or 1)
    
    # Get top worth items for each category
    top_coins = sorted(coins_list, key=lambda x: x.worth, reverse=True)[:10]
    top_goldbacks = sorted(goldbacks_list, key=lambda x: x.worth, reverse=True)[:10]
    top_metals = sorted(metals_list, key=lambda x: x.current_value, reverse=True)[:10]
    
    return render_template('dashboard.html', 
                         active_page='dashboard',
                         overall_stats=overall_stats,
                         categories=categories,
                         metal_breakdown=metal_breakdown,
                         form_breakdown=form_breakdown,
                         top_coins=top_coins,
                         top_goldbacks=top_goldbacks,
                         top_metals=top_metals)

@app.route('/coins')
@login_required
def coins():
    coins_list = Coin.query.all()
    
    # Sort by country (A-Z) then by year
    coins_list.sort(key=lambda c: (c.country or '', c.year or ''))
    
    # Calculate stats
    total_cost = sum(c.total_cost for c in coins_list)
    total_worth = sum(c.worth for c in coins_list)
    total_gain_loss = total_worth - total_cost
    total_gain_loss_percent = ((total_gain_loss / total_cost) * 100) if total_cost > 0 else 0
    
    stats = {
        'cost_basis': total_cost,
        'current_value': total_worth,
        'gain_loss': total_gain_loss,
        'gain_loss_percent': total_gain_loss_percent
    }
    
    return render_template('coins.html', active_page='coins', coins=coins_list, stats=stats)

@app.route('/goldbacks')
@login_required
def goldbacks():
    goldbacks_list = Goldback.query.all()
    
    # Sort by state (A-Z) then by denomination (ascending)
    goldbacks_list.sort(key=lambda g: (g.state or '', g.denomination or 0))
    
    # Calculate stats
    total_cost = sum(g.cost for g in goldbacks_list)
    total_worth = sum(g.worth for g in goldbacks_list)
    total_gb = sum(g.gb_total for g in goldbacks_list)  # Total goldbacks (denomination × count)
    total_gain_loss = total_worth - total_cost
    total_gain_loss_percent = ((total_gain_loss / total_cost) * 100) if total_cost > 0 else 0
    
    # Calculate GB rate (current value per 1 goldback)
    # Using gold price: (1/1000 oz) × gold_price × 2
    gold_price = price_fetcher.get_price('gold')
    gb_rate = (gold_price / 1000.0 * 2.0) if gold_price else 0.0
    
    stats = {
        'cost_basis': total_cost,
        'gb_total': total_gb,
        'gb_rate': gb_rate,
        'current_value': total_worth,
        'gain_loss': total_gain_loss,
        'gain_loss_percent': total_gain_loss_percent
    }
    
    return render_template('goldbacks.html', active_page='goldbacks', goldbacks=goldbacks_list, stats=stats)

@app.route('/metals')
@login_required
def metals():
    metals_list = Metal.query.all()
    
    # Custom sort: Metal (Gold first, then Silver), then Form (A-Z), then Weight (ascending), then Quantity (descending)
    def metal_sort_key(m):
        # Metal priority: Gold=0, Silver=1, others=2
        metal_priority = 0 if m.metal == 'Gold' else (1 if m.metal == 'Silver' else 2)
        # Negate count for descending order (high to low)
        return (metal_priority, m.form or '', m.weight_oz or 0, -(m.count or 0))
    
    metals_list.sort(key=metal_sort_key)
    
    # Calculate stats
    total_cost = sum(m.total_cost for m in metals_list)
    total_current_value = sum(m.current_value for m in metals_list)
    total_gain_loss = total_current_value - total_cost
    total_gain_loss_percent = ((total_gain_loss / total_cost) * 100) if total_cost > 0 else 0
    
    stats = {
        'cost_basis': total_cost,
        'current_value': total_current_value,
        'gain_loss': total_gain_loss,
        'gain_loss_percent': total_gain_loss_percent
    }
    
    return render_template('metals.html', 
                         active_page='metals', 
                         metals=metals_list,
                         stats=stats)

# API endpoints for CRUD operations
@login_required
@app.route('/api/metals', methods=['GET'])
@login_required
def get_metals():
    metals_list = Metal.query.all()
    return jsonify([{
        'id': m.id,
        'metal': m.metal,
        'form': m.form,
        'count': m.count,
        'weight_oz': m.weight_oz,
        'purity': m.purity,
        'year': m.year,
        'total_cost': m.total_cost,
        'current_value': m.current_value,
        'gain_loss': m.gain_loss,
        'brand': m.brand,
        'notes': m.notes,
        'image_filename': m.image_filename
    } for m in metals_list])

@login_required
@app.route('/api/metals', methods=['POST'])
@login_required
def add_metal():
    try:
        # Handle file upload if present
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image_filename = save_upload_file(file, 'metals')
        
        # Get form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            data['count'] = int(data.get('count', 1))
            data['weight_oz'] = parse_weight(data.get('weight_oz', '1'))
            data['total_cost'] = float(data['total_cost'])
            data['current_value'] = float(data.get('current_value', 0))
        else:
            data = request.json
            if 'weight_oz' in data:
                data['weight_oz'] = parse_weight(data['weight_oz'])
        
        new_metal = Metal(
            metal=data['metal'],
            form=data['form'],
            count=data.get('count', 1),
            weight_oz=data['weight_oz'],
            purity=data['purity'],
            year=data.get('year', ''),
            total_cost=data['total_cost'],
            current_value=data.get('current_value', 0),
            brand=data.get('brand', ''),
            notes=data.get('notes', ''),
            image_filename=image_filename
        )
        db.session.add(new_metal)
        db.session.commit()
        return jsonify({'success': True, 'id': new_metal.id}), 201
    
    except Exception as e:
        print(f"Error adding metal: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@login_required
@app.route('/api/metals/<int:id>', methods=['PUT'])
def update_metal(id):
    metal = Metal.query.get_or_404(id)
    data = request.json
    
    metal.metal = data.get('metal', metal.metal)
    metal.form = data.get('form', metal.form)
    metal.count = data.get('count', metal.count)
    if 'weight_oz' in data:
        metal.weight_oz = parse_weight(data['weight_oz'])
    metal.purity = data.get('purity', metal.purity)
    metal.year = data.get('year', metal.year)
    metal.total_cost = data.get('total_cost', metal.total_cost)
    metal.current_value = data.get('current_value', metal.current_value)
    metal.brand = data.get('brand', metal.brand)
    metal.notes = data.get('notes', metal.notes)
    
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/metals/<int:id>', methods=['DELETE'])
def delete_metal(id):
    metal = Metal.query.get_or_404(id)
    
    # Delete associated image file if it exists
    if metal.image_filename:
        image_path = os.path.join(UPLOAD_FOLDER, metal.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(metal)
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/metals/<int:id>/image', methods=['POST'])
def upload_metal_image(id):
    """Upload or replace image for existing metal entry"""
    try:
        metal = Metal.query.get_or_404(id)
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Delete old image if exists
        if metal.image_filename:
            old_path = os.path.join(UPLOAD_FOLDER, metal.image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Save new image
        image_filename = save_upload_file(file, 'metals')
        if not image_filename:
            return jsonify({'success': False, 'error': 'Failed to save image'}), 400
        
        metal.image_filename = image_filename
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error uploading image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Goldbacks API Endpoints
@login_required
@app.route('/api/goldbacks', methods=['GET'])
def get_goldbacks():
    goldbacks_list = Goldback.query.all()
    return jsonify([{
        'id': g.id,
        'state': g.state,
        'denomination': g.denomination,
        'year': g.year,
        'count': g.count,
        'alpha': g.alpha,
        'serial': g.serial,
        'cost': g.cost,
        'worth': g.worth,
        'gain_loss': g.gain_loss,
        'circulated': g.circulated,
        'notes': g.notes,
        'image_filename': g.image_filename
    } for g in goldbacks_list])

def parse_weight(value):
    """Convert fraction strings like '1/200', '1/100' to decimals for weight"""
    if not value or value == '':
        return 1.0
    
    value_str = str(value).strip()
    
    # Check for fractions
    if '/' in value_str:
        try:
            parts = value_str.split('/')
            return float(parts[0]) / float(parts[1])
        except:
            return float(value_str)
    else:
        try:
            return float(value_str)
        except:
            return 1.0

def parse_denomination(value):
    """Convert fraction strings like '1/2', '1/4' to decimals"""
    if not value or value == '':
        return 1.0
    
    value_str = str(value).strip()
    
    # Check for fractions
    if value_str == '1/2':
        return 0.5
    elif value_str == '1/4':
        return 0.25
    elif '/' in value_str:
        # Generic fraction parsing
        try:
            parts = value_str.split('/')
            return float(parts[0]) / float(parts[1])
        except:
            return float(value_str)
    else:
        try:
            return float(value_str)
        except:
            return 1.0

@login_required
@app.route('/api/goldbacks', methods=['POST'])
def add_goldback():
    try:
        # Handle file upload if present
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image_filename = save_upload_file(file, 'goldbacks')
        
        # Get form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            data['count'] = int(data.get('count', 1))
            data['denomination'] = parse_denomination(data.get('denomination', '1'))
            data['cost'] = float(data.get('cost', 0))
        else:
            data = request.json
            if 'denomination' in data:
                data['denomination'] = parse_denomination(data['denomination'])
        
        new_goldback = Goldback(
            state=data.get('state', ''),
            denomination=data.get('denomination', 1),
            year=data.get('year', ''),
            count=data.get('count', 1),
            alpha=data.get('alpha', 'No'),
            serial=data.get('serial', ''),
            cost=data.get('cost', 0),
            circulated=data.get('circulated', 'No'),
            notes=data.get('notes', ''),
            image_filename=image_filename
        )
        db.session.add(new_goldback)
        db.session.commit()
        return jsonify({'success': True, 'id': new_goldback.id}), 201
    
    except Exception as e:
        print(f"Error adding goldback: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@login_required
@app.route('/api/goldbacks/<int:id>', methods=['PUT'])
def update_goldback(id):
    goldback = Goldback.query.get_or_404(id)
    data = request.json
    
    goldback.state = data.get('state', goldback.state)
    if 'denomination' in data:
        goldback.denomination = parse_denomination(data['denomination'])
    goldback.year = data.get('year', goldback.year)
    goldback.count = data.get('count', goldback.count)
    goldback.alpha = data.get('alpha', goldback.alpha)
    goldback.serial = data.get('serial', goldback.serial)
    goldback.cost = data.get('cost', goldback.cost)
    goldback.circulated = data.get('circulated', goldback.circulated)
    goldback.notes = data.get('notes', goldback.notes)
    
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/goldbacks/<int:id>', methods=['DELETE'])
def delete_goldback(id):
    goldback = Goldback.query.get_or_404(id)
    
    # Delete associated image file if it exists
    if goldback.image_filename:
        image_path = os.path.join(UPLOAD_FOLDER, goldback.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(goldback)
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/goldbacks/<int:id>/image', methods=['POST'])
def upload_goldback_image(id):
    """Upload or replace image for existing goldback entry"""
    try:
        goldback = Goldback.query.get_or_404(id)
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Delete old image if exists
        if goldback.image_filename:
            old_path = os.path.join(UPLOAD_FOLDER, goldback.image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Save new image
        image_filename = save_upload_file(file, 'goldbacks')
        if not image_filename:
            return jsonify({'success': False, 'error': 'Failed to save image'}), 400
        
        goldback.image_filename = image_filename
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error uploading image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Metal prices API endpoint
@login_required
@app.route('/api/prices', methods=['GET'])
def get_prices():
    """Get current metal prices"""
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    if force_refresh:
        price_fetcher.fetch_all_prices()  # Force immediate fetch
    return jsonify(price_fetcher.get_prices())

# Coins API Endpoints
@login_required
@app.route('/api/coins', methods=['GET'])
def get_coins():
    coins_list = Coin.query.all()
    return jsonify([{
        'id': c.id,
        'material': c.material,
        'country': c.country,
        'year': c.year,
        'weight': c.weight,
        'denomination': c.denomination,
        'quantity': c.quantity,
        'total_cost': c.total_cost,
        'worth': c.worth,
        'gain_loss': c.gain_loss,
        'worth_updated': c.worth_updated,
        'km': c.km,
        'km_url': c.km_url,
        'notes': c.notes,
        'image_filename': c.image_filename
    } for c in coins_list])

@login_required
@app.route('/api/coins', methods=['POST'])
def add_coin():
    try:
        # Handle file upload if present
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image_filename = save_upload_file(file, 'coins')
        
        # Get form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            data['quantity'] = int(data.get('quantity', 1))
            data['total_cost'] = float(data.get('total_cost', 0))
            data['worth'] = float(data.get('worth', 0))
        else:
            data = request.json
        
        new_coin = Coin(
            material=data.get('material', ''),
            country=data.get('country', ''),
            year=data.get('year', ''),
            weight=data.get('weight', ''),
            denomination=data.get('denomination', ''),
            quantity=data.get('quantity', 1),
            total_cost=data.get('total_cost', 0),
            worth=data.get('worth', 0),
            worth_updated=data.get('worth_updated', ''),
            km=data.get('km', ''),
            km_url=data.get('km_url', ''),
            notes=data.get('notes', ''),
            image_filename=image_filename
        )
        db.session.add(new_coin)
        db.session.commit()
        return jsonify({'success': True, 'id': new_coin.id}), 201
    
    except Exception as e:
        print(f"Error adding coin: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@login_required
@app.route('/api/coins/<int:id>', methods=['PUT'])
def update_coin(id):
    coin = Coin.query.get_or_404(id)
    data = request.json
    
    coin.material = data.get('material', coin.material)
    coin.country = data.get('country', coin.country)
    coin.year = data.get('year', coin.year)
    coin.weight = data.get('weight', coin.weight)
    coin.denomination = data.get('denomination', coin.denomination)
    coin.quantity = data.get('quantity', coin.quantity)
    coin.total_cost = data.get('total_cost', coin.total_cost)
    coin.worth = data.get('worth', coin.worth)
    coin.worth_updated = data.get('worth_updated', coin.worth_updated)
    
    # Handle KM fields - allow empty strings to clear the values
    if 'km' in data:
        coin.km = data['km'] if data['km'] else None
    if 'km_url' in data:
        coin.km_url = data['km_url'] if data['km_url'] else None
    
    coin.notes = data.get('notes', coin.notes)
    
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/coins/<int:id>', methods=['DELETE'])
def delete_coin(id):
    coin = Coin.query.get_or_404(id)
    
    # Delete associated image file if it exists
    if coin.image_filename:
        image_path = os.path.join(UPLOAD_FOLDER, coin.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(coin)
    db.session.commit()
    return jsonify({'success': True})

@login_required
@app.route('/api/coins/<int:id>/image', methods=['POST'])
def upload_coin_image(id):
    """Upload or replace image for existing coin entry"""
    try:
        coin = Coin.query.get_or_404(id)
        
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Delete old image if exists
        if coin.image_filename:
            old_path = os.path.join(UPLOAD_FOLDER, coin.image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Save new image
        image_filename = save_upload_file(file, 'coins')
        if not image_filename:
            return jsonify({'success': False, 'error': 'Failed to save image'}), 400
        
        coin.image_filename = image_filename
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error uploading image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Only start price updater in the reloader child process
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_price_updater()
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)

