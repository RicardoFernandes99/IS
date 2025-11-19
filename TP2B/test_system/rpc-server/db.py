from pymongo import MongoClient
import os
from bson import ObjectId
from bson.errors import InvalidId
import gridfs
from gridfs.errors import NoFile
import gzip

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = "testdb"
COLLECTION = "documents"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db, collection=COLLECTION)

def insert_xml(xml_string):
    compressed = gzip.compress(xml_string.encode("utf-8"))
    file_id = fs.put(
        compressed,
        content_type="application/xml",
        metadata={"compression": "gzip"},
    )
    return str(file_id)

def get_document(doc_id):
    try:
        file = fs.get(ObjectId(doc_id))
        data = file.read()
        if file.metadata and file.metadata.get("compression") == "gzip":
            data = gzip.decompress(data)
        return data.decode("utf-8")
    except (NoFile, InvalidId):
        return None

def list_documents():
    return [str(doc._id) for doc in fs.find().sort("uploadDate", -1)]
