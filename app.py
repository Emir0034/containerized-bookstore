import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId



app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "BOOKSTORE")
COLLECTION = os.getenv("COLLECTION", "books")

# Kubernetes supplies database credentials through a Secret. Local Docker setups
# can keep using an unauthenticated MONGO_URI without these variables.
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
if bool(MONGO_USERNAME) != bool(MONGO_PASSWORD):
    raise RuntimeError("Set both MONGO_USERNAME and MONGO_PASSWORD or neither")

if MONGO_USERNAME and MONGO_PASSWORD:
    client = MongoClient(
        MONGO_URI,
        username=MONGO_USERNAME,
        password=MONGO_PASSWORD,
        authSource=os.getenv("MONGO_AUTH_SOURCE", "admin"),
    )
else:
    client = MongoClient(MONGO_URI)
db = client[DB_NAME]
books = db[COLLECTION]

def fix_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@app.get("/health")
def health():
    return {"ok": True, "db": DB_NAME, "collection": COLLECTION}

@app.get("/books")
def list_books():
    return jsonify([fix_id(x) for x in books.find()])

@app.get("/books/<id>")
def get_book(id):
    try:
        doc = books.find_one({"_id": ObjectId(id)})
    except Exception:
        return {"error": "invalid id"}, 400
    return (fix_id(doc), 200) if doc else ({"error": "not found"}, 404)

@app.post("/books")
def create_book():
    data = request.get_json(force=True)
    res = books.insert_one(data)
    return {"_id": str(res.inserted_id)}, 201

@app.put("/books/<id>")
def update_book(id):
    data = request.get_json(force=True)
    try:
        oid = ObjectId(id)
    except Exception:
        return {"error": "invalid id"}, 400
    books.update_one({"_id": oid}, {"$set": data})
    doc = books.find_one({"_id": oid})
    return (fix_id(doc), 200) if doc else ({"error": "not found"}, 404)

@app.delete("/books/<id>")
def delete_book(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return {"error": "invalid id"}, 400
    res = books.delete_one({"_id": oid})
    return {"deleted": res.deleted_count == 1}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
