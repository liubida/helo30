import threading

class singleton:
    _instance_lock = threading.Lock() 
    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """ 
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        if not hasattr(self, '_instance'):
            with singleton._instance_lock:
                if not hasattr(self, '_instance'):
                    self._instance = self._decorated()

        return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
