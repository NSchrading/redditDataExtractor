import shelve
import sys
import os
from queue import Queue

from PyQt4.Qt import QApplication, QThread, QObject, pyqtSignal, pyqtSlot

from RedditDataExtractor.redditDataExtractor import RedditDataExtractor
from RedditDataExtractor.GUI.listModel import ListModel
from RedditDataExtractor.GUI.genericListModelObjects import User, Subreddit
from RedditDataExtractor.GUI.redditDataExtractorGUI import RddtDataExtractorGUI



class QueueMessageReceiver(QObject):
    """
    A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
    It blocks until data is available, and once it has got something from the queue, it sends
    it to the main GUI thread by emitting the pyqtSignal 'finished'
    """
    mysignal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = queue
        self.continueOperation = True

    @pyqtSlot()
    def run(self):
        while(self.continueOperation):
            text = self.queue.get()
            self.mysignal.emit(text)
        self.finished.emit()

    def stop(self):
        self.continueOperation = False
        self.queue.put("") # wake up the queue (it blocks until it gets something)

def loadState():
    print("attempting to load state")
    shelf = shelve.open(os.path.join("saves", "settings.db"))
    rddtDataExtractor = None
    try:
        rddtDataExtractor = shelf['rddtDataExtractor']
        userListSettings = shelf['userLists']
        subredditListSettings = shelf['subredditLists']
        rddtDataExtractor.userLists = {}
        rddtDataExtractor.subredditLists = {}
        for key, val in userListSettings.items():
            print("loading from saved " + key)
            rddtDataExtractor.userLists[key] = ListModel(val, User)
        for key, val in subredditListSettings.items():
            print("loading from saved " + key)
            rddtDataExtractor.subredditLists[key] = ListModel(val, Subreddit)
    except KeyError as e:
        print(e)
    finally:
        shelf.close()
        return rddtDataExtractor

def main():
    a = QApplication(sys.argv)
    rddtDataExtractor = loadState()
    if rddtDataExtractor is None:
        print("rddt data client was None, making new one")
        rddtDataExtractor = RedditDataExtractor()
    rddtDataExtractor.currentlyDownloading = False # If something weird happened to cause currentlyDownloading to be saved as True, set it back to False
    queue = Queue()
    thread = QThread()
    recv = QueueMessageReceiver(queue)
    w = RddtDataExtractorGUI(rddtDataExtractor, queue, recv)
    recv.mysignal.connect(w.append_text)
    recv.moveToThread(thread)
    thread.started.connect(recv.run)
    recv.finished.connect(thread.quit)
    recv.finished.connect(recv.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()

    w.show()

    sys.exit(a.exec_())


if __name__ == "__main__":
    main()
