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

import warnings
import pathlib
import youtube_dl

# Without this we get tons of warnings about unclosed sockets.
# Not sure if it's something I'm doing wrong or if it's a bug in Requests / PRAW / urllib
warnings.filterwarnings("ignore", category=ResourceWarning)


class Content():
    __slots__ = (
        'userOrSubName', 'submissionID', 'defaultPath', 'URL', 'redditSubmissionURL', 'numInSeq', 'savePath',
        'specialString', 'specialCount', 'specialPath')

    def __init__(self, userOrSubName, submissionID, defaultPath, URL, redditSubmissionURL, numInSeq="",
                 specialString=None, specialCount=None, specialPath=None):
        """
        Class to hold information about a single external file downloaded as content from a Reddit submission
        :param URL: The direct URL that this content is located at
        :param redditSubmissionURL: The permalink of the Reddit submission
        :param numInSeq: A string containing a number indicating the number that the image is in a sequence (if, e.g. it is from an album)
        :param specialString: An optional string to specify additional information in the filename e.g. _comment_ if it is a comment image
        :param specialCount: An optional int to specify additional information in the filename about e.g. the number of this comment image
        :param specialPath: An optional string to specify additional information about where the image should be saved to
        :type userOrSubName: str
        :type submissionID: str
        :type fileType: str
        :type defaultPath: pathlib.Path
        :type URL: str
        :type redditSubmissionURL: str
        :type numInSeq: str
        :type specialString: str
        :type specialCount int
        :type specialPath str
        """
        self.userOrSubName = userOrSubName
        self.submissionID = submissionID
        self.defaultPath = defaultPath
        self.URL = URL
        self.redditSubmissionURL = redditSubmissionURL
        self.numInSeq = numInSeq
        self.savePath = ""
        self.specialString = specialString
        self.specialCount = specialCount
        self.specialPath = specialPath
        self._makeSavePath()

    def _makeSavePath(self):
        if self.numInSeq != "":
            imageFile = self.submissionID + " " + str(self.numInSeq)
        else:
            imageFile = self.submissionID
        if self.specialString is not None and self.specialCount is not None:
            if self.numInSeq != "":
                imageFile = self.submissionID + self.specialString + str(self.specialCount) + " " + str(self.numInSeq)
            else:
                imageFile = self.submissionID + self.specialString + str(self.specialCount)
        if self.specialPath is not None:
            directory = self.defaultPath / self.userOrSubName / self.specialPath
            if not directory.exists():
                directory.mkdir(parents=True)
            self.savePath = directory / imageFile
        else:
            self.savePath = self.defaultPath / self.userOrSubName / imageFile


class Image(Content):
    # header in hex for image content that makes up a well-formed gif
    gifHeader = [hex(ord("G")), hex(ord("I")), hex(ord("F"))]

    __slots__ = (
        'userOrSubName', 'submissionID', 'fileType', 'defaultPath', 'URL', 'redditSubmissionURL', '_iterContent',
        'numInSeq', 'savePath', 'specialString', 'specialCount', 'specialPath')

    def __init__(self, userOrSubName, submissionID, fileType, defaultPath, URL, redditSubmissionURL, iterContent,
                 numInSeq="", specialString=None, specialCount=None, specialPath=None):
        """
        Class to hold information about a single image / gif / webm downloaded as content from a Reddit submission
        :param iterContent: The HTTP request's content broken up into chunks by the request library's iter_content generator
        :type iterContent: generator
        """
        super().__init__(userOrSubName, submissionID, defaultPath, URL, redditSubmissionURL, numInSeq, specialString,
                         specialCount, specialPath)
        self.fileType = fileType
        self._iterContent = iterContent
        self.savePath = pathlib.Path(str(self.savePath) + self.fileType)


    def _isActuallyGif(self):
        """
        If this image is actually a gif but the URL indicated it was a .jpg or .png we want to save it as a .gif and
        set its information to indicate that it is, in fact, a gif.
        """
        with self.savePath.open('rb') as f:
            for i in range(3):
                if hex(ord(f.read(1))) != Image.gifHeader[i]:
                    return False
            return True

    def download(self):
        try:
            with self.savePath.open('wb') as fo:
                for chunk in self._iterContent:
                    fo.write(chunk)
            filePath = self.savePath.parent
            fileName = self.savePath.stem
            fileExtension = self.savePath.suffix
            if fileExtension in {".jpg", ".jpeg", ".png"}:
                if self._isActuallyGif():
                    newPath = filePath / (fileName + ".gif")
                    self.savePath.rename(newPath)
                    self.savePath = newPath
                    self.fileType = ".gif"
            return True
        except:
            return False


class Video(Content):
    __slots__ = (
        'userOrSubName', 'submissionID', 'defaultPath', 'URL', 'redditSubmissionURL', 'numInSeq', 'savePath',
        'specialString', 'specialCount', 'specialPath', '_ydl')

    def __init__(self, userOrSubName, submissionID, defaultPath, URL, redditSubmissionURL, numInSeq="",
                 specialString=None, specialCount=None, specialPath=None):
        """
        Class to hold information about a single video downloaded as content from a Reddit submission
        """
        super().__init__(userOrSubName, submissionID, defaultPath, URL, redditSubmissionURL, numInSeq, specialString,
                         specialCount, specialPath)
        ydlOpts = {'outtmpl': str(self.savePath) + "_%(autonumber)s.%(ext)s", 'quiet': True, 'restrictfilenames': True,
                   'no_warnings': True, 'ignoreerrors': True, 'logtostderr': False, 'nooverwrites': False,
                   'logger': False, 'bidi_workaround': False}
        self._ydl = youtube_dl.YoutubeDL(ydlOpts)
        self._ydl.add_default_info_extractors()
        self._ydl.to_stderr = lambda: 1

    def download(self):
        success = False
        try:
            retcode = self._ydl.download([self.URL])
            if retcode == 0:
                # We don't have the extension or full name of the file yet. Figure it out
                possibleRealSavePath = pathlib.Path(self.savePath.parent)
                possibilities = list(possibleRealSavePath.glob(self.savePath.stem + '*'))
                if len(possibilities) > 0:
                    self.savePath = possibilities[0]
                    success = True
        except:
            success = False
        finally:
            return success
