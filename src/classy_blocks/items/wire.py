from typing import List, Set

from classy_blocks.items.vertex import Vertex
from classy_blocks.items.edges.edge import Edge
from classy_blocks.items.edges.line import LineEdge

from classy_blocks.grading.grading import Grading

class Wire:
    """Represents two vertices that define an edge;
    supplies tools to create and compare, etc"""
    def __init__(self, vertices:List[Vertex], axis:int, corner_1:int, corner_2:int):
        self.corners = [corner_1, corner_2]
        self.vertices = [vertices[corner_1], vertices[corner_2]]

        self.axis = axis

        # the default edge is 'line' but will be replaced if the user wishes so
        self.edge:Edge = LineEdge(*self.vertices)

        # grading/counts of this wire
        self.grading = Grading(self.edge.length)

        # up to 4 wires can be at the same spot; this list holds other
        # coincident wires
        self.coincidents:Set['Wire'] = set()

    @property
    def is_valid(self) -> bool:
        """A pair with two equal vertices is useless"""
        return self.vertices[0] != self.vertices[1]

    def is_coincident(self, wire:'Wire') -> bool:
        """Returns True if this wire is in the same spot than the argument,
        regardless of alignment"""
        return self.vertices == wire.vertices or \
            self.vertices == wire.vertices[::-1]

    def is_aligned(self, wire:'Wire') -> bool:
        """Returns true is this pair has the same alignment
        as the pair in the argument"""
        if not self.is_coincident(wire):
            raise RuntimeError(f"Wires are not coincident: {self}, {wire}")

        return self.vertices == wire.vertices

    def add_coincident(self, wire):
        """Adds a reference to a coincident wire, if it's aligned"""
        if self.is_coincident(wire):
            self.coincidents.add(wire)

    def __repr__(self):
        return f"Wire between {self.vertices} (corners {self.corners})"
