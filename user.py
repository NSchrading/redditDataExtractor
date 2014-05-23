class User():
    slots = ('name', 'posts')

    def __init__(self, name, posts=None):
        self.name = name
        if posts is None:
            self.posts = set([])
        else:
            self.posts = posts