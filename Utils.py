class Source:
    __slots__ = ('func', 'url', 'loop', 'stream')

    def __init__(self, func, url, loop, stream):
        self.func = func
        self.url = url
        self.loop = loop
        self.stream = stream

    def __getitem__(self, item):
        try:
            return self.__getattribute__(item)
        except:
            pass

    def __iter__(self):
        yield self.func
        yield self.url
        yield self.loop
        yield self.stream
