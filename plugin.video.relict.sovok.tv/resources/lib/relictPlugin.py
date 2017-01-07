from resources.lib.simpleplugin.simpleplugin import Plugin
from resources.lib.simpleplugin.simpleplugin import Storage
import xbmcgui
import xbmc
from cPickle import dump, load, PickleError
from datetime import datetime, timedelta
import gzip
import os


class RelictStorage(Storage):

    def __init__(self, storage_dir, filename='storage.pcl'):
        """
        Class constructor

        @param storage_dir: directory for storage
        @type storage_dir: str
        @param filename: the name of a storage file (optional)
        @type filename: str
        @return:
        """
        xbmc.log('Init storage %s' % filename)
        self._storage = {}
        self.filename = os.path.join(storage_dir, filename)
        if os.path.exists(self.filename):
            mode = 'r+b'
            _file_gzip = gzip.open(self.filename, mode)
            try:
                self._storage = load(_file_gzip)
            except (PickleError, EOFError):
                pass
            _file_gzip.close()
        xbmc.log('The storage %s is ready' % filename)

    def clean(self):
        current_time = datetime.now()
        for key in self.keys():
            if u'ttl' in self[key]:
                if (current_time - self[key][u'timestamp']) > timedelta(
                        minutes=int(self[key][u'ttl'])):
                    del self[key]

    def save(self):
        """
        Flush storage to disk

        This method invalidates a Storage instance.
        @return:
        """
        mode = 'wb'
        _file_gzip = gzip.open(self.filename, mode)

        self.clean()
        dump(self._storage, _file_gzip)
        # self._file.truncate()
        _file_gzip.flush()

    def flush(self):
        """
        Flush storage to disk

        This method invalidates a Storage instance.
        @return:
        """
        mode = 'wb'
        _file_gzip = gzip.open(self.filename, mode)
        dump(self._storage, _file_gzip)
        # self._file.truncate()
        _file_gzip.close()
        del _file_gzip
        del self._storage


class RelictPlugin(Plugin):
    def get_storage(self, filename='storage.pcl'):
        """
        Get a persistent Storage instance for storing arbitrary values between addon calls.

        A Storage instance can be used as a context manager.

        Example::

            with plugin.get_storage() as storage:
                storage['param1'] = value1
                value2 = storage['param2']

        Note that after exiting 'with' block a Storage instance is invalidated.
        @param filename: the name of a storage file (optional)
        @type filename: str
        @return: L{Storage} object
        """
        return RelictStorage(self.config_dir, filename)

    def get_plugin_url(self):
        return self._url

    def _create_listing(self, context):
        super(RelictPlugin, self)._create_listing(context)
        if u'focus_item_idx' in context:
            try:
                win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
                win.getControl(win.getFocusId()).selectItem(context[u'focus_item_idx'] + 1)
            except:
                self.log(' cannot to select %s item' % context[u'focus_item_idx'], xbmc.LOGERROR)
