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
:license: GNU GPLv3, see LICENSE.txt for more details.

"""

__title__ = 'reddit Data Extractor'
__version__ = '1.0'
__build__ = 0x010000
__author__ = 'J Nicolas Schrading'
__license__ = 'GNU GPLv3'
__copyright__ = 'Copyright 2014 J Nicolas Schrading'