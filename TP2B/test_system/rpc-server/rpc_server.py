import os
from pathlib import Path
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

from converter import csv_file_to_xml, xml_xsd_validator, group_and_write
import db

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data/shared")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Handler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)

# Helpers
def _resolve_in_data(filename: str) -> Path:
    """Resolve a filename inside the shared data directory, preventing traversal."""
    base = DATA_DIR
    target = (base / filename).resolve()
    if base not in target.parents and target != base:
        raise ValueError("File path is outside the shared data directory.")
    return target

# RPC methods
def rpc_convert_csv_to_file(filename, root_name="root", row_name="row"):
    """Convert a CSV stored in DATA_DIR into an XML file in the same directory."""
    csv_path = _resolve_in_data(filename)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {filename}")

    xml_filename = f"{csv_path.stem}.xml"
    xml_path = _resolve_in_data(xml_filename)

    csv_file_to_xml(csv_path, xml_path, root_name=root_name, row_name=row_name)
    return {"xml_file": xml_filename}


def rpc_group_xml_file(xml_filename, attr_tag, filter_value=None, row_tag="row", root_name="root", output_filename=None):
    source_path = _resolve_in_data(xml_filename)
    if not source_path.is_file():
        raise FileNotFoundError(f"XML file not found: {xml_filename}")

    if output_filename:
        out_path = _resolve_in_data(output_filename)
    else:
        suffix = filter_value or "all"
        out_name = f"{source_path.stem}_grouped_by_{attr_tag.lower()}_{suffix}.xml"
        out_path = _resolve_in_data(out_name)

    group_and_write(
        source_path,
        row_tag=row_tag,
        attr_tag=attr_tag,
        filter_value=filter_value,
        output_path=out_path,
        root_name=root_name,
    )
    return {"xml_file": out_path.name, "xsd_file": out_path.with_suffix(".xsd").name}


def rpc_list_xml_files():
    """List XML files available in the shared data directory."""
    files = sorted([p.name for p in DATA_DIR.glob("*.xml") if p.is_file()])
    return files

def rpc_insert_xml_file(xml_filename, collection=None):
    """Read an XML file from DATA_DIR and insert rows into MongoDB."""
    xml_path = _resolve_in_data(xml_filename)
    if not xml_path.is_file():
        raise FileNotFoundError(f"XML file not found: {xml_filename}")
    return db.insert_xml_file(str(xml_path), collection=collection)

def rpc_validate_xml(xml_filename, xsd_filename):
    """Validate an XML file against an XSD in the shared data directory."""
    return xml_xsd_validator(xml_filename, xsd_filename)

def rpc_get_document(doc_id, collection=None):
    return db.get_document(doc_id, collection=collection)

def rpc_list_documents(collection=None):
    return db.list_documents(collection=collection)

with SimpleXMLRPCServer(("0.0.0.0", 8000), requestHandler=Handler, allow_none=True) as server:
    print("RPC server running on port 8000")

    server.register_function(rpc_convert_csv_to_file, "convert_csv_to_file")
    server.register_function(rpc_list_xml_files, "list_xml_files")
    server.register_function(rpc_insert_xml_file, "insert_xml_file")
    server.register_function(rpc_validate_xml, "validate_xml")
    server.register_function(rpc_group_xml_file, "group_xml_file")
    server.register_function(rpc_get_document, "get_document")
    server.register_function(rpc_list_documents, "list_documents")

    server.serve_forever()
