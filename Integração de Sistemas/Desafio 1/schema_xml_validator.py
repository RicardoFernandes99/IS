import xmlschema
schema = xmlschema.XMLSchema('idealista_houses.xsd')
is_valid = schema.is_valid('idealista_houses.xml')
print(f'XML is valid: {is_valid}')