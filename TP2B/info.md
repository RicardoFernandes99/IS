# Project Overview
- **Goal**: End-to-end CSV → XML conversion, XML validation/grouping, and MongoDB import/browsing via a web UI.
- **Stack**: Docker Compose with MongoDB, an XML-RPC worker, a FastAPI REST bridge, and a Flask frontend.
- **Shared data**: Host `data/` is mounted into containers as `/data/shared` for CSV/XML/XSD files.

# Containers (docker-compose)
- **mongo**: MongoDB 7 with persisted volume `mongo_data`.
- **rpc-server**: Python 3.11 + BaseX CLI; exposes XML-RPC on `:8000`; does CSV→XML, XSD generation, grouping, validation, and Mongo inserts.
- **rest-api**: FastAPI bridge on `:8001`; turns HTTP requests into XML-RPC calls; also exposes Mongo collections listing.
- **flask-app**: Flask UI on `:5000`; calls REST API to drive conversions/imports/validation.

Run everything: `cd test_system && docker-compose up --build`

# Components & responsibilities
- **mongo**: Persists documents. Runs MongoDB 7 with a named volume (`mongo_data`) so data survives container rebuilds.
- **rpc-server** (`test_system/rpc-server`):
  - Interface: XML-RPC on port 8000.
  - Responsibilities: CSV→XML conversion with XSD generation, XML validation, XML grouping/filtering via BaseX, streaming XML insertion into MongoDB, listing/fetching Mongo documents.
  - Key files: `rpc_server.py` (XML-RPC server), `converter.py` (convert/validate/group/XSD), `db.py` (Mongo insert/list/get), `requirements.txt` (pymongo, lxml).
- **rest-api** (`test_system/rest-api`):
  - Interface: HTTP/JSON on port 8001 (FastAPI).
  - Responsibilities: Thin bridge that maps HTTP routes to XML-RPC calls; exposes collection listing directly from MongoDB.
  - Key files: `main.py` (routes), `rpc_client.py` (XML-RPC client), `requirements.txt` (fastapi, uvicorn, pymongo).
- **flask-app** (`test_system/flask-app`):
  - Interface: Web UI on port 5000.
  - Responsibilities: User-facing forms to convert CSV, validate XML, group XML, and import to MongoDB; shows lists of XML files, collections, and document IDs.
  - Key files: `app.py`, templates in `templates/` (mainly `index.html`), `requirements.txt` (flask, requests).

# Data flow (HTTP → RPC → Mongo)
1) **Upload/convert CSV** (Flask → REST `/convert-stored-csv` → RPC `convert_csv_to_file`): writes XML + generated XSD to `/data/shared`.
2) **Validate XML** (Flask → REST `/validate-xml` → RPC `validate_xml`): stream-validates XML against XSD.
3) **Group/filter XML** (Flask → REST `/group-xml` → RPC `group_xml_file`): BaseX XQuery groups rows by an attribute, emits new XML + XSD.
4) **Import to Mongo** (Flask → REST `/import-xml` → RPC `insert_xml_file`): streams XML rows into MongoDB collection; defaults to `Collection`.
5) **Browse docs** (Flask → REST `/documents` + `/documents/{id}`): list document IDs and fetch individual docs.
6) **List collections** (Flask → REST `/collections`): shows current Mongo collections.

# Key code
- **Flask UI**: `test_system/flask-app/app.py`, templates in `test_system/flask-app/templates/`.
- **REST API**: `test_system/rest-api/main.py` (FastAPI routes). XML-RPC client in `test_system/rest-api/rpc_client.py`.
- **XML-RPC server**: `test_system/rpc-server/rpc_server.py`.
- **Conversion & validation**: `test_system/rpc-server/converter.py` (CSV→XML, XSD generation, validation, grouping via BaseX).
- **Mongo integration**: `test_system/rpc-server/db.py`.

# Dockerfiles
- `test_system/rpc-server/Dockerfile`: installs BaseX CLI + Python deps; starts `rpc_server.py`.
- `test_system/rest-api/Dockerfile`: installs FastAPI deps; starts Uvicorn `main:app` on `8001`.
- `test_system/flask-app/Dockerfile`: installs Flask; runs `flask run` on `5000`.

# Environments & defaults
- Shared data mount: `../data:/data/shared` (relative to `test_system/` compose folder).
- Mongo URI env: `MONGO_URI` (defaults to `mongodb://mongo:27017`), DB name `MONGO_DB_NAME=testdb`.
- REST URL env for Flask: `REST_API_URL` (defaults to `http://rest-api:8001` inside compose).
- Flask secrets/timeouts: `FLASK_SECRET_KEY`, `REQUEST_TIMEOUT`.

# How to use (typical flow)
- Place CSV into host `data/`.
- In the UI, “Convert CSV from shared data/” to produce XML/XSD.
- Validate XML or create grouped XML/XSD.
- Import XML into Mongo (optionally choose collection name).
- Browse collections and documents from the UI.

# Notes
- BaseX CLI is used for XQuery-based grouping; XML-RPC server wraps these operations.
- Validation is streaming; huge XML files don’t need to fully load in memory.
- Generated XSDs are derived from sampled rows; adjust `converter.py` if you need stricter schemas.
- `converter.py` currently uses `/data/shared` as the data root; override via `DATA_DIR` env in `rpc_server.py` if you change the mount point.

# API quick reference (REST)
- `POST /convert-stored-csv` (filename, root_name?, row_name?)
- `POST /group-xml` (filename, attr_tag, filter_value?, row_tag?, root_name?, output_filename?)
- `POST /import-xml` (filename, collection?)
- `POST /validate-xml` (filename, xsd_filename)
- `GET /xml-files`
- `GET /documents?collection=...`
- `GET /documents/{id}?collection=...`
- `GET /collections`

# XML-RPC methods (rpc-server)
- `convert_csv_to_file(filename, root_name?, row_name?)`
- `group_xml_file(xml_filename, attr_tag, filter_value?, row_tag?, root_name?, output_filename?)`
- `insert_xml_file(xml_filename, collection?)`
- `validate_xml(xml_filename, xsd_filename)`
- `list_xml_files()`
- `list_documents(collection?)`
- `get_document(doc_id, collection?)`
