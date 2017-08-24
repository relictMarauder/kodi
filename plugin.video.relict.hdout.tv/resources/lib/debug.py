import os

__author__ = 'Alexander Bonelis'


class RemoteDebug:
    def __init__(self, debug):
        self.debug = debug
        self.pydevd = None
        if self.debug:
            self.pydevd = self.import_pydevd()

    @staticmethod
    def import_pydevd():
        import sys
        sys.path.append(os.path.normpath(r'p:\\home\\.IntelliJIdea\\config\\plugins\\python\\pycharm-debug.egg'))
        #sys.path.append(os.path.normpath(r'r:\\home\\.IntelliJIdea\\config\\plugins\\python\\helpers\\pydev'))
        # for comp in sys.path:
        #     if comp.find('addons') != -1:
        #         pydevd_path = os.path.normpath(os.path.join(comp, os.pardir, 'script.module.pydevd', 'lib'))
        #         sys.path.append(pydevd_path)
        #         break
        #     pass

        import pydevd
        return pydevd

    def start(self, host='localhost'):
        if self.debug:
            self.pydevd.settrace(host=host, stdoutToServer=True, stderrToServer=True, port=51768,
                                 suspend=True,
                                 # trace_only_current_thread=False,
                                 # overwrite_prev_trace=True,
                                 # patch_multiprocessing=True,
                                 )
            pass

    def stop(self):
        if self.debug:
            self.pydevd.stoptrace()
