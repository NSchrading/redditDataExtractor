import sys
import requests.certs
import py_compile
from cx_Freeze import setup, Executable


'''
Note: with version 3.0.0 of PRAW, you need to modify PRAW for downloads to work
I need to figure out a better way to go about this, but for now this works

add a line to praw/handlers.py
    def __init__(self):
        """Establish the HTTP session."""
        self.http = Session()  # Each instance should have its own session
        self.http.verify = 'RedditDataExtractor/cacert.pem'       # <-------------- add this
'''


zip_includes = []
includes = ["atexit", "re", "sip"]

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
    prawIniLoc = 'C:/Python34/Lib/site-packages/praw/praw.ini'
    targetName = 'redditDataExtractor.exe'
else:
    prawIniLoc = '/usr/local/lib/python3.4/site-packages/praw/praw.ini'
    # for some reason my computer couldn't find ntpath.py to include it in the zip
    py_compile.compile('/usr/local/lib/python3.4/ntpath.py', cfile='ntpath.pyc')
    zip_includes = ['ntpath.pyc']
    targetName = 'redditDataExtractor'

packages = []

for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
        # If we found the module, ensure it's copied to the build directory.
        packages.append(dbmodule)

include_files = [('RedditDataExtractor/images', 'RedditDataExtractor/images'), (requests.certs.where(),'RedditDataExtractor/cacert.pem'), (prawIniLoc, 'praw.ini')]

setup(
    name='RedditDataExtractor',
    version='1.0',
    packages=['test', 'RedditDataExtractor', 'RedditDataExtractor.GUI'],
    url='',
    license='GNU GPLv3',
    author='J Nicolas Schrading',
    author_email='NSchrading@gmail.com',
    description='The reddit Data Extractor is a GUI tool for downloading almost any content posted to reddit.',
    options = {"build_exe": {'includes': includes, 'packages': packages, 'include_files': include_files, 'zip_includes': zip_includes, 'copy_dependent_files': True, 'icon': 'RedditDataExtractor/images/logo.ico'}},
    executables = [Executable("main.py", base=base, targetName=targetName)]
)