import concurrent.futures
import praw
import requests
import os
import shelve
import threading
import re
import json
from imageFinder import ImageFinder
from ImgurImageFinder import ImgurImageFinder
from minusImageFinder import MinusImageFinder
from vidbleImageFinder import VidbleImageFinder
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User

class DownloadType():
    USER_SUBREDDIT_CONSTRAINED = 1
    USER_SUBREDDIT_ALL = 2
    SUBREDDIT_FRONTPAGE = 3

class RedditData():
    __slots__ = ('defaultPath', 'subredditLists', 'userLists', 'currentSubredditListName', 'currentUserListName',
                 'defaultSubredditListName', 'defaultUserListName', 'downloadedUserPosts', 'r', 'downloadType', 'avoidDuplicates', 'subSort', 'subLimit')

    def __init__(self, defaultPath=os.path.abspath(os.path.expanduser('Downloads')), subredditLists=None,
                 userLists=None,
                 currentSubredditListName='Default Subs',
                 currentUserListName='Default User List', defaultSubredditListName='Default Subs',
                 defaultUserListName='Default User List', avoidDuplicates=True, subSort='hot', subLimit=10):

        self.defaultPath = defaultPath
        if subredditLists is None:
            self.subredditLists = {'Default Subs': ListModel(
                [GenericListModelObj("adviceanimals"), GenericListModelObj("aww"), GenericListModelObj("books"),
                 GenericListModelObj("earthporn"), GenericListModelObj("funny"), GenericListModelObj("gaming"),
                 GenericListModelObj("gifs"), GenericListModelObj("movies"), GenericListModelObj("music"),
                 GenericListModelObj("pics"),
                 GenericListModelObj("science"), GenericListModelObj("technology"), GenericListModelObj("television"),
                 GenericListModelObj("videos"), GenericListModelObj("wtf")], GenericListModelObj)}
        else:
            self.subredditLists = subredditLists
        if userLists is None:
            self.userLists = {'Default User List': ListModel([], User)}
        else:
            self.userLists = userLists
        self.currentSubredditListName = currentSubredditListName
        self.currentUserListName = currentUserListName
        self.defaultSubredditListName = defaultSubredditListName
        self.defaultUserListName = defaultUserListName
        self.r = praw.Reddit(user_agent='RedditUserScraper by /u/VoidXC')
        self.downloadType = DownloadType.USER_SUBREDDIT_CONSTRAINED
        self.avoidDuplicates = avoidDuplicates
        self.subSort = subSort
        self.subLimit = subLimit

    def downloadUserProcess(self, user, redditor):
        userName = user.name
        print("Starting download for: " + userName)
        self.makeDirectoryForUser(userName)
        # Temporary
        refresh = None
        #numPosts = None if options.refresh == 0 else options.refresh
        submitted = redditor.get_submitted(limit=refresh)
        posts = self.getValidPosts(submitted, user)
        images = self.getImages(posts, user)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future = [executor.submit(image.download, user, self.avoidDuplicates) for image in images if image is not None]
            concurrent.futures.wait(future)

    def downloadThread(self, validRedditors):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future = [executor.submit(self.downloadUserProcess, user, redditor) for user, redditor in validRedditors]
            concurrent.futures.wait(future)
        # Save changes made during downloading (e.g. downloadedUserPosts)
        self.saveState()

    def download(self):
        if self.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED or self.downloadType == DownloadType.USER_SUBREDDIT_ALL:
            validRedditors = self.getValidRedditors()
        if len(validRedditors) > 0:
            thread = threading.Thread(target=self.downloadThread, args=(validRedditors,))
            thread.start()

    '''
    def getImages(self, posts, user):
        images = []
        imgurImageFinder = ImgurImageFinder(user.externalDownloads, self.avoidDuplicates)
        for post in posts:
            if 'imgur' in post.domain:
                imageFinder = imgurImageFinder
            else:
                imageFinder = ImageFinder(post.url)
            images.extend(imageFinder.getImages(post, self.defaultPath))
        return images
    '''

    def getImages(self, post, user):
        images = []
        imgurImageFinder = ImgurImageFinder(user.externalDownloads.values(), self.avoidDuplicates)
        minusImageFinder = MinusImageFinder(user.externalDownloads.values(), self.avoidDuplicates)
        vidbleImageFinder = VidbleImageFinder(user.externalDownloads.values(), self.avoidDuplicates)
        if 'imgur' in post.domain:
            imageFinder = imgurImageFinder
        elif 'i.minus' in post.domain:
            imageFinder = minusImageFinder
        elif 'vidble' in post.domain:
            imageFinder = vidbleImageFinder
        else:
            imageFinder = ImageFinder()
        ims = imageFinder.getImages(post, self.defaultPath)
        images.extend(ims)
        return images

    def getValidPosts(self, submitted, user):
        posts = []
        validSubreddits = None
        if self.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED:
            validSubreddits = self.subredditLists.get(self.currentSubredditListName).stringsInLst
        for post in submitted:
            subreddit = post.subreddit.display_name
            validSubreddit = validSubreddits is None or subreddit.lower() in validSubreddits
            if validSubreddit and self.isValidPost(post, user):
                posts.append(post)
        return posts

    def isValidPost(self, post, user):
        """ Determines if this is a good post to download from
        Valid if:
            it is a new submission (meaning the files have not been downloaded from this post already)
            it is not a xpost from another subreddit which is itself a valid subreddit (to avoid duplicate file downloads)
            it is not in a blacklisted post for the user
        """
        return self.isNewSubmission(post, user) and self.isNotXPost(post) and user.isNotInBlacklist(post.permalink)

    @staticmethod
    def isNewSubmission(post, user):
        redditURL = post.permalink
        downloads = user.redditPosts
        return len(downloads) <= 0 or redditURL not in downloads

    def isNotXPost(self, post):
        if not self.avoidDuplicates:
            return True
        xpostSynonyms = ['xpost', 'x-post', 'x post', 'crosspost', 'cross-post', 'cross post']
        title = post.title.lower()
        if self.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED:
            validSubreddits = self.subredditLists.get(self.currentSubredditListName).stringsInLst
            for subreddit in validSubreddits:
                if (subreddit in title) and any(syn in title for syn in xpostSynonyms):
                    return False
        elif self.downloadType == DownloadType.USER_SUBREDDIT_ALL:
            if any(syn in title for syn in xpostSynonyms):
                return False
        return True

    def getSubredditSubmissions(self, validSubreddits):
        submissions = []
        for subreddit in validSubreddits:
            if self.subSort == 'new':
                contentFunc = subreddit.get_new
            elif self.subSort == 'rising':
                contentFunc = subreddit.get_rising
            elif self.subSort == 'controversial':
                contentFunc = subreddit.get_controversial
            elif self.subSort == 'top':
                contentFunc = subreddit.get_top
            else:
                contentFunc = subreddit.get_hot
            submissions.append((subreddit.display_name, list(contentFunc(limit=self.subLimit))))
        return submissions

    def downloadSubmission(self, subreddit, submission):
        MAX_PATH = 260 # Windows is stupid and only lets you make paths up to a length of 260 chars
        directory = os.path.abspath(os.path.join(self.defaultPath, subreddit))
        title = re.sub('[^\w\-_\. ]', '', submission.title)
        path = os.path.join(directory, title + '.txt')
        if len(path) > MAX_PATH:
            lenOver = len(path) - MAX_PATH
            title = title[:-(lenOver+len('.txt'))]
            path = os.path.join(directory, title + '.txt')
        with open(path, 'w') as f:
            json.dump(self.getSubmissionData(submission), f, ensure_ascii=True)

    def getSubmissionData(self, submission):
        submissionData = {"Permalink" : submission.permalink}
        submissionData['Title'] = submission.title
        submissionData['Post ID'] = submission.id
        submissionData['Upvotes'] = submission.ups
        submissionData['Downvotes'] = submission.downs
        submissionData['Domain'] = submission.domain
        submissionData['Selftext'] = submission.selftext
        submissionData['URL'] = submission.url
        submissionData['Comments'] = self.getAllComments(submission.comments)
        self.getAllComments(submission.comments)
        return submissionData

    def getAllComments(self, curComments):
        comments = {}
        for comment in curComments:
            if isinstance(comment, praw.objects.Comment):
                author = comment.author
                if author is None:
                    author = "[Deleted]"
                else:
                    author = author.name
                comments[author] = {'Body': comment.body, 'Replies': self.getAllComments(comment.replies)}
        return comments


    def changeDownloadType(self, downloadType):
        self.downloadType = downloadType

    def makeDirectory(self, dirName):
        directory = os.path.abspath(os.path.join(self.defaultPath, dirName))
        if not os.path.exists(directory):
            os.makedirs(directory)

    def saveState(self):
        userListModels = self.userLists
        userListSettings = {}  # Use this to save normally unpickleable stuff
        subredditListModels = self.subredditLists
        subredditListSettings = {}
        successful = False
        for key, val in userListModels.items():
            userListSettings[key] = val.lst
        for key, val in subredditListModels.items():
            subredditListSettings[key] = val.lst
        shelf = shelve.open("settings.db")
        try:
            self.userLists = None  # QAbstractListModel is not pickleable so set this to None
            self.subredditLists = None
            shelf['rddtScraper'] = self
            shelf['userLists'] = userListSettings  # Save QAbstractList data as a simple dict of list
            shelf['subredditLists'] = subredditListSettings
            self.userLists = userListModels  # Restore the user lists in case the user is not exiting program
            self.subredditLists = subredditListModels
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

    def getRedditor(self, userName):
        try:
            redditor = self.r.get_redditor(userName)
        except requests.exceptions.HTTPError:
            redditor = None
        return redditor

    def getSubreddit(self, subredditName):
        try:
            subreddit = self.r.get_subreddit(subredditName, fetch=True)
        except requests.exceptions.HTTPError:
            subreddit = None
        return subreddit
