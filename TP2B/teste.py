from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict
from xml.sax.saxutils import escape

from lxml import etree
xml_base_path = "data/city_temperature.xml"


def group_by_attribute(xml_path, row_tag="row", attr_tag="City", filter_value=None):
    """Stream rows and group by attr_tag (child element). If filter_value is set, keep only that value."""
    xml_path = Path(xml_path)
    groups = defaultdict(list)

    for _, elem in etree.iterparse(str(xml_path), events=("end",), tag=row_tag, huge_tree=True):
        attr_val = elem.findtext(attr_tag, default="")
        if filter_value is None or attr_val == filter_value:
            groups[attr_val].append(etree.tostring(elem, encoding="unicode"))
        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            while parent.getprevious() is not None:
                del parent.getparent()[0]

    for attr_val, rows in groups.items():
        yield f'<Group {attr_tag}="{attr_val}">\n' + "\n".join(rows) + "\n</Group>"


def group_and_write(xml_path, row_tag="row", attr_tag="City", filter_value=None, output_path=None, root_name="root"):
    """Group rows by attr_tag and write grouped XML."""
    xml_path = Path(xml_path)
    out_path = Path(output_path) if output_path else xml_path.with_name(
        f"{xml_path.stem}_grouped_by_{attr_tag.lower()}_{filter_value or 'all'}.xml"
    )

    grouped_blocks = list(group_by_attribute(xml_path, row_tag=row_tag, attr_tag=attr_tag, filter_value=filter_value))

    with out_path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"<{root_name}>\n")
        for block in grouped_blocks:
            f.write(block)
            f.write("\n")
        f.write(f"</{root_name}>\n")

    xsd_content = generate_xsd_from_xml(out_path, root_name=root_name, row_name=row_tag, attr_tag=attr_tag)
    xsd_path = out_path.with_suffix(".xsd")
    with xsd_path.open("w", encoding="utf-8", newline="") as xsd_file:
        xsd_file.write(xsd_content)


def generate_xsd_from_xml(xml_path, root_name=None, row_name="row", attr_tag=None, max_samples: int = 200):
    """Derive an XSD from the XML content by sampling row elements."""
    xml_path = Path(xml_path)
    detected_root = root_name or _detect_root_tag(xml_path) or "root"
    field_types, group_tag, group_attributes = _infer_fields_from_xml(
        xml_path, row_name=row_name, max_samples=max_samples
    )
    return _build_xsd(
        detected_root,
        row_name,
        field_types,
        group_tag=group_tag,
        group_attr_names=group_attributes or ([attr_tag] if attr_tag else []),
    )


def _detect_root_tag(xml_path: Path) -> str:
    for _, elem in etree.iterparse(str(xml_path), events=("start",), huge_tree=True):
        if isinstance(elem.tag, str):
            return elem.tag
    return "root"


def _infer_fields_from_xml(xml_path: Path, row_name="row", max_samples: int = 200):
    field_types: Dict[str, str] = {}
    group_tag = None
    group_attributes = []
    rows_seen = 0

    for _, elem in etree.iterparse(str(xml_path), events=("end",), tag=row_name, huge_tree=True):
        if group_tag is None:
            parent = elem.getparent()
            if parent is not None and isinstance(parent.tag, str):
                group_tag = parent.tag
                group_attributes = list(parent.attrib.keys())

        for child in elem:
            if not isinstance(child.tag, str):
                continue
            inferred = _simple_type(child.text or "")
            current = field_types.get(child.tag)
            field_types[child.tag] = inferred if current is None else _widen_type(current, inferred)

        rows_seen += 1
        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            while parent.getprevious() is not None:
                del parent.getparent()[0]
        if rows_seen >= max_samples:
            break

    return field_types, group_tag, group_attributes


def _widen_type(existing: str, new: str) -> str:
    if existing == new:
        return existing

    numeric_rank = {"xs:boolean": 0, "xs:int": 1, "xs:decimal": 2}
    if existing in numeric_rank and new in numeric_rank:
        return "xs:decimal" if max(numeric_rank[existing], numeric_rank[new]) == 2 else "xs:int"

    if existing in {"xs:date", "xs:dateTime"} and new in {"xs:date", "xs:dateTime"}:
        return "xs:dateTime"

    if "xs:string" in (existing, new):
        return "xs:string"

    # Mixed incompatible types fall back to string.
    return "xs:string"


def _build_xsd(root_name: str, row_name: str, fields: Dict[str, str], group_tag=None, group_attr_names=None) -> str:
    group_attr_names = group_attr_names or []

    lines = [
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">',
        f'  <xs:element name="{escape(root_name)}">',
        "    <xs:complexType>",
        "      <xs:sequence>",
    ]

    if group_tag:
        lines += [
            f'        <xs:element name="{escape(group_tag)}" minOccurs="0" maxOccurs="unbounded">',
            "          <xs:complexType>",
            "            <xs:sequence>",
            f'              <xs:element name="{escape(row_name)}" minOccurs="0" maxOccurs="unbounded">',
            "                <xs:complexType>",
            "                  <xs:sequence>",
        ]
        for col, xsd_type in fields.items():
            lines.append(f'                    <xs:element name="{escape(col)}" type="{xsd_type}" minOccurs="0"/>')
        lines += [
            "                  </xs:sequence>",
            "                </xs:complexType>",
            "              </xs:element>",
            "            </xs:sequence>",
        ]
        for attr_name in group_attr_names:
            lines.append(f'            <xs:attribute name="{escape(attr_name)}" type="xs:string" use="optional"/>')
        lines += [
            "          </xs:complexType>",
            "        </xs:element>",
        ]
    else:
        lines += [
            f'        <xs:element name="{escape(row_name)}" minOccurs="0" maxOccurs="unbounded">',
            "          <xs:complexType>",
            "            <xs:sequence>",
        ]
        for col, xsd_type in fields.items():
            lines.append(f'              <xs:element name="{escape(col)}" type="{xsd_type}" minOccurs="0"/>')
        lines += [
            "            </xs:sequence>",
            "          </xs:complexType>",
            "        </xs:element>",
        ]

    lines += [
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
    
if __name__ == "__main__":
    group_and_write(xml_base_path, attr_tag="Region", filter_value="Europe")
