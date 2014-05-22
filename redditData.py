import praw
import datetime
import requests
import re
import os
import optparse
import pprint
import shelve
import threading
import multiprocessing
from bs4 import BeautifulSoup
from imageFinder import ImageFinder
from ImgurImageFinder import ImgurImageFinder
from user import User
from userListModel import UserListModel

""" Saving File Scheme:
Album: BaseDirectory/username/submissionID #.filetype -- # is the nunber of that pic in the album
Image: BaseDirectory/username/submissionID.filetype
"""

nullToNoneRegex = re.compile("null")
validSubreddits = set(["adviceanimals", "aww", "books", "earthporn", "funny", "gaming", "gifs", "movies", "music", "pics", "science", "technology", "television", "videos", "wtf"])
defaultPath = os.path.abspath(os.path.expanduser('Downloads'))

class RedditData():
    __slots__ = ('defaultPath', 'subredditSets', 'userLists', 'currentSubredditSetName', 'currentUserListName', 'defaultSubredditSetName', 'defaultUserListName', 'downloadedUserPosts', 'r')

    def __init__(self, defaultPath=defaultPath, subredditSets={'Default Subs' : validSubreddits}, userLists={'Default User List' : UserListModel([])}, currentSubredditSetName='Default Subs', currentUserListName='Default User List', defaultSubredditSetName='Default Subs', defaultUserListName='Default User List'):
        self.defaultPath = defaultPath
        self.subredditSets = subredditSets
        self.userLists = userLists
        self.currentSubredditSetName = currentSubredditSetName
        self.currentUserListName = currentUserListName
        self.defaultSubredditSetName = defaultSubredditSetName
        self.defaultUserListName = defaultUserListName
        self.downloadedUserPosts = {}
        self.r = praw.Reddit(user_agent = 'RedditUserScraper by /u/VoidXC')


    def downloadUserProcess(self, user):
        print("Starting download for: " + user)
        self.makeDirectoryForUser(user)
        if userNotInBlacklist(user, self.defaultPath):
            try:
                user = self.r.get_redditor(user)
            except requests.exceptions.HTTPError:
                addUserToBlacklist(user, self.defaultPath)
            # Temporary
            refresh = None
            #numPosts = None if options.refresh == 0 else options.refresh
            submitted = user.get_submitted(limit=refresh)
            posts = self.getValidPosts(submitted)
            ''' TEMP: Add link posts to images so we can delete images via gui by specifying post
            for post in posts:
                self.addPostToUserDownloads(post)
            '''
            images = self.getImages(posts)
            for image in images:
                if image is not None:
                    image.download()

    def downloadThread(self):
        jobs = []
        for user in self.userLists.get(self.currentUserListName):
            process = multiprocessing.Process(target=self.downloadUserProcess, args=(user,))
            jobs.append(process)
        for process in jobs:
            process.start()
            
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

    def addPostToUserDownloads(self, post):
        user = post.author.name
        downloads = self.downloadedUserPosts.get(user)
        link = '<a href="' + post.permalink + '">' + post.permalink + '</a>' 
        if downloads is None:
            self.downloadedUserPosts[user] = set([link])
        else:
            self.downloadedUserPosts.get(user).add(link)

    def getValidPosts(self, submitted):
        posts = []
        for post in submitted:
            subreddit = post.subreddit.display_name
            if subreddit.lower() in [sreddit.lower() for sreddit in self.subredditSets.get(self.currentSubredditSetName)] and self.isValidPost(post):
                posts.append(post)
        return posts

    def isValidPost(self, post):
        ''' Determines if this is a good post to download from
        Valid if:
            it is from imgur
            it is a new submission (meaning the files have not been downloaded from this post already)
            it is not a xpost from another subreddit which is itself a valid subreddit (to avoid duplicate file downloads)
            it is not in a blacklist
        '''
        return self.isNewSubmission(post) and self.isNotXPost(post) and isNotInBlacklist(post, self.defaultPath)
    

    def isNewSubmission(self, post):
        user = post.author.name
        url = post.url
        downloads = self.downloadedUserPosts.get(user)
        return downloads is None or url not in downloads

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
        try:
            shelf = shelve.open("settings.db")
            rddtScraper = shelf['rddtScraper']
            rddtScraper.downloadedUserPosts = self.downloadedUserPosts
            shelf['rddtScraper'] = rddtScraper
        except KeyError:
            pass
        finally:
            shelf.close()

def getUser():
    return input("Enter user to scrape info from: ")

def getDirectory():
    return input("Enter path to save files in: ")  

def isNotInBlacklist(post, defaultPath):
    user = post.author.name
    postID = post.id
    path = os.path.abspath(os.path.join(defaultPath, user, "blacklist.txt"))
    if os.path.exists(path):
        with open(path, "r") as blacklist:
            for line in blacklist:
                if postID in line:
                    return False
    return True

def addToUserSpecificBlacklist(postID, user, defaultPath):
    path = os.path.abspath(os.path.join(defaultPath, user, "blacklist.txt"))
    with open(path, "a") as blacklist:
        blacklist.write(postID + "\n")

def check503BytesFile(savePath):
    """ Sometimes the content-length is not included in the response headers, but it is still a deleted image (503 bytes) 
    Returns True if it deleted a 503 byte file """
    if os.stat(savePath).st_size == 503:
        os.remove(savePath)
        return True
    return False

def addUserToBlacklist(user, defaultPath):
    answer = input("User: " + user + " does not exist or no longer exists. Add to blacklist so no downloads from this name will be attempted in the future? (yes/y/no/n)\n").lower()
    while answer != 'y' and answer != 'yes' and answer != 'n' and answer != 'no': 
        answer = input("You must enter yes/y or no/n\n").lower()
    if answer == 'y' or answer == 'yes':
        with open(os.path.abspath(os.path.join(defaultPath, "blacklist.txt")), "a") as blacklist:
            blacklist.write(user + "\n")
            print("User: " + user + " successfully added to blacklist.")

def userNotInBlacklist(user, defaultPath):
    path = os.path.abspath(os.path.join(defaultPath, "blacklist.txt"))
    if os.path.exists(path):
        with open(path, "r") as blacklist:
            for line in blacklist:
                if user in line:
                    return False
    return True

def main():
    parser = optparse.OptionParser()
    parser.add_option("-u", "--user", action="store", type="string", dest="user", help="The reddit username of the user to get content from.")
    parser.add_option("-d", "--directory", action="store", type="string", dest="directory", help="The full path to the directory that the gw content should be saved in.")
    parser.add_option("-r", "--refresh", action="store", type="int", dest="refresh", help="Use this option to look for any new posts by already downloaded users in the given directory. The number specified is how many posts to look up, starting from the user's most recent posts. 0 means all posts.")
    options, args = parser.parse_args()

    user = None
    if options.user is None and options.refresh is None:
        user = getUser()
    else:
        user = options.user
    if options.directory is None:
        defaultPath = os.getcwd()
    else:
        defaultPath = options.directory
    r = praw.Reddit(user_agent = 'GWUserScraper by /u/VoidXC')
    if options.refresh is None and userNotInBlacklist(user, defaultPath):
        makeDirectoryForUser(user, defaultPath)
        try:
            user = r.get_redditor(user)
        except requests.exceptions.HTTPError:
            addUserToBlacklist(user, defaultPath)
            return
        submitted = user.get_submitted(limit=None)
        GWPosts = getGWPosts(submitted, defaultPath)
        getImages(GWPosts, defaultPath)
    elif options.refresh is not None:
        dledUsers = next(os.walk(defaultPath))[1] # os.walk returns list of [currentPath, directories, filenames]. [1] Gets the directories
        for user in dledUsers:
            if userNotInBlacklist(user, defaultPath):
                try:
                    user = r.get_redditor(user)
                except requests.exceptions.HTTPError:
                    addUserToBlacklist(user, defaultPath)
                    print("Continuing to next user...")
                    continue
                numPosts = None if options.refresh == 0 else options.refresh
                submitted = user.get_submitted(limit=numPosts)
                GWPosts = getGWPosts(submitted, defaultPath)
                getImages(GWPosts, defaultPath)
    else:
        print("User: " + user + " is currently in the blacklist.")

if __name__ == "__main__":
    main()
