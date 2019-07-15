class EventArgs:
    """
    イベント引数
    """

    def __init__(self, params: dict = {}):
        self._params = params

    @property
    def params(self) -> dict:
        return self._params


class EventHandler:
    """
    イベントハンドラー
    """

    def __init__(self, obj):
        self._obj = obj
        self._funcs = []

    def add(self, func):
        self._funcs.append(func)

    def remove(self, func):
        self._funcs.remove(func)

    def fire(self, eargs: EventArgs):
        for func in self._funcs:
            func(self._obj, eargs)
