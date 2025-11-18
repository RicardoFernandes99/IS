from pymongo import MongoClient
import os
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = "testdb"
COLLECTION = "documents"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION]

def insert_xml(xml_string):
    res = collection.insert_one({"xml": xml_string})
    return str(res.inserted_id)

def get_document(doc_id):
    doc = collection.find_one({"_id": ObjectId(doc_id)})
    return doc["xml"] if doc else None

def list_documents():
    return [str(d["_id"]) for d in collection.find({}, {"_id": 1})]
