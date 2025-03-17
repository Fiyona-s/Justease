from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
from flask_cors import CORS
from flask_session import Session  # Import Flask-Session
from flask import send_file
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta
import os  # Import the 'os' module
import gridfs
from io import BytesIO
from werkzeug.utils import secure_filename  

app = Flask(__name__, template_folder='templates')
CORS(app, supports_credentials=True)

MONGO_URI = os.getenv("MONGO_URI")  # Get MongoDB URI from environment variables

try:
    client = MongoClient(MONGO_URI)
    db = client['Just_Ease']
    laws_collection = db['Cases']
    users_collection = db['users']
    contacts_collection = db['contacts']
    sessions_collection = db['sessions']
    fs = gridfs.GridFS(db)
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")

# Your News API Key (Keep it private)
NEWS_API_KEY = "8bfe418c7d034af5b101ef0b5263b303"  
NEWS_API_URL = "https://newsapi.org/v2/everything"

app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}



# Define the local PDF storage path
PDF_FOLDER = os.path.join(os.getcwd(), "static", "pdf")

# Ensure the directory exists
os.makedirs(PDF_FOLDER, exist_ok=True)

def upload_pdf(file_path):
    """Saves a PDF to the local `static/pdf/` folder instead of MongoDB."""
    try:
        filename = os.path.basename(file_path)  # Get only the file name
        destination = os.path.join(PDF_FOLDER, filename)  # Target location

        # Copy file to `static/pdf/`
        with open(file_path, "rb") as f_src, open(destination, "wb") as f_dest:
            f_dest.write(f_src.read())

        print(f"PDF saved locally! Path: {destination}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

@app.route('/pdf/<filename>', methods=['GET'])
def get_pdf(filename):
    """Fetch a PDF file from the local `static/pdf/` folder."""
    try:
        file_path = os.path.join(PDF_FOLDER, filename)  # Get the full file path
        
        if os.path.exists(file_path):  # Check if the file exists
            return send_file(file_path, mimetype='application/pdf', as_attachment=False, download_name=filename)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# Track Page Visits

@app.before_request
def track_page_visits():
    session_id = session.get("session_id")
    if session_id:
        page_url = request.path  # Get the current URL path
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$push": {"visited_pages": page_url}}
        )

# Endpoints
@app.route('/')
def home():
        return render_template('index.html')  # Make sure this file exists in "templates/"


@app.route('/login')
def login():
    return render_template('login.html')

# Endpoint for the cases page
@app.route('/cases')
def cases():
    return render_template('cases.html')

# Endpoint for the change password page
@app.route('/change-password')
def change_password_page():
    return render_template('change-pass.html')

@app.route('/dashboard')
def dashboard():
    # Fetch the session ID from the session
    session_id = session.get("session_id")
    # Fetch session data from the sessions collection
    session_data = sessions_collection.find_one({"session_id": session_id})
    # Fetch the user's ID from the session data
    user_id = session_data["user_id"]

    # Fetch the user's data from the users collection
    user = users_collection.find_one({"_id": user_id})

    # Render the dashboard template and pass the user object
    return render_template('dashboard.html', user=user)

# Endpoint for the easbot page
@app.route('/easbot')
def easbot():
    return render_template('easbot.html')

@app.route('/lawyer-finder')
def lawyer_finder():
    return render_template('lawyer-finder.html')

# Endpoint for the legal resources page
@app.route('/legal-resource')
def legal_resources():
    return render_template('legal-resource.html')

# Endpoint for the news page
@app.route('/news')
def news():
    return render_template('news.html')

# Endpoint for the doc page
@app.route('/doc')
def doc():
    return render_template('doc.html')


# Endpoint for the checklist page
@app.route('/checklist')
def checklist():
    return render_template('checklist.html')


# Endpoint for the profile page
@app.route('/profile')
def profile():
    session_id = session.get("session_id")
    if session_id:
        session_data = sessions_collection.find_one({"session_id": session_id})
        if not session_data:
            return redirect(url_for('login'))

        # Fetch user data
        user_id = session_data["user_id"]
        user = users_collection.find_one({"_id": user_id})
        if not user:
            return redirect(url_for('login'))

        # Handle expiration date
        expiration_date = session_data.get("expiration")
        if expiration_date:
            if isinstance(expiration_date, str):  # Check if it's a string
                expiration_date = datetime.fromisoformat(expiration_date).strftime("%B %d, %Y, %I:%M %p")  # Format: "March 11, 2025, 6:54 PM"
            elif isinstance(expiration_date, datetime):  # Check if it's already a datetime object
                expiration_date = expiration_date.strftime("%B %d, %Y, %I:%M %p")
            else:
                expiration_date = "No expiration date set"  # Fallback for invalid data
        else:
            expiration_date = "No expiration date set"  # Fallback for missing data

        return render_template(
            "profile.html",
            user=user,
            expiration_date=expiration_date,  # Pass the formatted date to the template
            visited_pages=session_data.get("visited_pages", []),
            preferences=session_data.get("preferences", {})
        )
    return redirect(url_for('login'))

# Route to handle the logout action
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clear the entire session
    return jsonify({"message": "Logout successful"}), 200
    
# Endpoint to fetch corporate law news
@app.route('/corporate-law-news', methods=['GET'])
def get_corporate_law_news():
    params = {
        'q': 'corporate law OR corporate court OR corporate rules OR corporate governance OR corporate advocate OR corporate compliance',
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 10,  # Fetching only 10 articles
        'domains': 'thehindu.com, indiatoday.in, livemint.com, barandbench.com, theprint.in, economictimes.indiatimes.com, business-standard.com'
    }
    headers = {"X-Api-Key": NEWS_API_KEY}

    try:
        response = requests.get(NEWS_API_URL, params=params, headers=headers)
        response.raise_for_status()  # Handle HTTP errors
        data = response.json()

        if data.get("articles"):
            articles = [
                {
                    "title": article["title"],
                    "description": article["description"],
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "publishedAt": article["publishedAt"]
                }
                for article in data["articles"]
            ]
            return jsonify({"corporate_law_news": articles})

        return jsonify({"error": "No corporate law-related news found"}), 404

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": "HTTP error", "details": str(http_err)}), 401
    except requests.exceptions.RequestException as req_err:
        return jsonify({"error": "Failed to fetch news", "details": str(req_err)}), 500

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    firstname = data.get('first-name')
    lastname = data.get('last-name')
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    user_data = {"firstname": firstname, "lastname": lastname,"email": email, "password": hashed_password}

    try:
        users_collection.insert_one(user_data)
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500

# Signin route
@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    print("Received data:", data)  # Debugging line

    if not data:
        return jsonify({"message": "No data received or invalid JSON"}), 400
    
    email = data.get('email')
    password = data.get('password')

    # Validate input
    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400
    
    # Check if user exists
    user = users_collection.find_one({"email": email})

    # Validate user credentials
    if user and check_password_hash(user['password'], password):
        session_id = str(uuid.uuid4())  # Generate a unique session ID
        expiration_time = datetime.utcnow() + timedelta(hours=1)  # Example: session expires in 1 hour

        session_data = {
            "user_id": user["_id"],  # Link session to user
            "session_id": session_id,
            "visited_pages": [],
            "preferences": {},  # Placeholder for user settings
             "selected_items":[],
            "expiration": expiration_time
            
        }
        sessions_collection.insert_one(session_data)

        session["session_id"] = session_id  # Store session ID in Flask session
        userData = {"firstname": user.get('firstname'), "lastname": user.get('lastname'), "email": email}
        session['logged_in'] = True

        return jsonify({"message": "Login successful", "user": userData}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

# Change Password
@app.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    email = data.get('email')
    old_password = data.get('old-password')
    new_password = data.get('new-password')
    confirm_password = data.get('confirm-password')

    

    # Find the user by email
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"message": "User not found"}), 404

   

    # Hash the new password and update it in the database
    hashed_new_password = generate_password_hash(new_password)
    users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_new_password}}
    )

    return jsonify({"message": "Password changed successfully"}), 200
# Contact Form Submission
@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    phone = data.get('phone', '')  # Optional field
    message = data.get('message')

    # Check for required fields
    if not first_name or not last_name or not email or not message:
        return jsonify({"message": "All required fields must be filled!"}), 400

    contact_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "message": message
    }

    try:
        contacts_collection.insert_one(contact_data)  # Store data in MongoDB
        return jsonify({"message": "Message sent successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"Error: {e}"}), 500

# Fetch all laws with pagination
@app.route('/laws', methods=['GET'])
def get_all_laws():
    page = max(1, int(request.args.get('page', 1)))
    limit = max(1, int(request.args.get('limit', 10)))
    skip = (page - 1) * limit

    total_documents = laws_collection.count_documents({})
    total_pages = max(1, (total_documents + limit - 1) // limit)

    if page > total_pages:
        return jsonify({"error": "Page out of range", "total_pages": total_pages}), 400

    laws = list(laws_collection.find({}, {"_id": 0}).skip(skip).limit(limit))
    return jsonify({
        "laws": laws,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    })

@app.route('/laws/highcourt/<court_name>', methods=['GET'])
def get_laws_by_highcourt(court_name):
    page = max(1, int(request.args.get('page', 1)))
    limit = max(1, int(request.args.get('limit', 5)))
    skip = (page - 1) * limit

    total_documents = laws_collection.count_documents({"court_name": court_name + " High Court"})
    total_pages = max(1, (total_documents + limit - 1) // limit)

    if page > total_pages:
        return jsonify({"error": "Page out of range", "total_pages": total_pages}), 400

    laws = list(laws_collection.find({"court_name": court_name + " High Court"}, {"_id": 0}).skip(skip).limit(limit))

    if not laws:
        return jsonify({"error": f"No case files found for {court_name}"}), 404

    return jsonify({
        "laws": laws,
        "court_name": court_name,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    })
    
# New search route for fetching case files based on a search term
@app.route('/laws/search', methods=['GET'])
def search_cases():
    query = request.args.get('query', '')
    page = max(1, int(request.args.get('page', 1)))
    limit = max(1, int(request.args.get('limit', 5)))
    skip = (page - 1) * limit

    # Query the database for cases that contain the search term
    total_documents = laws_collection.count_documents({
        "$or": [
            {"case_data.case_name": {"$regex": query, "$options": "i"}},
            {"court_name": {"$regex": query, "$options": "i"}},
            {"year": {"$regex": query, "$options": "i"}},
        ]
    })

    total_pages = max(1, (total_documents + limit - 1) // limit)

    if page > total_pages:
        return jsonify({"error": "Page out of range", "total_pages": total_pages}), 400

    laws = list(laws_collection.find({
        "$or": [
            {"case_data.case_name": {"$regex": query, "$options": "i"}},
            {"court_name": {"$regex": query, "$options": "i"}},
            {"year": {"$regex": query, "$options": "i"}},
        ]
    }, {"_id": 0}).skip(skip).limit(limit))

    return jsonify({
        "laws": laws,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    })

# Google Maps API Integration
GOOGLE_MAPS_API_KEY = "AIzaSyANSebl5DZm3EA6XlkL0w6FUJGzAwwFYeg"

def get_lat_lng_from_location(location):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(geocode_url)
    if response.status_code != 200:
        return None

    geocode_data = response.json()
    if geocode_data['status'] == 'OK':
        lat = geocode_data['results'][0]['geometry']['location']['lat']
        lng = geocode_data['results'][0]['geometry']['location']['lng']
        return lat, lng
    return None

# Fetching all lawyers by location
@app.route('/find_lawyers_by_location', methods=['GET'])
def find_lawyers_by_location():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location parameter is required.'}), 400

    lat_lng = get_lat_lng_from_location(location)
    if lat_lng is None:
        return jsonify({'error': 'Could not find coordinates for the location.'}), 400

    lat, lng = lat_lng
    return search_nearby_lawyers(lat, lng)



@app.route('/delete-account', methods=['POST'])
def delete_account():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch the session data
    session_data = sessions_collection.find_one({"session_id": session_id})
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    # Fetch the user ID from the session
    user_id = session_data["user_id"]

    try:
        # Delete the user from MongoDB
        users_collection.delete_one({"_id": user_id})

        # Delete the session from MongoDB
        sessions_collection.delete_one({"session_id": session_id})

        # Clear the Flask session
        session.clear()

        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Fetching all lawyers based on latitude and longitude
@app.route('/find_lawyers', methods=['GET'])
def find_lawyers():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    if not lat or not lng:
        return jsonify({'error': 'Latitude and Longitude parameters are required.'}), 400
    return search_nearby_lawyers(lat, lng)

def search_nearby_lawyers(lat, lng):
    search_radii = [5000, 10000, 15000, 25000, 50000]
    lawyers = []

    for radius in search_radii:
        places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&keyword=corporate%20lawyer&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(places_url)

        if response.status_code != 200:
            return jsonify({'error': 'Google Places API request failed'}), 500

        places_response = response.json()

        if places_response.get('status') == 'OK':
            for place in places_response.get('results', []):
                place_id = place.get('place_id')
                details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,geometry,website,geometry/location&key={GOOGLE_MAPS_API_KEY}"
                details_response = requests.get(details_url).json()
                details = details_response.get('result', {})

                lawyer_lat = details.get('geometry', {}).get('location', {}).get('lat')
                lawyer_lng = details.get('geometry', {}).get('location', {}).get('lng')
                distance = calculate_distance(lat, lng, lawyer_lat, lawyer_lng)

                lawyer_info = {
                    'name': details.get('name', 'Unknown'),
                    'address': details.get('formatted_address', 'Address not available'),
                    'latitude': lawyer_lat,
                    'longitude': lawyer_lng,
                    'website': details.get('website', None),
                    'rating': details.get('rating', 'No rating available'),
                    'distance': distance
                }
                lawyers.append(lawyer_info)

        if lawyers:
            break

    lawyers_sorted = sorted(lawyers, key=lambda x: x['distance'])

    return jsonify({'lawyers': lawyers_sorted})

def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0
    lat1_rad, lon1_rad = radians(float(lat1)), radians(float(lon1))
    lat2_rad, lon2_rad = radians(float(lat2)), radians(float(lon2))
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


@app.route('/update-profile', methods=['POST'])
def update_profile():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch the session data
    session_data = sessions_collection.find_one({"session_id": session_id})
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    # Fetch the user ID from the session
    user_id = session_data["user_id"]

    # Get the updated data from the request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update the user's profile in MongoDB
    try:
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "role": data.get("role"),
                "state": data.get("state"),
                "phone": data.get("phone"),
            }}
        )
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#checklist route:
# Endpoint to save selected items for a user
@app.route('/save-selected-items', methods=['POST'])
def save_selected_items():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    selected_items = data.get("selectedItems", [])

    # Fetch the user's session data
    session_data = sessions_collection.find_one({"session_id": session_id})
    if session_data:
        user_id = session_data["user_id"]
        # Update the user's selected items in the users collection
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {"selected_items": selected_items}}
        )
        return jsonify({"message": "Selected items saved successfully"}), 200

    return jsonify({"error": "Session not found"}), 404

# Endpoint to get selected items for a user
@app.route('/get-selected-items', methods=['GET'])
def get_selected_items():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "Unauthorized"}), 401

    session_data = sessions_collection.find_one({"session_id": session_id})
    if session_data:
        user_id = session_data["user_id"]
        user_data = users_collection.find_one({"_id": user_id})
        if user_data:
            selected_items = user_data.get("selected_items", [])
            return jsonify({"selectedItems": selected_items}), 200

    return jsonify({"selectedItems": []}), 200
import os

if __name__ == '__main__':
    app.secret_key = 'alwin123123'
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Get the port dynamically assigned by Render, default to 10000
    port = int(os.environ.get("PORT", 10000))  
    app.run(host='0.0.0.0', port=port, debug=False)
