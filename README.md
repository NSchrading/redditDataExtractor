Note: This project is no longer supported. The frozen executable releases may continue to work; however, changes to the reddit API have rendered the current version built from source obsolete. You are welcome to fork and make improvements if you wish.

A similar but still supported tool exists here: https://github.com/MalloyDelacroix/DownloaderForReddit

Requirements
==================
* Python3.4
* PyQt4
* praw
* beautifulsoup4
* requests
* youtube-dl

You can download a standalone executable (for Windows or Linux 64-bit) if you don't want to compile from source here: https://github.com/NSchrading/redditDataExtractor/releases

The reddit Data Extractor
===================

![Main application](http://i.imgur.com/ekuaFS9.png)


The reddit Data Extractor is a cross-platform GUI tool for downloading almost any content posted to reddit. Downloads from specific users, specific subreddits, users by subreddit, and with filters on the content is supported. Some intelligence is built in to attempt to avoid downloading duplicate external content.

For data scientists and curious redditors, JSON-encoded text files can be extracted for analysis. These contain all the characteristics of reddit submissions, including the title, a hierarchy of comments, the score, selftext, creation date, and more. Below is a snippet of some of the attributes that are retrieved.

![JSON encoded submission data](http://i.imgur.com/lKxB3Hl.png)


For redditors who want to easily retrieve submitted images, gifs, webms, and videos, or for people interested in training machine learning applications that link semantic content (submission data) with images, the reddit data extractor supports you as well. Imgur*, Gfycat, Vidble, and Minus are specifically supported, and any direct link to an image should work as well. In addition, any video site supported by the youtube-dl project is also supported (http://rg3.github.io/youtube-dl/supportedsites.html).

\* Imgur requires a client-id for non-direct links - see Site specific notes for more details.

External content can be downloaded from submission links, comments, and selftext.

Filters can be set to download only those submissions, or those submission's external content, passing the filter criteria.

Here are all the settings available:

![Settings](http://i.imgur.com/8NJpYBO.png)

* Default User List: The user list that will display on starting the program.
* Default Subreddit List: The subreddit list that will display on starting the program.
* Display Imgur API Notification on Startup if No Client-id is Set: Uncheck this to stop the program from notifying you that you need an imgur client-id.
* Change / Reset Client-id: Check this to change or reset your Imgur client-id.
* Sort Subreddit Content by: Select the sorting method used when obtaining submissions from subreddits. 'New' is the only method that you will be able to use if want to restrict the retrieved submissions by creation date. (Only affects downloads when using the "Subreddits in List" download option)
* Max Posts Retrieved in Subreddit Content Download: The number of submissions that will be examined for downloading per subreddit (Only affects downloads when using the "Subreddits in List" download option)
* Download External Content of Submission: Select this to download the external images / gifs / webms linked by a non-selftext submission to reddit.
* Download External Content Linked in Comments: Select this to download any external images / gifs / webms linked to by comments in the submission.
* Download Submission Content: Select this to download JSON-encoded submission data representing the submission's properties.
* Download External Content Linked in Selftext: Select this to download any external images / gifs / webms linked to in the selftext of a reddit submission.
* Avoid downloading Duplicate Images If Possible: Select this to attempt to avoid downloading images that have already been downloaded. This works per-user or per-subreddit, so if multiple users submit the same image, the reddit Data Extractor may still download both.
* Do Not Download Videos: Select this to prevent the downloader from downloading video content linked by the submission, comments, or selftext.
* Only Download Author's Comment External Content: Select this to only download external content in comments if it is the original author of the submission making the comment. This will also download deleted author comments just in case the original author was the one that was deleted.
* Restrict retrieved submissions to creation dates after the last downloaded submission: Select this to prevent the reddit Data Extractor from viewing submissions posted before the last downloaded submission. This will always work for downloads by user, but will only work for downloads by subreddit if you use the "New" sorting method. This option may speed up the time it takes to finish downloading. Deselect this option if you had failures on downloading content and wish to re-attempt to download them.
* Only download external content when: Select this and then enter values into the table below to filter submissions and only download their external content when they pass the filter.
* Only download submission content when: Select this and then enter values into the table below to filter submissions and only download their JSON-content when they pass the filter.
  * If you wish to have multiple filters you can only use one type to group them: AND, OR, or XOR. Not a combination of them.
  * Filters on comments will pass the submission if *ANY* of the comments pass the filter. Currently there is no way to filter if all comments pass the filter.
  * The values you enter are case-sensitive.
  * If you select the "Equals Bool" operator, enter True or False in the Value box.


Right clicking on a user or subreddit in the user or subreddit list that has already had content downloaded for them and selecting 'view downloaded posts' will display a preview of the downloaded content, broken up by JSON-encoded submission content, external submission links, comment links, and selftext links.

![Downloaded content gui](http://i.imgur.com/hFS58uy.png)

Clicking on the display images will take you to the reddit submission from which the content was downloaded. Right clicking the submission (to the right of the image) will allow you to delete the content. Deselecting the 'restrict retrieved submissions to creation dates after the last downloaded submission' checkbox in the settings will then allow you to redownload the content. Or if you never want to download that content again, you can select 'delete content and never download again' which will blacklist it.

Add/Remove Users/Subreddits by clicking the +/- buttons or selecting File->New. Edit their names by double clicking on the "new list item" entry in the lists. Right click on the user/subreddit list dropdown or hit File->New to make new user or subreddit lists to download from. In this way you can organize users or subreddits to download from so that your downloads go faster if you only want to download from a specific subset.

The reddit data extractor will remember your settings and the users and subreddits you downloaded from, as long as you save before exiting. If you wish to delete a save, remove the 3 files under RedditDataExtractor/saves called settings.db.bak, settings.db.dat, and settings.db.dir.

If you remove a user or subreddit from the list, the program will lose all memory of having downloaded content from them, allowing you to redownload everything again. Removing them will not delete their already downloaded content from your computer, however.

Hit View->Remaining Imgur Requests (if you have set an Imgur client-id) to see how many requests you have left to make this day. Do not exceed this limit or you may be rate-limited or banned by Imgur.

<dl>
  <dt>The following file types are supported:</dt>
  <dd>jpg, png, gif, webm</dd>
  <dd>Any video file type supported by the youtube-dl project</dd>
</dl>
  
<dl>
  <dt>Site specific notes:</dt>
  <dd>Imgur page, gallery, and album links will only be downloadable if you obtain an Imgur API client-id and enter it into the reddit data extractor. You can obtain a client-id here: https://api.imgur.com/oauth2/addclient. <br>Suggested data to enter:<br>Application name: reddit Data Extractor<br/>Authorization type: Anonymous usage without user authorization<br/>Authorization callback URL: https://www.google.com (or any valid URL -- it doesn't matter for anonymous usage)<br/>Application website: https://github.com/NSchrading/redditDataExtractor<br/>Email: Your email address to send the client-id to.</dd>
  <dd>Minus galleries are not currently supported - only page and direct links.</dd>
</dl>

### Running the reddit Data Extractor

If you downloaded the executable files (found here: https://github.com/NSchrading/redditDataExtractor/releases), open the folder that was downloaded. Inside you will see a bunch of .dll files or .so files. Also included in the mess of files is the executable:

![Executable](http://i.imgur.com/i3W9uF4.png)

On windows it is called redditDataExtractor.exe. On Linux it is called redditDataExtractor. On linux, run it by typing in the console:

        ./redditDataExtractor
        
On windows, simply double click the .exe.

### Installing the reddit Data Extractor from Source

The reddit Data Extractor has been tested and is working for 64-bit versions of both Windows 8 and Linux Mint 16. Precompiled versions of the program are available for download if you don't want to go through the arduous process of installing PyQt. These are found under the releases section: https://github.com/NSchrading/redditDataExtractor/releases

If you do wish to run the program from source, below are the steps I took to run them on Windows and Linux. A slightly different process may be required for versions of linux not based off of Ubuntu. In general, Python 3.4, PyQt4, PRAW, BeautifulSoup4, Requests, and youtube-dl are required.

##### Linux
    [sudo] apt-get install libxext-dev python-qt4 qt4-dev-tools libqt4-dev libqt4-core libqt4-gui build-essential

Download SIP: http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.2/sip-4.16.2.tar.gz/

Download PyQt: http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.1/PyQt-x11-gpl-4.11.1.tar.gz/

Extract both tarballs

    cd sip-4.16.2
    python configure.py
    make
    [sudo] make install
    
    cd PyQt-x11-gpl-4.11.1
    python configure.py
    make
    [sudo] make install

###### Warning: Compiling / linking PyQt will take a while.
When that's done:

    [sudo] pip install -r requirements.txt
    
    ~OR~
    
    [sudo] pip install praw
    [sudo] pip install requests
    [sudo] pip install beautifulsoup4
    [sudo] pip install youtube-dl
    
And now you should be ready to run the reddit Data Extractor! main.py is where all the magic starts.

    python main.py
    
##### Windows

Download Python 3.4 for 64-bit or 32-bit systems:
https://www.python.org/downloads/release/python-340/

Download the PyQt4 64-bit installer built for python 3.4: http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.1/PyQt4-4.11.1-gpl-Py3.4-Qt4.8.6-x64.exe

Or the PyQt4 32-bit installer built for python 3.4:
http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.1/PyQt4-4.11.1-gpl-Py3.4-Qt4.8.6-x32.exe
    
    Run the installer.
    
    pip install -r requirements.txt
    
    ~OR~
    
    pip install praw
    pip install requests
    pip install beautifulsoup4
    pip install youtube-dl
    
And now you should be ready to run the reddit Data Extractor! main.py is where all the magic starts.

    python main.py
