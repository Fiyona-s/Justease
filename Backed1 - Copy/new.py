from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb+srv://fiyonasaji:fiyonasaji@cluster0.x1tki.mongodb.net/legal_advisor?retryWrites=true&w=majority')
db = client['Just_Ease']  # Updated database name
laws_collection = db['Cases']  # Updated collection name

# Fetch all laws with pagination
@app.route('/laws', methods=['GET'])
def get_all_laws():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    skip = (page - 1) * limit

    total_documents = laws_collection.count_documents({})  # Count total documents
    total_pages = (total_documents + limit - 1) // limit  # Calculate total pages

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
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    skip = (page - 1) * limit

    total_documents = laws_collection.count_documents({"court_name": court_name})
    total_pages = (total_documents + limit - 1) // limit

    laws = list(laws_collection.find({"court_name": court_name}, {"_id": 0}).skip(skip).limit(limit))

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

# Test route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Flask backend is running!"})

if __name__ == '__main__':
    app.run(debug=True)
