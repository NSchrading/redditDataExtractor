"""
    This file is part of the reddit Data Extractor.

    The reddit Data Extractor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The reddit Data Extractor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with The reddit Data Extractor.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import pathlib
import shelve
import operator
import re
import json
import praw
import requests

from .imageFinder import ImageFinder, ImgurImageFinder, MinusImageFinder, VidbleImageFinder, GfycatImageFinder
from .GUI.listModel import ListModel
from .GUI.genericListModelObjects import User, Subreddit
from enum import Enum


def xorLst(lst):
    """
    Essentially does what any() and all() do for OR and AND, except for XOR now

    :param lst: A list of booleans
    :type lst: list
    :rtype: bool
    """
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
    """
    :type s: str
    :type val: str
    :rtype: bool
    """
    return s.lstrip().startswith(val)


def notBeginWith(s, val):
    """
    :type s: str
    :type val: str
    :rtype: bool
    """
    return not s.lstrip().startswith(val)


def endWith(s, val):
    """
    :type s: str
    :type val: str
    :rtype: bool
    """
    return s.rstrip().endswith(val)


def notEndWith(s, val):
    """
    :type s: str
    :type val: str
    :rtype: bool
    """
    return not s.rstrip().endswith(val)


def notContain(s, val):
    """
    :type s: str
    :type val: str
    :rtype: bool
    """
    return not val in s


def equalsBool(s, val):
    """
    An attempt to get around Reddits API which makes 'edited' False if it is False and a float utc timestamp if it is True
    Simply returns whether or not the passed in val boolean is the same as the boolean / string in s
    :type s: str or bool
    :type val: bool
    :rtype: bool
    """
    if s == False or s == "False" or s == "":
        return not val
    else:
        return val


class DownloadType(Enum):
    USER_SUBREDDIT_CONSTRAINED = 1
    USER_SUBREDDIT_ALL = 2
    SUBREDDIT_CONTENT = 3

class ListType(Enum):
    USER = 1
    SUBREDDIT = 2


class RedditDataExtractor():
    """
    The "model" behind the GUI. Most of the code that deals with PRAW data is in this class. This is also the class
    that gets pickled and saved to store user settings and downloaded content information.
    """
    def __init__(self):
        self._r = praw.Reddit(user_agent='Data Extractor for reddit v1.0 by /u/VoidXC')
        # domains that are specifically targeted to work for downloading external content
        self._supportedDomains = ['imgur', 'minus', 'vidble', 'gfycat']
        # This is a regex to parse URLs, courtesy of John Gruber, http://daringfireball.net/2010/07/improved_regex_for_matching_urls
        # https://gist.github.com/gruber/8891611
        self._urlFinder = re.compile(
            r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
            re.IGNORECASE)
        # Telling PRAW to get all the comments for a submission is expensive API-call wise. Avoid doing it more than once
        # for a single submission
        self._commentCache = {}

        self.defaultPath = pathlib.Path(os.path.expanduser('~')) / 'Downloads'

        # The list of default subs to start with on a fresh run of the program
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

        self.imgurAPIClientID = None

        # Restrict certain actions while program is downloading using this boolean
        self.currentlyDownloading = False

        # Filter stuff
        self.operMap = {"Equals": operator.eq, "Does not equal": operator.ne, "Begins with": beginWith,
                        "Does not begin with": notBeginWith, "Ends with": endWith,
                        "Does not end with": notEndWith, "Greater than": operator.gt,
                        "Less than": operator.lt, "Contains": operator.contains,
                        "Does not contain": notContain, "Equals bool": equalsBool}

        self.validOperForPropMap = {"boolean": {"Equals bool"},
                                    "number": {"Equals", "Does not equal", "Greater than", "Less than"},
                                    "string": {"Equals", "Does not equal", "Begins with", "Does not begin with",
                                               "Ends with", "Does not end with", "Greater than", "Less than",
                                               "Contains", "Does not contain"}}

        self.connectMap = {"And": all, "Or": any, "Xor": xorLst}
        self.submissionFilts = []
        self.commentFilts = []
        self.connector = None

        # Default setting values that can be set by the user in the settings panel
        self.filterExternalContent = False
        self.filterSubmissionContent = False
        self.downloadType = DownloadType.USER_SUBREDDIT_CONSTRAINED
        self.avoidDuplicates = True
        self.getExternalContent = False
        self.getCommentExternalContent = False
        self.getSelftextExternalContent = False
        self.getSubmissionContent = True
        self.subSort = 'hot'
        self.subLimit = 10
        self.restrictDownloadsByCreationDate = True
        self.showImgurAPINotification = True

    def _isValidSubmission(self, submission, lstModelObj):
        """ Determines if this is a good submission to download from
        Valid if:
            it is not a xpost from another subreddit which is itself a valid subreddit (to avoid duplicate file downloads)
            it is not in a blacklisted submission for the user
            it does not have a creation date that is further in the past than the last downloaded creation date (if restrictDownloadsByCreationDate is set to True)

        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type submission: praw.objects.Submission
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :rtype: bool
        """
        return self._isNotXPost(submission) and lstModelObj.submissionNotInBlacklist(submission.permalink) and (
        not self.restrictDownloadsByCreationDate or lstModelObj.submissionBeforeLastDownload(submission))

    def _submissionPassesFilter(self, submission):
        """
        Determine if the submission passes the filters set by the user
        :type submission: praw.objects.Submission
        :rtype: bool
        """
        passes = False
        comments = []
        if len(self.commentFilts) > 0:
            comments = praw.helpers.flatten_tree(submission.comments)
            self._cacheComments(comments, submission.id)
        if self.connector is not None:
            passes = self.connector([self.connector(
                [oper(submission.__dict__.get(prop), val) for prop, oper, val in self.submissionFilts if
                 submission.__dict__.get(prop) is not None]), any([self.connector(
                [oper(comment.__dict__.get(prop), val) for prop, oper, val in self.commentFilts if
                 comment.__dict__.get(prop) is not None]) for comment in comments if
                                                             isinstance(comment, praw.objects.Comment)])])
        else:
            if len(self.submissionFilts) > 0:
                prop, oper, val = self.submissionFilts[0]
                if submission.__dict__.get(prop) is not None:
                    passes = oper(submission.__dict__.get(prop), val)
            elif len(comments) > 0:
                prop, oper, val = self.commentFilts[0]
                passes = any([oper(comment.__dict__.get(prop), val) for comment in comments if
                              isinstance(comment, praw.objects.Comment) and comment.__dict__.get(prop) is not None])
        return passes

    def _isNotXPost(self, submission):
        """
        Try to figure out if the submission is a cross-post from a different subreddit.
        Returns False, meaning it is a cross-post, if any cross-post synonym appears in the
        submission title and, if it is user_subreddit_constrained downloading,
        the name of a valid subreddit appears in the title
        :type submission: praw.objects.Submission
        """
        if not self.avoidDuplicates:
            return True
        xpostSynonyms = ['xpost', 'x-post', 'x post', 'crosspost', 'cross-post', 'cross post']
        title = submission.title.lower()
        if self.downloadType is DownloadType.USER_SUBREDDIT_CONSTRAINED:
            validSubreddits = self.subredditLists.get(self.currentSubredditListName).stringsInLst
            for subreddit in validSubreddits:
                if (subreddit in title) and any(syn in title for syn in xpostSynonyms):
                    return False
        elif self.downloadType is DownloadType.USER_SUBREDDIT_ALL:
            if any(syn in title for syn in xpostSynonyms):
                return False
        return True

    def _cacheComments(self, comments, submissionID):
        """
        Save viewed comments in a cache to avoid querying them again.
        :type comments: list
        :type submissionID: str
        """
        self._commentCache[submissionID] = comments

    def _getSubmissionData(self, submission):
        """
        Get the JSON of a submission object
        :type submission: praw.objects.Submission
        :rtype: dict
        """
        submissionData = submission.__dict__.copy()  # copy so we don't mess with the submission's own __dict__
        if submission.author is None:
            submissionData['author'] = "[Deleted]"
        else:
            submissionData['author'] = submission.author.name
        submissionData['subreddit'] = submission.subreddit.display_name
        submissionData['comments'] = self._getAllComments(submission.comments)
        del submissionData['_comments']  #  objects from praw are not json serializable
        del submissionData['_comments_by_id']
        del submissionData['reddit_session']
        return submissionData

    def _getAllComments(self, curComments):
        """
        Get all the comments of a Reddit submission in a nice, JSON-formatted hierarchy of comments and replies.
        Uses recursion to get the comment hierarchy.
        :type curComments: list
        :rtype: dict
        """
        comments = {}
        for comment in curComments:
            if isinstance(comment, praw.objects.Comment):  # Make sure it isn't a MoreComments object
                author = comment.author
                if author is None:
                    author = "[Deleted]"
                else:
                    author = author.name
                if comments.get(
                        author) is not None:  # We make this a list in case the author comments multiple times in the submission on the same level of the comment tree
                    comments[author].append({'Body': comment.body, 'Replies': self._getAllComments(comment.replies)})
                else:
                    comments[author] = [{'Body': comment.body, 'Replies': self._getAllComments(comment.replies)}]
        return comments

    def _fudgeSubmissionDomainAndURL(self, submission, url):
        """
        When we are downloading comment or selftext images, we want to utilize most of the same functionality as a
        simple getImages() for a submission image, but we want to change the domain to the domain of the comment or
        selftext image so that we don't use an incorrect ImageFinder based on the submission's domain.

        :type submission: praw.objects.Submission
        :type url: str
        :rtype: bool
        """
        for supportedDomain in self._supportedDomains:
            if supportedDomain in url:
                submission.domain = supportedDomain
                submission.url = url
                return True
        # default to an unknown domain and hope it's a directly linked image
        submission.domain = "UNKNOWN"
        submission.url = url
        return True

    def _getCommentImageURLs(self, submission):
        """
        Get image URLs linked from comments in the submission.
        :type submission: praw.objects.Submission
        :rtype: dict
        """
        urls = {}
        if self._commentCache.get(submission.id) is None:
            allComments = praw.helpers.flatten_tree(submission.comments)
            self._cacheComments(allComments, submission.id)
        else:
            allComments = self._commentCache.get(submission.id)
        for comment in allComments:
            if isinstance(comment, praw.objects.Comment):  # Make sure it isn't a MoreComments object
                author = comment.author
                if author is None:
                    author = "[Deleted]"
                else:
                    author = author.name
                matches = self._urlFinder.findall(comment.body)
                authorURLs = urls.get(author)
                if authorURLs is None:
                    urls[author] = matches
                else:
                    urls[author].extend(matches)
        return urls

    def getImages(self, submission, lstModelObj, queue, specialString=None, specialCount=None, specialPath=None):
        """
        Get Images from the submission

        :param lstModelObj: The User or Subreddit "ListModel" Object
        :param specialString: An optional string to specify additional information in the filename e.g. _comment_ if it is a comment image
        :param specialCount: An optional int to specify additional information in the filename about e.g. the number of this comment image
        :param specialPath: An optional string to specify additional information about where the image should be saved to

        :type submission: praw.objects.Submission
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type queue: Queue.queue
        :type specialString: str
        :type specialCount: str
        :type specialPath: str

        :rtype: generator
        """
        imageFinder = None
        imageFinderDomains = {
            self._supportedDomains[0]: ImgurImageFinder(lstModelObj.externalDownloads, self.avoidDuplicates, queue, self.imgurAPIClientID),
            self._supportedDomains[1]: MinusImageFinder(lstModelObj.externalDownloads, self.avoidDuplicates, queue),
            self._supportedDomains[2]: VidbleImageFinder(lstModelObj.externalDownloads, self.avoidDuplicates, queue),
            self._supportedDomains[3]: GfycatImageFinder(lstModelObj.externalDownloads, self.avoidDuplicates, queue)}

        if self.imgurAPIClientID is None:
            del imageFinderDomains['imgur']

        domains = imageFinderDomains.keys()

        for domain in domains:
            if domain in submission.domain:
                imageFinder = imageFinderDomains.get(domain)
                break
        if imageFinder is None:
            imageFinder = ImageFinder(queue)  # default to a basic image finder if no supported domain is found
        images = imageFinder.getImages(submission, self.defaultPath, lstModelObj, specialString, specialCount, specialPath)
        for image in images:
            yield image

    def getValidSubmissions(self, submitted, lstModelObj):
        """
        Return valid submissions, meaning they pass all the requirements in _isValidSubmission()
        and if it is user_subreddit_constrained the submission is in a selected subreddit.

        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type submitted: generator
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :rtype: generator
        """
        validSubreddits = None
        if self.downloadType is DownloadType.USER_SUBREDDIT_CONSTRAINED:
            validSubreddits = self.subredditLists.get(self.currentSubredditListName).stringsInLst
        for submission in submitted:
            subreddit = submission.subreddit.display_name
            validSubreddit = validSubreddits is None or subreddit.lower() in validSubreddits
            if validSubreddit and self._isValidSubmission(submission, lstModelObj):
                yield submission, (
                not self.filterSubmissionContent and not self.filterExternalContent or self._submissionPassesFilter(submission))

    def getSubredditSubmissions(self, validSubreddit):
        """
        Based on the subreddit sorting setting, and the subLimit, return the submissions for
        a subreddit.
        :type validSubreddit: praw.objects.Subreddit
        :rtype: generator
        """
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
        return contentFunc(limit=self.subLimit)

    def downloadSubmission(self, submission, user=""):
        """
        Download the JSON content of a submission to the downloads directory.
        :param user: Optional parameter specifying where this submission data is going to be saved to. If user is not empty string, it goes in a user folder, otherwise it goes in a subreddit folder
        :type submission: praw.objects.Submission
        :type user: str
        :rtype: tuple
        """
        MAX_PATH = 260  # Windows is stupid and only lets you make paths up to a length of 260 chars
        if user != "":
            directory = self.defaultPath / user
        else:
            subreddit = submission.subreddit.display_name
            directory = self.defaultPath / subreddit
        title = re.sub('[^\w\-_\. ]', '', submission.title)
        path = directory / (title + '.txt')
        if len(str(path)) > MAX_PATH:
            lenOver = len(str(path)) - MAX_PATH
            title = title[:-(lenOver + len('.txt'))]
            path = directory / (title + '.txt')
        try:
            with path.open('w') as f:
                json.dump(self._getSubmissionData(submission), f, ensure_ascii=True)
                return True, path
        except:
            return False, path

    def getCommentImages(self, submission, lstModelObj, queue):
        """
        Get Images from comments in a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object

        :type submission: praw.objects.Submission
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type queue: Queue.queue
        :rtype: generator
        """
        origSubmissionURL = submission.url  # We're going to be hijacking these variables to use self.getImages
        origSubmissionDomain = submission.domain
        commentImageURLs = self._getCommentImageURLs(submission)
        for author in commentImageURLs:
            urls = commentImageURLs.get(author)
            count = 1
            for url in urls:
                if url.lstrip().startswith("http"): # sometimes the regex returns matches without http in the front.
                    canDownload = self._fudgeSubmissionDomainAndURL(submission, url)
                    if canDownload:
                        images = self.getImages(submission, lstModelObj, queue, "_comment_", count, author)
                        count += 1
                        for image in images:
                            yield image
        submission.url = origSubmissionURL  # Restore the submission info back to what it was
        submission.domain = origSubmissionDomain

    def getSelftextImages(self, submission, lstModelObj, queue):
        """
        Get Images from selftext of a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object

        :type submission: praw.objects.Submission
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type queue: Queue.queue
        :rtype: generator
        """
        origSubmissionURL = submission.url  # We're going to be hijacking these variables to use self.getImages
        origSubmissionDomain = submission.domain
        if submission.is_self:
            urls = self._urlFinder.findall(submission.selftext)
            count = 1
            for url in urls:
                if url.lstrip().startswith("http"): # sometimes the regex returns matches without http in the front.
                    canDownload = self._fudgeSubmissionDomainAndURL(submission, url)
                    if canDownload:
                        images = self.getImages(submission, lstModelObj, queue, "_selftext_", count)
                        count += 1
                        for image in images:
                            yield image
        submission.url = origSubmissionURL  # Restore the submission info back to what it was
        submission.domain = origSubmissionDomain


    def changeDownloadType(self, downloadType):
        """
        Used like this rather than directly changing the variable because it is tied to a button .clicked call
        :type downloadType: DownloadType
        """
        self.downloadType = downloadType

    def makeDirectory(self, dirName):
        """
        Make a directory in the default path with name of dirName
        :type dirName: str
        """
        directory = self.defaultPath / dirName
        if not directory.exists():
            directory.mkdir(parents=True)

    def mapFilterTextToOper(self, text):
        """
        Function to get an operation function given the text it is connected to.
        :type text: str
        :rtype: function
        """
        return self.operMap.get(text)

    def mapConnectorTextToOper(self, text):
        """
        Function to get a connector function given the text it is connected to.
        :type text: str
        :rtype: function
        """
        return self.connectMap.get(text)


    def getRedditor(self, userName):
        """
        Validate a redditor with the given userName
        :type userName: str
        :rtype: praw.objects.Redditor
        """
        try:
            redditor = self._r.get_redditor(userName)
        except requests.exceptions.HTTPError:
            redditor = None
        return redditor

    def getSubreddit(self, subredditName):
        """
        Validate a subreddit with the given subredditName
        :type userName: str
        :rtype: praw.objects.Redditor
        """
        try:
            subreddit = self._r.get_subreddit(subredditName, fetch=True)
        except:
            subreddit = None
        return subreddit

    def saveState(self):
        """
        Save the RedditDataExtractor using shelf (pickle) and return a boolean indicating success / failure
        Some GUI objects are temporarily made None because they are not pickleable -- but that's okay
        because we can just pickle their underlying list
        :rtype: bool
        """
        successful = False
        if not self.currentlyDownloading:
            userListModels = self.userLists
            userListSettings = {}  # Use this to save normally unpickleable stuff
            subredditListModels = self.subredditLists
            subredditListSettings = {}
            commentCache = self._commentCache
            self._commentCache = {}
            for key, val in userListModels.items():
                userListSettings[key] = val.lst
            for key, val in subredditListModels.items():
                subredditListSettings[key] = val.lst
            shelf = shelve.open(str(pathlib.Path("RedditDataExtractor", "saves", "settings.db")))
            try:
                self.userLists = None  # QAbstractListModel is not pickleable so set this to None
                self.subredditLists = None
                shelf['rddtDataExtractor'] = self
                shelf['userLists'] = userListSettings  # Save QAbstractList data as a simple dict of list
                shelf['subredditLists'] = subredditListSettings
                print("Saving program")
                successful = True
            except KeyError:
                print("save fail")
                successful = False
            finally:
                shelf.close()
                self.userLists = userListModels  # Restore the user lists in case the user is not exiting program
                self.subredditLists = subredditListModels
                self._commentCache = commentCache
        return successful
