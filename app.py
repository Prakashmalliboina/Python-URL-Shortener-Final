import os
import shortuuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- CONFIGURATION ---
# Base directory for the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize the Flask App
app = Flask(__name__)

# Configure SQLAlchemy (Database setup)
# We will use a simple SQLite database file named 'urls.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize the SQLAlchemy object with the Flask app
db = SQLAlchemy(app)

# --- DATABASE MODEL: URL ---
class URL(db.Model):
    """Defines the structure of the URLs table in the database."""
    # The primary key (auto-incrementing ID)
    id = db.Column(db.Integer, primary_key=True)
    
    # The short code (e.g., 'aBz12c') - must be unique
    short_id = db.Column(db.String(10), unique=True, nullable=False)
    
    # The original long URL
    long_url = db.Column(db.String(255), nullable=False)
    
    # Timestamp for creation
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __init__(self, long_url, short_id=None):
        """Initializes a new URL object."""
        self.long_url = long_url
        
        # Generate a unique short_id if one is not provided
        if short_id is None:
            # Generate a random 7-character ID
            self.short_id = shortuuid.uuid()[:7] 
        else:
            self.short_id = short_id

    def __repr__(self):
        return f'<URL {self.short_id}>'

# --- COMMAND TO INITIALIZE DATABASE ---
@app.cli.command('create-db')
def create_db():
    """CLI command to create the database file and tables."""
    with app.app_context():
        db.create_all()
        print('Database tables created successfully!')

# --- REST OF THE CODE WILL GO HERE (Phase 3: Endpoints) ---
# app.py (Insert this code before if __name__ == '__main__':)

from flask import request, redirect, jsonify, render_template

# --- 1. Short URL Creation Endpoint (API) ---
@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Accepts a long URL and returns a JSON object with the short URL."""
    data = request.get_json()
    long_url = data.get('url')

    if not long_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    # Basic URL validation (check if it looks like a URL)
    if not long_url.startswith(('http://', 'https://')):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    # Check if URL already exists in the database
    existing_url = URL.query.filter_by(long_url=long_url).first()
    if existing_url:
        return jsonify({
            "short_id": existing_url.short_id,
            "short_url": request.host_url + existing_url.short_id,
            "message": "URL already shortened"
        }), 200

    # Create a new short URL entry
    new_url = URL(long_url=long_url)
    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        "short_id": new_url.short_id,
        "short_url": request.host_url + new_url.short_id
    }), 201 # 201 Created status

# --- 2. Redirect Endpoint ---
@app.route('/<short_id>')
def redirect_to_long_url(short_id):
    """Takes the short_id and redirects the user to the long URL."""
    # Retrieve the URL object based on the short_id
    url_entry = URL.query.filter_by(short_id=short_id).first()

    if url_entry:
        # Redirect the user to the original long URL
        return redirect(url_entry.long_url, code=302) 
    else:
        # If the short_id is not found, return a 404 error (Not Found)
        return jsonify({"error": "Short URL not found"}), 404

# --- 3. Simple Home Page (For quick testing/UI demonstration) ---
@app.route('/')
def index():
    """A basic HTML page to show the app is running."""
    return render_template('index.html')

with app.app_context():
    # This checks if the tables are created and creates them if they aren't.
    db.create_all()

if __name__ == '__main__':
    # This block is currently for development/testing
    app.run(debug=True)
