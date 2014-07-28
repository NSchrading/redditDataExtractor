import sys
import shutil
import os
import requests.certs
from cx_Freeze import setup, Executable

# python setup.py build

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

includes = ["atexit", "re", "sip", 'requests', 'http.cookiejar', 'http.client', 'dummy_threading']

packages = []

for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
        # If we found the module, ensure it's copied to the build directory.
        packages.append(dbmodule)

include_files = [('RedditDataExtractor/images', 'RedditDataExtractor/images'), (requests.certs.where(),'RedditDataExtractor/cacert.pem')]

setup(
    name='RedditDataExtractor',
    version='1.0',
    packages=['test', 'RedditDataExtractor', 'RedditDataExtractor.GUI'],
    url='',
    license='GNU GPLv3',
    author='J Nicolas Schrading',
    author_email='NSchrading@gmail.com',
    description='The reddit Data Extractor is a GUI tool for downloading almost any content posted to reddit.',
    options = {"build_exe": {'includes': includes, 'packages': packages, 'include_files': include_files, 'copy_dependent_files': True}},
    executables = [Executable("main.py", base=base)]
)

shutil.copyfile('C:/Python34/Lib/site-packages/praw/praw.ini', os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'praw.ini'))