import json
import copy
from pydantic import BaseModel
from collections.abc import Iterable

def schema2json(schema: BaseModel):
  obj = {}
    
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
      obj[prop] = 'string'
    elif propertyType == 'integer':
      obj[prop] = 0
    elif propertyType == 'boolean':
      obj[prop] = True
    else:
      obj[prop] = None
  
  return json.dumps(obj, separators=(',\n', ':'))

# def model2dict(obj: object):
#   converted = copy.deepcopy(obj.__dict__)
#   try:
#     del(converted['_sa_instance_state'])
#   except KeyError:
#     return None
#   return converted

def model2dict(data: object):
  tmp = []
  flag = False
  if not isinstance(data, Iterable):
    data = [data, ]
    flag = True
  
  for row in data:
    fields = {}
    if not isinstance(row, Iterable):
      row = (row, )
    for obj in row:
      for column in obj.__table__.columns:
        fields[column.name] = getattr(obj, column.name)
    
    if flag:
      return fields
    
    tmp.append(fields)
  return tmp