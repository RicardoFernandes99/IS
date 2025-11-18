import pandas as pd
from lxml import etree

def csv_to_xml(csv_path, xml_path):
    df = pd.read_csv(csv_path)

    root = etree.Element("rows")

    for _, row in df.iterrows():
        row_el = etree.SubElement(root, "row")
        for col in df.columns:
            col_el = etree.SubElement(row_el, col)
            col_el.text = str(row[col]) if pd.notna(row[col]) else ""

    tree = etree.ElementTree(root)
    tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"XML written to {xml_path}")

if __name__ == "__main__":
    csv_to_xml("/data/sample.csv", "/data/output.xml")
