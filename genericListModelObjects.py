class GenericListModelObj():
    slots = 'name'

    def __init__(self, name):
        self.name = name.lower()


class User(GenericListModelObj):
    slots = ('name', 'redditPosts', 'externalDownloads' 'blacklist')

    def __init__(self, name):
        super().__init__(name)
        self.redditPosts = {}
        self.externalDownloads = {}
        self.blacklist = set([])

    def isNotInBlacklist(self, redditPost):
        return redditPost not in self.blacklist

# currently the same as User, but separated because we might want to add other features
class Subreddit(GenericListModelObj):
    slots = ('name', 'redditPosts', 'externalDownloads' 'blacklist')

    def __init__(self, name):
        super().__init__(name)
        self.redditPosts = {}
        self.externalDownloads = {}
        self.blacklist = set([])

    def isNotInBlacklist(self, redditPost):
        return redditPost not in self.blacklist