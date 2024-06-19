import json
from pydantic import BaseModel

def schema2json(schema: BaseModel):
  exampleJSON = {}
    
  # Iterate through properties
  schema = schema.model_json_schema()
  for prop, details in schema['properties'].items():
    propertyType = None
    if 'anyOf' in details:
      # Handle anyOf case
      for subtype in details['anyOf']:
        if 'type' in subtype:
          if subtype['type'] != 'null':
            propertyType = subtype['type']
    else:
      # Handle other cases
      propertyType = details.get('type', 'unknown_type')

    if propertyType == 'string':
      exampleJSON[prop] = 'string'
    elif propertyType == 'integer':
      exampleJSON[prop] = 0
    elif propertyType == 'boolean':
      exampleJSON[prop] = True
    else:
      exampleJSON[prop] = None
  
  return json.dumps(exampleJSON, separators=(',\n', ':'))