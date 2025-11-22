import os
import json
import csv
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import requests
from werkzeug.utils import secure_filename

REST_API_URL = os.getenv("REST_API_URL", "http://rest-api:8001")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "600"))
# Use shared data dir (container volume) by default; can be overridden with env `DATA_DIR`
DATA_DIR = Path(os.getenv("DATA_DIR", "/data/shared"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")


def _fetch_documents(collection: str):
    try:
        resp = requests.get(
            f"{REST_API_URL}/documents",
            params={"collection": collection},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("documents", []), None
    except requests.RequestException as exc:
        return [], str(exc)

def _fetch_xml_files():
    try:
        resp = requests.get(f"{REST_API_URL}/xml-files", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("files", []), None
    except requests.RequestException as exc:
        return [], str(exc)

def _validate_xml(filename: str, xsd_filename: str):
    try:
        resp = requests.post(
            f"{REST_API_URL}/validate-xml",
            data={"filename": filename, "xsd_filename": xsd_filename},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def _group_xml(filename: str, attr_tag: str, filter_value: str, row_tag: str):
    try:
        resp = requests.post(
            f"{REST_API_URL}/group-xml",
            data={
                "filename": filename,
                "attr_tag": attr_tag,
                "filter_value": filter_value,
                "row_tag": row_tag,
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def _is_valid_csv(file_storage) -> tuple:
    """Basic validation for uploaded CSV files.

    - Checks extension is .csv
    - Reads a small sample and ensures first line contains a comma
    - Resets stream position after sampling
    Returns (True, "") on success or (False, reason) on failure.
    """
    filename = (getattr(file_storage, 'filename', '') or '').strip()
    if not filename or not filename.lower().endswith('.csv'):
        return False, "Filename must have a .csv extension"

    stream = file_storage.stream
    try:
        sample_bytes = stream.read(4096)
        # reset for later save
        stream.seek(0)
    except Exception:
        return False, "Unable to read uploaded file"

    if not sample_bytes:
        return False, "Uploaded file is empty"

    try:
        sample = sample_bytes.decode('utf-8', errors='replace')
    except Exception:
        sample = str(sample_bytes)

    # check for comma in first line
    first_line = sample.splitlines()[0] if sample.splitlines() else ''
    if ',' not in first_line:
        return False, "File does not look like a CSV (no commas found in header)"

    # optional: try csv sniff (best-effort)
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample)
        # prefer comma delimiter
        if getattr(dialect, 'delimiter', ',') != ',':
            # still allow but warn
            pass
    except Exception:
        # if sniff fails, don't block — we already checked commas
        pass

    return True, ""


@app.route("/upload-file", methods=["POST"])
def upload_file():
    """Endpoint to upload a CSV file to the shared data directory."""
    uploaded = request.files.get('file')
    if not uploaded:
        flash('Choose a file to upload.', 'error')
        return redirect(url_for('index'))

    filename = (uploaded.filename or '').strip()
    valid, reason = _is_valid_csv(uploaded)
    if not valid:
        flash(f'Upload failed: {reason}', 'error')
        return redirect(url_for('index'))

    safe_name = secure_filename(filename)
    target_path = DATA_DIR / safe_name
    try:
        # FileStorage.save accepts a path-like or string; convert to str for compatibility
        uploaded.save(str(target_path))
        flash(f'Uploaded CSV saved as: {safe_name}')
    except Exception as exc:
        flash(f'Failed to save file: {exc}', 'error')

    return redirect(url_for('index'))


def getMongoCollections():
    try:
        resp = requests.get(
            f"{REST_API_URL}/collections",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)
    

@app.route("/", methods=["GET"])
def index():
    collection = request.args.get("collection") or "Collection"
    documents, error = _fetch_documents(collection)
    xml_files, xml_error = _fetch_xml_files()
    collections, collections_error = getMongoCollections()
    if collections is None:
        collections = []
    return render_template(
        "index.html",
        documents=documents,
        error=error,
        xml_files=xml_files,
        xml_error=xml_error,
        collection=collection,
        collections=collections,
        collections_error=collections_error,
    )


@app.route("/see_csv_file_data", methods=["GET"])
def see_csv_file_data():
    """Return a JSON object with CSV filenames found in DATA_DIR."""
    try:
        files = [p.name for p in DATA_DIR.iterdir() if p.is_file() and p.name.lower().endswith('.csv')]
        return Response(json.dumps({"files": files}), mimetype="application/json")
    except Exception as exc:
        return Response(json.dumps({"files": [], "error": str(exc)}), mimetype="application/json", status=500)


@app.route("/upload", methods=["POST"])
def upload():
    filename = request.form.get("filename", "").strip()
    root_name = request.form.get("root_name") or "root"
    row_name = request.form.get("row_name") or "row"

    if not filename:
        flash("Enter a CSV filename located in the shared data directory.", "error")
        return redirect(url_for("index"))

    data = {
        "filename": filename,
        "root_name": root_name,
        "row_name": row_name,
    }

    try:
        resp = requests.post(
            f"{REST_API_URL}/convert-stored-csv",
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        flash(f"Converted {filename} to XML file: {payload.get('xml_file')}")
    except requests.RequestException as exc:
        flash(f"Conversion failed: {exc}", "error")

    return redirect(url_for("index"))


@app.route("/import-xml", methods=["POST"])
def import_xml():
    filename = request.form.get("xml_filename", "").strip()
    collection = request.form.get("collection") or "Collection"
    if not filename:
        flash("Choose an XML filename to import.", "error")
        return redirect(url_for("index", collection=collection))

    data = {"filename": filename, "collection": collection}
    try:
        resp = requests.post(
            f"{REST_API_URL}/import-xml",
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        flash(f"Imported {filename}. Inserted rows: {payload.get('inserted_count')}")
    except requests.RequestException as exc:
        flash(f"Import failed: {exc}", "error")

    return redirect(url_for("index", collection=collection))


@app.route("/validate-xml", methods=["POST"])
def validate_xml():
    filename = request.form.get("xml_filename", "").strip()
    if not filename:
        flash("Provide an XML filename.", "error")
        return redirect(url_for("index"))
    xsd_filename = filename.replace(".xml", ".xsd")

    result, error = _validate_xml(filename, xsd_filename)
    if error:
        flash(f"Validation failed: {error}", "error")
    else:
        status = result.get("status")
        message = result.get("message")
        if status == "ok":
            flash(f"Validation succeeded: {message}")
        else:
            flash(f"Validation failed: {message}", "error")

    return redirect(url_for("index"))


@app.route("/group-xml", methods=["POST"])
def group_xml():
    filename = request.form.get("xml_filename", "").strip()
    attr_tag = request.form.get("attr_tag", "").strip()
    filter_value = request.form.get("filter_value", "").strip()
    row_tag = request.form.get("row_tag") or "row"
    if not filename or not attr_tag:
        flash("Provide XML filename and attribute name to filter/group.", "error")
        return redirect(url_for("index"))

    result, error = _group_xml(filename, attr_tag, filter_value, row_tag)
    if error:
        flash(f"Group/Filter failed: {error}", "error")
    else:
        xml_out = result.get("xml_file")
        xsd_out = result.get("xsd_file")
        target = filter_value or "all"
        flash(f"Created grouped XML ({attr_tag}={target}): {xml_out} (+ {xsd_out})")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
