import csv
import io
from xml.sax.saxutils import escape


def csv_to_xml(csv_bytes, root_name="root", row_name="row"):
    """Stream the CSV and build XML without loading entire dataframes."""
    text_stream = io.TextIOWrapper(io.BytesIO(csv_bytes), encoding="utf-8", newline="")
    reader = csv.DictReader(text_stream)
    output = io.StringIO()

    output.write(f"<{root_name}>\n")
    row_indent = "  "
    col_indent = "    "

    for row in reader:
        output.write(f"{row_indent}<{row_name}>\n")
        for column, value in row.items():
            safe_value = "" if value is None else value
            output.write(f"{col_indent}<{column}>{escape(safe_value)}</{column}>\n")
        output.write(f"{row_indent}</{row_name}>\n")

    output.write(f"</{root_name}>\n")
    text_stream.detach()
    return output.getvalue()
