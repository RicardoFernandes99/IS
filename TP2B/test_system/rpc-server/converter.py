import pandas as pd
from lxml import etree
import io

def csv_to_xml(csv_bytes, root_name="root", row_name="row"):
    df = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)
    
    root = etree.Element(root_name)

    for _, row in df.iterrows():
        row_el = etree.SubElement(root, row_name)
        for col in df.columns:
            el = etree.SubElement(row_el, col)
            el.text = str(row[col])

    return etree.tostring(root, pretty_print=True, encoding="utf-8").decode()
