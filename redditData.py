import praw
import requests
import os
import shelve
import operator
import re
import json
from imageFinder import ImageFinder, ImgurImageFinder, MinusImageFinder, VidbleImageFinder, GfycatImageFinder
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User, Subreddit


# Essentially does what any and all do for OR and AND, except for XOR now
def xorLst(lst):
    if len(lst) > 1:
        res = lst[0] ^ lst[1]
        lst = lst[2:]
        for b in lst:
            res ^= b
    elif len(lst) == 1:
        res = lst[0]
    else:
        res = False
    return res

# The following functions are made to get around the fact that lambdas and builtin functions on str like str.endswith
# are not pickleable. Operator functions like operator.ne are pickleable though...weird.
def beginWith(s, val):
    return s.lstrip().startswith(val)

def notBeginWith(s, val):
    return not s.lstrip().startswith(val)

def endWith(s, val):
    return s.rstrip().startswith(val)

def notEndWith(s, val):
    return not s.rstrip().endswith(val)

def notContain(s, val):
    return not val in s

class DownloadType():
    USER_SUBREDDIT_CONSTRAINED = 1
    USER_SUBREDDIT_ALL = 2
    SUBREDDIT_CONTENT = 3

class ListType():
    USER = 1
    SUBREDDIT = 2

class RedditData():
    __slots__ = ('defaultPath', 'subredditLists', 'userLists', 'currentSubredditListName', 'currentUserListName',
                 'defaultSubredditListName', 'defaultUserListName', 'downloadedUserPosts', 'r', 'downloadType',
                 'avoidDuplicates', 'getExternalContent', 'getSubmissionContent', 'getCommentData', 'subSort',
                 'subLimit', 'supportedDomains', 'urlFinder', 'operMap', 'connectMap', 'postFilts', 'commentFilts', 'connector', 'filterExternalContent', 'filterSubmissionContent', 'commentCache', 'restrictDownloadsByCreationDate')

    def __init__(self):
        self.defaultPath = os.path.abspath(os.path.expanduser('Downloads'))

        self.subredditLists = {'Default Subs': ListModel(
                [Subreddit("adviceanimals"), Subreddit("aww"), Subreddit("books"),
                 Subreddit("earthporn"), Subreddit("funny"), Subreddit("gaming"),
                 Subreddit("gifs"), Subreddit("movies"), Subreddit("music"),
                 Subreddit("pics"),
                 Subreddit("science"), Subreddit("technology"), Subreddit("television"),
                 Subreddit("videos"), Subreddit("wtf")], Subreddit)}

        self.userLists = {'Default User List': ListModel([], User)}

        self.currentSubredditListName = 'Default Subs'
        self.currentUserListName = 'Default User List'
        self.defaultSubredditListName = 'Default Subs'
        self.defaultUserListName = 'Default User List'
        self.r = praw.Reddit(user_agent='RedditUserScraper by /u/VoidXC')
        self.downloadType = DownloadType.USER_SUBREDDIT_CONSTRAINED
        self.avoidDuplicates = True
        self.getExternalContent = False
        self.getSubmissionContent = True
        self.getCommentData = False
        self.subSort = 'hot'
        self.subLimit = 10
        self.supportedDomains = ['imgur', 'i.minus', 'vidble', 'gfycat']

        # This is a regex to parse URLs, courtesy of John Gruber, http://daringfireball.net/2010/07/improved_regex_for_matching_urls
        # https://gist.github.com/gruber/8891611
        self.urlFinder = re.compile(
            r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
            re.IGNORECASE)

        self.operMap = {"Equals": operator.eq, "Does not equal": operator.ne, "Begins with": beginWith,
                        "Does not begin with": notBeginWith, "Ends with": endWith,
                        "Does not end with": notEndWith, "Greater than": operator.gt,
                        "Less than": operator.lt, "Contains": operator.contains,
                        "Does not contain": notContain}

        self.connectMap = {"And": all, "Or": any, "Xor": xorLst}

        self.postFilts = []
        self.commentFilts = []
        self.connector = None
        self.filterExternalContent = False
        self.filterSubmissionContent = False
        self.commentCache = {}
        self.restrictDownloadsByCreationDate = True

    def getImages(self, post, user, commentAuthor=None, commentAuthorURLCount=None):
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
        images = imageFinder.getImages(post, self.defaultPath, user, commentAuthor, commentAuthorURLCount)
        for image in images:
            yield image

    def getValidPosts(self, submitted, listModel):
        posts = []
        validSubreddits = None
        if self.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED:
            validSubreddits = self.subredditLists.get(self.currentSubredditListName).stringsInLst
        for post in submitted:
            subreddit = post.subreddit.display_name
            validSubreddit = validSubreddits is None or subreddit.lower() in validSubreddits
            if validSubreddit and self.isValidPost(post, listModel):
                posts.append(post)
        return posts

    def isValidPost(self, post, listModel):
        """ Determines if this is a good post to download from
        Valid if:
            it is a new submission (meaning the files have not been downloaded from this post already)
            it is not a xpost from another subreddit which is itself a valid subreddit (to avoid duplicate file downloads)
            it is not in a blacklisted post for the user
        """
        return self.isNewSubmission(post, listModel) and self.isNotXPost(post) and listModel.isNotInBlacklist(post.permalink) and (not self.restrictDownloadsByCreationDate or listModel.postBeforeLastDownload(post))

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

    def getPostIdsPassingFilters(self, posts):
        return {post.id for post in posts if self.postPassesFilter(post)}

    def postPassesFilter(self, post):
        passes = False
        comments = []
        if len(self.commentFilts) > 0:
            comments = praw.helpers.flatten_tree(post.comments)
            self.cacheComments(comments, post.id)
        if self.connector is not None:
            passes = self.connector([self.connector([oper(post.__dict__.get(prop), val) for prop, oper, val in self.postFilts if post.__dict__.get(prop) is not None]), any([self.connector([oper(comment.__dict__.get(prop), val) for prop, oper, val in self.commentFilts if comment.__dict__.get(prop) is not None]) for comment in comments if isinstance(comment, praw.objects.Comment)])])
        else:
            if len(self.postFilts) > 0:
                prop, oper, val = self.postFilts[0]
                if post.__dict__.get(prop) is not None:
                    passes = oper(post.__dict__.get(prop), val)
            elif len(comments) > 0:
                prop, oper, val = self.commentFilts[0]
                passes = any([oper(comment.__dict__.get(prop), val) for comment in comments if isinstance(comment, praw.objects.Comment) and comment.__dict__.get(prop) is not None])
        return passes

    def cacheComments(self, comments, postID):
        pass
        #self.commentCache[postID] = comments

    def getSubredditSubmissions(self, validSubreddit, subredditListModel):
        if self.subSort == 'new':
            contentFunc = validSubreddit.get_new
        elif self.subSort == 'rising':
            contentFunc = validSubreddit.get_rising
        elif self.subSort == 'controversial':
            contentFunc = validSubreddit.get_controversial
        elif self.subSort == 'top':
            contentFunc = validSubreddit.get_top
        else:
            contentFunc = validSubreddit.get_hot
        return list(contentFunc(limit=self.subLimit))

    def downloadSubmission(self, submission, user=""):
        MAX_PATH = 260  # Windows is stupid and only lets you make paths up to a length of 260 chars
        if user != "":
            directory = os.path.abspath(os.path.join(self.defaultPath, user))
        else:
            subreddit = submission.subreddit.display_name
            directory = os.path.abspath(os.path.join(self.defaultPath, subreddit))
        title = re.sub('[^\w\-_\. ]', '', submission.title)
        path = os.path.join(directory, title + '.txt')
        if len(path) > MAX_PATH:
            lenOver = len(path) - MAX_PATH
            title = title[:-(lenOver + len('.txt'))]
            path = os.path.join(directory, title + '.txt')
        try:
            with open(path, 'w') as f:
                json.dump(self.getSubmissionData(submission), f, ensure_ascii=True)
                return True, path
        except:
            return False, path


    def getSubmissionData(self, submission):
        submissionData = submission.__dict__.copy() # copy so we don't mess with the submission's own __dict__
        if submission.author is None:
            submissionData['author'] = "[Deleted]"
        else:
            submissionData['author'] = submission.author.name
        submissionData['subreddit'] = submission.subreddit.display_name
        submissionData['comments'] = self.getAllComments(submission.comments)
        del submissionData['_comments'] #  objects from praw are not json serializable
        del submissionData['_comments_by_id']
        del submissionData['reddit_session']
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
        for author in commentImageURLs:
            urls = commentImageURLs.get(author)
            count = 1
            for url in urls:
                canDownload = self.fudgePostDomainAndURL(post, url)
                if canDownload:
                    count += 1
                    images = self.getImages(post, user, author, count)
                    post.url = origPostURL  # Restore the post info back to what it was
                    post.domain = origPostDomain
                    for image in images:
                        yield image

    def getCommentImageURLs(self, submission):
        urls = {}
        if self.commentCache.get(submission.id) is None:
            allComments = praw.helpers.flatten_tree(submission.comments)
        else:
            allComments = self.commentCache.get(submission.id)
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

    def mapFilterTextToOper(self, text):
        return self.operMap.get(text)

    def mapConnectorTextToOper(self, text):
        return self.connectMap.get(text)

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
