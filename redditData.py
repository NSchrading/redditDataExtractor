import concurrent.futures
import praw
import requests
import os
import shelve
import threading
import re
import json
from imageFinder import ImageFinder, ImgurImageFinder, MinusImageFinder, VidbleImageFinder, GfycatImageFinder
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User


class DownloadType():
    USER_SUBREDDIT_CONSTRAINED = 1
    USER_SUBREDDIT_ALL = 2
    SUBREDDIT_CONTENT = 3


class RedditData():
    __slots__ = ('defaultPath', 'subredditLists', 'userLists', 'currentSubredditListName', 'currentUserListName',
                 'defaultSubredditListName', 'defaultUserListName', 'downloadedUserPosts', 'r', 'downloadType',
                 'avoidDuplicates', 'getExternalDataSub', 'getCommentData', 'subSort', 'subLimit', 'supportedDomains',
                 'urlFinder')

    def __init__(self, defaultPath=os.path.abspath(os.path.expanduser('Downloads')), subredditLists=None,
                 userLists=None,
                 currentSubredditListName='Default Subs',
                 currentUserListName='Default User List', defaultSubredditListName='Default Subs',
                 defaultUserListName='Default User List', avoidDuplicates=True, getExternalDataSub=False,
                 getCommentData=False, subSort='hot', subLimit=10, supportedDomains=None):

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
        self.getExternalDataSub = getExternalDataSub
        self.getCommentData = getCommentData
        self.subSort = subSort
        self.subLimit = subLimit
        if supportedDomains is None:
            self.supportedDomains = ['imgur', 'i.minus', 'vidble', 'gfycat']
        else:
            self.supportedDomains = supportedDomains

        # This is a regex to parse URLs, courtesy of John Gruber, http://daringfireball.net/2010/07/improved_regex_for_matching_urls
        # https://gist.github.com/gruber/8891611
        self.urlFinder = re.compile(
            r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
            re.IGNORECASE)

    def getImages(self, post, user, commentAuthor=None, commentAuthorURLCount=None):
        images = []
        imageFinder = None
        imageFinderDomains = {
        self.supportedDomains[0]: ImgurImageFinder(user.externalDownloads.values(), self.avoidDuplicates),
        self.supportedDomains[1]: MinusImageFinder(user.externalDownloads.values(), self.avoidDuplicates),
        self.supportedDomains[2]: VidbleImageFinder(user.externalDownloads.values(), self.avoidDuplicates),
        self.supportedDomains[3]: GfycatImageFinder(user.externalDownloads.values(), self.avoidDuplicates)}
        domains = imageFinderDomains.keys()

        for domain in domains:
            if domain in post.domain:
                imageFinder = imageFinderDomains.get(domain)
                break
        if imageFinder is None:
            imageFinder = ImageFinder()  # default to a basic image finder if no supported domain is found
        ims = imageFinder.getImages(post, self.defaultPath, commentAuthor, commentAuthorURLCount)
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
        MAX_PATH = 260  # Windows is stupid and only lets you make paths up to a length of 260 chars
        directory = os.path.abspath(os.path.join(self.defaultPath, subreddit))
        title = re.sub('[^\w\-_\. ]', '', submission.title)
        path = os.path.join(directory, title + '.txt')
        if len(path) > MAX_PATH:
            lenOver = len(path) - MAX_PATH
            title = title[:-(lenOver + len('.txt'))]
            path = os.path.join(directory, title + '.txt')
        with open(path, 'w') as f:
            json.dump(self.getSubmissionData(submission), f, ensure_ascii=True)

    def getSubmissionData(self, submission):
        submissionData = {"Permalink": submission.permalink}
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
            if isinstance(comment, praw.objects.Comment):  # Make sure it isn't a MoreComments object
                author = comment.author
                if author is None:
                    author = "[Deleted]"
                else:
                    author = author.name
                comments[author] = {'Body': comment.body, 'Replies': self.getAllComments(comment.replies)}
        return comments

    def fudgePostDomainAndURL(self, post, url):
        for supportedDomain in self.supportedDomains:
            if supportedDomain in url:
                post.domain = supportedDomain
                post.url = url
                return True
        return False

    def getCommentImages(self, post, user):
        origPostURL = post.url  # We're going to be hijacking these variables to use self.getImages
        origPostDomain = post.domain
        commentImageURLs = self.getCommentImageURLs(post)
        images = []
        for author in commentImageURLs:
            urls = commentImageURLs.get(author)
            count = 1
            for url in urls:
                canDownload = self.fudgePostDomainAndURL(post, url)
                if canDownload:
                    images.extend(self.getImages(post, user, author, count))
                    count += 1
        post.url = origPostURL  # Restore the post info back to what it was
        post.domain = origPostDomain
        return images

    def getCommentImageURLs(self, submission):
        urls = {}
        allComments = praw.helpers.flatten_tree(submission.comments)
        for comment in allComments:
            if isinstance(comment, praw.objects.Comment):  # Make sure it isn't a MoreComments object
                author = comment.author
                if author is None:
                    author = "[Deleted]"
                else:
                    author = author.name
                matches = self.urlFinder.findall(comment.body)
                authorURLs = urls.get(author)
                if authorURLs is None:
                    urls[author] = matches
                else:
                    urls[author].extend(matches)
        return urls

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
        except:
            subreddit = None
        return subreddit
