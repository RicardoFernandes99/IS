from xmlrpc.client import ServerProxy
from pymongo import MongoClient


rpc = ServerProxy("http://rpc-server:8000/RPC2", allow_none=True)

def convert_csv_to_file(filename, root_name="root", row_name="row"):
    return rpc.convert_csv_to_file(filename, root_name, row_name)

def list_xml_files():
    return rpc.list_xml_files()

def insert_xml_file(xml_filename, collection=None):
    return rpc.insert_xml_file(xml_filename, collection)

def validate_xml(xml_filename, xsd_filename):
    return rpc.validate_xml(xml_filename, xsd_filename)

def list_documents(collection=None):
    return rpc.list_documents(collection)

def get_document(doc_id, collection=None):
    return rpc.get_document(doc_id, collection)

def group_xml_file(xml_filename, attr_tag, filter_value=None, row_tag="row", root_name="root", output_filename=None):
    return rpc.group_xml_file(xml_filename, attr_tag, filter_value, row_tag, root_name, output_filename)
