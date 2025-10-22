import pandas as pd

df = pd.read_csv('idealista_houses.csv')
df.to_xml('idealista_houses.xml', index=False)