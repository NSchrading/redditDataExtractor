"""
-----------------------------------------------------------------------------------------------------------------------
Reddit Data Extractor
-----------------------------------------------------------------------------------------------------------------------

The Reddit Data Extractor is a GUI tool for downloading almost any content posted to Reddit.

Downloads from specific users, specific subreddits, users by subreddit, and with filters on
the content is supported. Some intelligence is built in to attempt to avoid downloading duplicate external content.

Submission data downloads are saved as .txt files in JSON format.
External content like images and gifs can also be downloaded if they are from a supported site or
are linked directly (e.g. http://www.somerandomsite.com/foo.jpg).

Supported sites:
Imgur
Gfycat
Vidble
Minus

Supported external file types:
jpeg / jpg
png
gif
webm

:copyright: (c) 2014 by J Nicolas Schrading.
:license: GNU GPLv3, see LICENSE for more details.

"""

__title__ = 'RedditDataExtractor'
__version__ = '1.0'
__build__ = 0x010000
__author__ = 'J Nicolas Schrading'
__license__ = 'GNU GPLv3'
__copyright__ = 'Copyright 2014 J Nicolas Schrading'