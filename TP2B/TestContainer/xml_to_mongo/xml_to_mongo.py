from lxml import etree
from pymongo import MongoClient

def insert_xml_to_mongo(xml_path):
    client = MongoClient("mongodb://mongo:27017")
    db = client["testdb"]
    collection = db["people"]

    tree = etree.parse(xml_path)
    root = tree.getroot()

    docs = []
    for row in root.findall("row"):
        doc = {child.tag: child.text for child in row}
        docs.append(doc)

    res = collection.insert_many(docs)
    print(f"Inserted documents: {res.inserted_ids}")

if __name__ == "__main__":
    insert_xml_to_mongo("/data/output.xml")
