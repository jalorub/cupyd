from traceback import TracebackException

from cupyd.core.constants.node_actions import NODE_ACTIONS


class NodeException:
    def __init__(self, exc: Exception, action: str):
        if isinstance(exc, Exception):
            self.exc = exc
        else:
            raise TypeError("Input exception isn't one!")
        if action not in NODE_ACTIONS:
            raise ValueError(f"Node action {action} not recognized")
        else:
            self.action = action

        traceback_exc = TracebackException.from_exception(exc=self.exc)
        traceback_formatted = list(traceback_exc.format())
        self.traceback_formatted = "".join(traceback_formatted)

    def __str__(self):
        return f"{self.action}: {self.exc}"

    def __repr__(self):
        return str(self)
