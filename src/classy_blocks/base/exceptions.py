class VertexNotFoundError(Exception):
    """Raised when a vertex at a given point in space doesn't exist yet"""


class EdgeNotFoundError(Exception):
    """Raised when an edge between a given pair of vertices doesn't exist yet"""


class UndefinedGradingsError(Exception):
    """Raised when the user hasn't supplied enough grading data to
    define all blocks in the mesh"""
