from typing import List, Set

from classy_blocks.base.exceptions import InconsistentGradingsError
from classy_blocks.grading.chop import Chop
from classy_blocks.grading.grading import Grading
from classy_blocks.items.vertex import Vertex
from classy_blocks.items.wires.manager import WireManager
from classy_blocks.items.wires.wire import Wire
from classy_blocks.types import AxisType


class Axis:
    """One of block axes, indexed 0, 1, 2
    and wires - edges that are defined along the same direction."""

    def __init__(self, index: AxisType, wires: List[Wire]):
        self.index = index
        self.wires = WireManager(wires)
        self.chops: List[Chop] = []

        # will be added after blocks are added to mesh
        self.neighbours: Set[Axis] = set()

    def add_neighbour(self, axis: "Axis") -> None:
        """Adds an 'axis' from another block if it shares at least one wire"""
        for this_wire in self.wires:
            for nei_wire in axis.wires:
                if this_wire.is_coincident(nei_wire):
                    self.neighbours.add(axis)

    def add_sequential(self, axis: "Axis") -> None:
        """Adds an axis that comes before/after this one"""
        # As opposed to neighbours that are 'around' this axis
        if self.start_vertices == axis.end_vertices or self.end_vertices == axis.start_vertices:
            for this_wire in self.wires:
                for nei_wire in axis.wires:
                    this_wire.add_series(nei_wire)

    def is_aligned(self, other: "Axis") -> bool:
        """Returns True if wires of the other axis are aligned
        to wires of this one"""
        # first identify common wires
        for this_wire in self.wires:
            for other_wire in other.wires:
                if this_wire.is_coincident(other_wire):
                    return this_wire.is_aligned(other_wire)

        raise RuntimeError("Axes are not neighbours")

    def grade(self) -> None:
        if self.is_defined:
            return

        if len(self.wires.undefined) < 4:
            # some wires have defined gradings; share those with others
            self.wires.propagate_gradings()
            return

        if len(self.chops) == 0:
            # nothing to work with
            return

        # create Grading from chops, if there are any
        grading = Grading(0)
        for chop in self.chops:
            grading.add_chop(chop)

        take = self.chops[0].take

        if take == "avg":
            # make a fake grading with an average length,
            # calculate count from it, then copy it with the same
            # count to all wires
            avg_length = sum([w.length for w in self.wires]) / 4
            grading.length = avg_length
            for wire in self.wires:
                wire.grading = grading.copy(wire.length, False)
        else:
            # take a specific wire
            wires_by_length = list(sorted(self.wires, key=lambda w: w.length))
            if self.chops[0].take == "max":
                # chop the longest wire, then propagate
                wire = wires_by_length[-1]
            else:  # "min"
                wire = wires_by_length[0]

            wire.grading = grading
            wire.update()

        # copy grading to all wires in this axis
        self.wires.propagate_gradings()

    @property
    def is_defined(self) -> bool:
        """Returns True if this axis's counts and gradings are defined"""
        return self.wires.is_defined

    def check_consistency(self) -> None:
        counts = set(wire.grading.count for wire in self.wires)
        if len(counts) != 1:
            raise InconsistentGradingsError(f"Axis Wires have different counts! {counts} {self}")

        for wire in self.wires:
            wire.check_consistency()

    @property
    def start_vertices(self) -> Set[Vertex]:
        return {wire.vertices[0] for wire in self.wires}

    @property
    def end_vertices(self) -> Set[Vertex]:
        return {wire.vertices[1] for wire in self.wires}

    @property
    def count(self) -> int:
        return self.wires.count

    @property
    def is_simple(self) -> bool:
        return self.wires.is_simple

    def __str__(self):
        return f"Axis {self.index} (" + "|".join(str(wire) for wire in self.wires.wires) + ")"