class GraphException(Exception):
    pass


class CyclicNodeError(GraphException):
    pass


class NodesAlreadyConnectedError(GraphException):
    pass


class CyclicGraphError(GraphException):
    pass


class NodesConnectionError(GraphException):
    pass


class ETLExecutionError(Exception):
    pass


class InterruptedETL(Exception):
    pass
