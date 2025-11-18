from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from converter import csv_to_xml
import db

class Handler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)

# RPC methods
def rpc_convert_csv(csv_bytes, root_name="root", row_name="row"):
    return csv_to_xml(csv_bytes.data, root_name=root_name, row_name=row_name)

def rpc_insert_xml(xml_string):
    return db.insert_xml(xml_string)

def rpc_get_document(doc_id):
    return db.get_document(doc_id)

def rpc_list_documents():
    return db.list_documents()

with SimpleXMLRPCServer(("0.0.0.0", 8000), requestHandler=Handler, allow_none=True) as server:
    print("RPC server running on port 8000")

    server.register_function(rpc_convert_csv, "convert_csv")
    server.register_function(rpc_insert_xml, "insert_xml")
    server.register_function(rpc_get_document, "get_document")
    server.register_function(rpc_list_documents, "list_documents")

    server.serve_forever()
