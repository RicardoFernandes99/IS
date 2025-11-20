import csv
from datetime import datetime
from pathlib import Path
from typing import Tuple, Union
from xml.sax.saxutils import escape

from lxml import etree

DATA_DIR = Path("/data/shared")

def csv_file_to_xml(csv_path: Union[str, Path], xml_path: Union[str, Path], root_name="root", row_name="row") -> None:
    csv_path = Path(csv_path)
    xml_path = Path(xml_path)

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file, \
         xml_path.open("w", encoding="utf-8", newline="") as xml_file:

        reader = csv.DictReader(csv_file)
        row_indent, col_indent = "  ", "    "
        xml_file.write(f"<{root_name}>\n")
        for row in reader:
            parts = [f"{row_indent}<{row_name}>\n"]
            for col, val in row.items():
                val = "" if val is None else escape(val)
                parts.append(f"{col_indent}<{col}>{val}</{col}>\n")
            parts.append(f"{row_indent}</{row_name}>\n")
            xml_file.write("".join(parts))
        xml_file.write(f"</{root_name}>\n")

    # Write XSD alongside the XML
    xsd_path = xml_path.with_suffix(".xsd")
    xsd_content = generate_xsd_from_csv(csv_path, root_name=root_name, row_name=row_name)
    xsd_path.write_text(xsd_content, encoding="utf-8")

def generate_xsd_from_csv(csv_path, root_name="root", row_name="row"):
    with Path(csv_path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        first_row = next(reader, {})  
    lines = [
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">',
        f'  <xs:element name="{escape(root_name)}">',
        "    <xs:complexType>",
        "      <xs:sequence>",
        f'        <xs:element name="{escape(row_name)}" minOccurs="0" maxOccurs="unbounded">',
        "          <xs:complexType>",
        "            <xs:sequence>",
    ]
    for col in cols:
        lines.append(f'              <xs:element name="{escape(col)}" type="{_simple_type(first_row.get(col, ""))}" minOccurs="0"/>')
    lines += [
        "            </xs:sequence>",
        "          </xs:complexType>",
        "        </xs:element>",
        "      </xs:sequence>",
        "    </xs:complexType>",
        "  </xs:element>",
        "</xs:schema>",
    ]
    return "\n".join(lines)


def _simple_type(val: str) -> str:
    if val is None:
        return "xs:string"
    v = val.strip()
    if v == "":
        return "xs:string"
    if v.lower() in {"true", "false"}:
        return "xs:boolean"
    
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            datetime.strptime(v, fmt)
            return "xs:dateTime" if "T" in fmt else "xs:date"
        except ValueError:
            pass
    try:
        int(v)
        return "xs:int"
    except ValueError:
        pass
    try:
        float(v)
        return "xs:decimal"
    except ValueError:
        return "xs:string"
    

def xml_xsd_validator(xml_filename: str, xsd_filename: str) -> Tuple[bool, str]:
    """Stream-validate an XML file against XSD; returns (ok, message)."""
    xml_path = DATA_DIR / xml_filename
    xsd_path = DATA_DIR / xsd_filename

    try:
        schema = etree.XMLSchema(etree.parse(str(xsd_path)))

        for _, elem in etree.iterparse(str(xml_path), events=("end",), schema=schema, huge_tree=True):
            elem.clear()
            parent = elem.getparent()
            if parent is not None:
                while parent.getprevious() is not None:
                    del parent.getparent()[0]
        return True, "OK"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
