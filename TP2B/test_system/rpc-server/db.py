import os
from pathlib import Path
from typing import List, Dict, Union
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from lxml import etree

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = "testdb"
DEFAULT_COLLECTION = "Collection"
BATCH_SIZE = 25000

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def _collection(name: str = None):
    return db[name or DEFAULT_COLLECTION]


def _detect_row_tag(source) -> str:
    """Detect the row tag; if wrapped in <Group>, return the child row tag instead."""
    source_path = str(source)
    row_tag = None

    # First pass: find the first element with a parent (could be Group or row).
    for _, elem in etree.iterparse(source_path, events=("start",), huge_tree=True):
        if elem.getparent() is not None and isinstance(elem.tag, str):
            row_tag = elem.tag
            break

    # If the first non-root element is a grouping wrapper, find its first child element tag.
    if row_tag == "Group":
        for _, group in etree.iterparse(source_path, events=("end",), tag="Group", huge_tree=True):
            for child in group.iterchildren():
                if isinstance(child.tag, str):
                    row_tag = child.tag
                    break
            break

    if not row_tag:
        raise ValueError("Unable to detect row tag in XML.")
    return row_tag


def insert_xml_file(xml_path: Union[str, Path], collection: str = None) -> List[str]:
    """Stream an XML file on disk and insert rows in batches."""
    xml_path = str(xml_path)
    row_tag = _detect_row_tag(xml_path)

    coll = _collection(collection)
    batch: List[Dict] = []
    inserted_ids: List[str] = []

    context = etree.iterparse(xml_path, events=("end",), tag=row_tag)
    for _, elem in context:
        doc = {child.tag: (child.text or "") for child in elem.iterchildren()}
        batch.append(doc)

        if len(batch) >= BATCH_SIZE:
            result = coll.insert_many(batch, ordered=False)
            inserted_ids.extend(str(_id) for _id in result.inserted_ids)
            batch.clear()

        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            while parent.getprevious() is not None:
                del parent.getparent()[0]

    if batch:
        result = coll.insert_many(batch, ordered=False)
        inserted_ids.extend(str(_id) for _id in result.inserted_ids)

    return inserted_ids



def get_document(doc_id: str, collection: str = None):
    coll = _collection(collection)
    try:
        doc = coll.find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def list_documents(collection: str = None):
    coll = _collection(collection)
    return [str(doc["_id"]) for doc in coll.find().sort("_id", -1)]
