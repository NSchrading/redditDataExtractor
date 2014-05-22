class User():
    slots = ('name',' posts')

    def __init__(self, name, posts=set([]), parent=None):
        self.name = name
