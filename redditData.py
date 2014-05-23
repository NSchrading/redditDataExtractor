import concurrent.futures
import praw
import requests
import re
import os
import shelve
import threading
from imageFinder import ImageFinder
from ImgurImageFinder import ImgurImageFinder
from userListModel import UserListModel

nullToNoneRegex = re.compile("null")
validSubreddits = {"adviceanimals", "aww", "books", "earthporn", "funny", "gaming", "gifs", "movies", "music", "pics",
                   "science", "technology", "television", "videos", "wtf"}
defaultPath = os.path.abspath(os.path.expanduser('Downloads'))


class RedditData():
    __slots__ = ('defaultPath', 'subredditSets', 'userLists', 'currentSubredditSetName', 'currentUserListName',
                 'defaultSubredditSetName', 'defaultUserListName', 'downloadedUserPosts', 'r')

    def __init__(self, defaultPath=defaultPath, subredditSets=None, userLists=None,
                 currentSubredditSetName='Default Subs',
                 currentUserListName='Default User List', defaultSubredditSetName='Default Subs',
                 defaultUserListName='Default User List'):
        self.defaultPath = defaultPath
        if subredditSets is None:
            self.subredditSets = {'Default Subs': validSubreddits}
        else:
            self.subredditSets = subredditSets
        if userLists is None:
            self.userLists = {'Default User List': UserListModel([])}
        else:
            self.userLists = userLists
        self.currentSubredditSetName = currentSubredditSetName
        self.currentUserListName = currentUserListName
        self.defaultSubredditSetName = defaultSubredditSetName
        self.defaultUserListName = defaultUserListName
        self.r = praw.Reddit(user_agent='RedditUserScraper by /u/VoidXC')

    def downloadUserProcess(self, user):
        userName = user.name
        print("Starting download for: " + userName)
        self.makeDirectoryForUser(userName)
        if self.userNotInBlacklist(userName):
            redditor = None
            try:
                redditor = self.r.get_redditor(userName)
            except requests.exceptions.HTTPError:
                self.addUserToBlacklist(userName)
            if redditor is not None:
                # Temporary
                refresh = None
                #numPosts = None if options.refresh == 0 else options.refresh
                submitted = redditor.get_submitted(limit=refresh)
                posts = self.getValidPosts(submitted, user)
                images = self.getImages(posts)
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future = [executor.submit(image.download, user) for image in images if image is not None]
                    concurrent.futures.wait(future)

    def downloadThread(self):
        jobs = []
        model = self.userLists.get(self.currentUserListName)
        for user in model.users:
            thread = threading.Thread(target=self.downloadUserProcess, args=(user,))
            jobs.append(thread)
        for thread in jobs:
            thread.start()
        for thread in jobs:
            thread.join()
        # Save changes made during downloading (e.g. downloadedUserPosts)
        self.saveState()

    def download(self):
        thread = threading.Thread(target=self.downloadThread)
        thread.start()

    def getImages(self, posts):
        images = []
        for post in posts:
            if 'imgur' in post.domain:
                imageFinder = ImgurImageFinder(post.url)
            else:
                imageFinder = ImageFinder(post.url)
            images.extend(imageFinder.getImages(post, self.defaultPath))
        return images

    def getValidPosts(self, submitted, user):
        posts = []
        for post in submitted:
            subreddit = post.subreddit.display_name
            if subreddit.lower() in [sreddit.lower() for sreddit in
                                     self.subredditSets.get(self.currentSubredditSetName)] and self.isValidPost(post,
                                                                                                                user):
                posts.append(post)
        return posts

    def isValidPost(self, post, user):
        ''' Determines if this is a good post to download from
        Valid if:
            it is from imgur
            it is a new submission (meaning the files have not been downloaded from this post already)
            it is not a xpost from another subreddit which is itself a valid subreddit (to avoid duplicate file downloads)
            it is not in a blacklist
        '''
        return self.isNewSubmission(post, user) and self.isNotXPost(post) and self.isNotInBlacklist(post)

    def isNewSubmission(self, post, user):
        url = post.permalink
        downloads = user.posts
        return len(downloads) <= 0 or url not in downloads

    def isNotXPost(self, post):
        xpostSynonyms = ['xpost', 'x-post', 'x post', 'crosspost', 'cross-post', 'cross post']
        title = post.title.lower()
        for subreddit in self.subredditSets.get(self.currentSubredditSetName):
            if (subreddit in title) and any(syn in title for syn in xpostSynonyms):
                return False
        return True

    def makeDirectoryForUser(self, user):
        directory = os.path.abspath(os.path.join(self.defaultPath, user))
        if not os.path.exists(directory):
            os.makedirs(directory)

    def saveState(self):
        userListModels = self.userLists
        userListSettings = {}  # Use this to save normally unpickleable stuff
        successful = False
        for key, val in userListModels.items():
            userListSettings[key] = val.users
        shelf = shelve.open("settings.db")
        try:
            self.userLists = None  # QAbstractListModel is not pickleable so set this to None
            shelf['rddtScraper'] = self
            shelf['userLists'] = userListSettings  # Save QAbstractList data as a simple dict of list
            self.userLists = userListModels  # Restore the user lists in case the user is not exiting program
            print("Saving program")
            successful = True
        except KeyError:
            print("save fail")
            successful = False
        finally:
            shelf.close()
        return successful

    def isNotInBlacklist(self, post):
        user = post.author.name
        postID = post.id
        path = os.path.abspath(os.path.join(self.defaultPath, user, "blacklist.txt"))
        if os.path.exists(path):
            with open(path, "r") as blacklist:
                for line in blacklist:
                    if postID in line:
                        return False
        return True

    def addUserToBlacklist(self, user):
        answer = input(
            "User: " + user + " does not exist or no longer exists. Add to blacklist so no downloads from this name will be attempted in the future? (yes/y/no/n)\n").lower()
        while answer != 'y' and answer != 'yes' and answer != 'n' and answer != 'no':
            answer = input("You must enter yes/y or no/n\n").lower()
        if answer == 'y' or answer == 'yes':
            with open(os.path.abspath(os.path.join(self.defaultPath, "blacklist.txt")), "a") as blacklist:
                blacklist.write(user + "\n")
                print("User: " + user + " successfully added to blacklist.")

    def userNotInBlacklist(self, user):
        path = os.path.abspath(os.path.join(self.defaultPath, "blacklist.txt"))
        if os.path.exists(path):
            with open(path, "r") as blacklist:
                for line in blacklist:
                    if user in line:
                        return False
        return True
