The reddit Data Extractor
===================

![Main application](http://i.imgur.com/ekuaFS9.png)


The reddit Data Extractor is a cross-platform GUI tool for downloading almost any content posted to reddit. Downloads from specific users, specific subreddits, users by subreddit, and with filters on the content is supported. Some intelligence is built in to attempt to avoid downloading duplicate external content.

For data scientists and curious redditors, JSON-encoded text files can be extracted for analysis. These contain all the characteristics of reddit submissions, including the title, a hierarchy of comments, the score, selftext, creation date, and more. Below is a snippet of some of the attributes that are retrieved.

![JSON encoded submission data](http://i.imgur.com/lKxB3Hl.png)


For redditors who want to easily retrieve submitted images, gifs, and webms, or for people interested in training machine learning applications that link semantic content (submission data) with images, the reddit data extractor supports you as well. Imgur*, Gfycat, Vidble, and Minus are specifically supported, and any direct link to an image should work as well.

\* Imgur requires a client-id for non-direct links - see Site specific notes for more details.

External content can be downloaded from submission links, comments, and selftext.

Filters can be set to download only those submissions, or those submission's external content, passing the filter criteria.

Here are all the settings available:

![Settings](http://i.imgur.com/f874li1.png)

Right clicking on a user or subreddit that has already had content downloaded for them will display a preview of the downloaded content, broken up by JSON-encoded submission content, external submission links, comment links, and selftext links.

![Downloaded content gui](http://i.imgur.com/hFS58uy.png)

Clicking on the display images will take you to the reddit submission from which the content was downloaded. Right clicking the submission (to the right of the image) will allow you to delete the content. Deselecting the 'restrict retrieved submissions to creation dates after the last downloaded submission' checkbox in the settings will then allow you to redownload the content. Or if you never want to download that content again, you can select 'delete content and never download again' which will blacklist it.

The reddit data extractor will remember your settings and the users and subreddits you downloaded from, as long as you save before exiting. If you wish to delete a save, remove the 3 files under RedditDataExtractor/saves called settings.db.bak, settings.db.dat, and settings.db.dir.

If you remove a user or subreddit from the list, the program will lose all memory of having downloaded content from them, allowing you to redownload everything again. Removing them will not delete their already downloaded content from your computer, however.

<dl>
  <dt>The following file types are supported:</dt>
  <dd>jpg, png, gif, webm</dd>
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

If you do wish to run the program from source, below are the steps I took to run them on Windows and Linux. A slightly different process may be required for versions of linux not based off of Ubuntu. In general, Python 3.4, PyQt4, PRAW, BeautifulSoup4, and Requests are required.

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
    
And now you should be ready to run the reddit Data Extractor! main.py is where all the magic starts.

    python main.py
    
##### Windows

Download the PyQt4 64-bit installer built for python 3.4: http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.1/PyQt4-4.11.1-gpl-Py3.4-Qt4.8.6-x64.exe
    
    Run the installer.
    
    pip install -r requirements.txt
    
    ~OR~
    
    pip install praw
    pip install requests
    pip install beautifulsoup4
    
And now you should be ready to run the reddit Data Extractor! main.py is where all the magic starts.

    python main.py
