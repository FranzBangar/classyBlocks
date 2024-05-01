from typing import List

import numpy as np

from classy_blocks.construct.flat.face import Face
from classy_blocks.construct.flat.sketches.sketch import Sketch
from classy_blocks.types import PointType
from classy_blocks.util.constants import DTYPE


class Grid(Sketch):
    """A `n x m` array of rectangles;
    not here because it's particularly useful but as an example of a cartesian sketch/stack.

    Lies in x-y plane and is aligned with cartesian coordinate system by default
    but can be rotated arbitrarily just like other entities.

    point_1 is 'lower left' and point_2 is upper right.

    TODO: make this more general and user-friendly"""

    def __init__(self, point_1: PointType, point_2: PointType, count_1: int, count_2: int):
        point_1 = np.asarray(point_1, dtype=DTYPE)
        point_2 = np.asarray(point_2, dtype=DTYPE)

        coords_1 = np.linspace(point_1[0], point_2[0], num=count_1)
        coords_2 = np.linspace(point_1[1], point_2[1], num=count_2)

        self.grid: List[Face] = []

        for iy in range(count_2 - 1):
            for ix in range(count_1 - 1):
                points = [
                    coords_1[ix],
                    coords_1[ix + 1],
                    coords_2[iy + 1],
                    coords_1[iy],
                ]

                self.grid.append(Face(points))

    @property
    def faces(self):
        return self.grid

    @property
    def center(self):
        return (self.faces[0].points[0].position + self.faces[-1].points[2].position) / 2
