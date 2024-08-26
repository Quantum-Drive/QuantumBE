class Node:
  def __init__(self, name, value):
    self.name = name
    self.value = value
    self.children = dict()
  
  def getValue(self):
    return self.value
  
  def addChild(self, child: 'Node'):
    self.children[child.name] = child
  
  def getChild(self, name):
    return self.children.get(name)
  
  def getChildren(self):
    return [item for item in self.children.values()]
  
  def removeChild(self, name):
    return self.children.pop(name)
  
  def hasChild(self, name):
    return name in self.children
  
  def __repr__(self):
    return f'Node({self.name}, {self.value})'
  
  def __str__(self, level=0):
    ret = "  " * level + repr(self) + "\n"
    for child in self.children.values():
      ret += child.__str__(level + 1)
    return ret

class Tree(Node):
  def __init__(self, value):
    super().__init__("root", value)
  
  def addPath(self, path: str, value):
    path = path.split("/")
    node = self
    for name in path[:-1]:
      if not node.hasChild(name):
        node.addChild(Node(name, None))
      node:Node = node.getChild(name)
      
      if node.name != "root" and node.getValue() is not None:
        return False
    node.addChild(Node(path[-1], value))
    return True
  
  def getPath(self, path: str):
    path = path.split("/")
    node = self
    for name in path:
      if not node.hasChild(name):
        return None
      node = node.getChild(name)
    return node
  
  def removePath(self, path: str):
    path = path.split("/")
    if len(path) == 1:
      return self.removeChild(path[0])
    
    node = self
    for name in path[:-1]:
      if not node.hasChild(name):
        return None
      node = node.getChild(name)
    return node.removeChild(path[-1])
  
  def __str__(self):
    return super().__str__()