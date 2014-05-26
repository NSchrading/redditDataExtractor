class GenericListModelObj():
    slots = 'name'

    def __init__(self, name):
        self.name = name


class User(GenericListModelObj):
    slots = ('name', 'posts', 'blacklist')

    def __init__(self, name, posts=None):
        super().__init__(name)
        if posts is None:
            self.posts = {}
        else:
            self.posts = posts
        self.blacklist = set([])

    def isNotInBlacklist(self, post):
        return post not in self.blacklist