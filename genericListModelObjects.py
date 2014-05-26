class GenericListModelObj():
    slots = 'name'

    def __init__(self, name):
        self.name = name


class User(GenericListModelObj):
    slots = ('name', 'redditPosts', 'imgurPosts' 'blacklist')

    def __init__(self, name, redditPosts=None):
        super().__init__(name)
        if redditPosts is None:
            self.redditPosts = {}
        else:
            self.redditPosts = redditPosts
        self.blacklist = set([])
        self.imgurPosts = set([])

    def isNotInBlacklist(self, redditPost):
        return redditPost not in self.blacklist