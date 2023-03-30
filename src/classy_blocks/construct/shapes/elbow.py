import numpy as np

from classy_blocks.types import PointType, VectorType

from classy_blocks.construct.flat.disk import Disk
from classy_blocks.construct.shapes.round import RoundShape

from classy_blocks.util import functions as f


class Elbow(RoundShape):
    """A curved round shape of varying cross-section"""

    sketch_class = Disk

    def transform_function(self, **kwargs):
        # FIXME: invent a better method than juggling with **kwargs
        new_sketch = self.sketch_1.copy()
        new_sketch.rotate(kwargs["angle"], kwargs["axis"], kwargs["origin"])
        new_sketch.scale(kwargs["radius"] / self.sketch_1.radius)

        return new_sketch

    def __init__(
        self,
        center_point_1: PointType,
        radius_point_1: PointType,
        normal_1: VectorType,
        sweep_angle: float,
        arc_center: PointType,
        rotation_axis: VectorType,
        radius_2: float,
    ):
        radius_1 = f.norm(np.asarray(radius_point_1) - np.asarray(center_point_1))

        super().__init__(
            [center_point_1, radius_point_1, normal_1],  # arguments for this cross-section
            {  # transformation parameters for sketch_2
                # parameters for .rotate
                "axis": rotation_axis,
                "angle": sweep_angle,
                "origin": arc_center,
                # parameters for .scale
                "radius": radius_2,
            },
            {  # transform parameters for mid sketch
                "axis": rotation_axis,
                "angle": sweep_angle / 2,
                "origin": arc_center,
                "radius": (radius_1 + radius_2) / 2,
            },
        )

    @classmethod
    def chain(
        cls,
        source: RoundShape,
        sweep_angle: float,
        arc_center: PointType,
        rotation_axis: VectorType,
        radius_2: float,
        start_face: bool = False,
    ) -> "Elbow":
        """Use another round Shape's end face as a starting point for this Elbow;
        Returns a new Elbow object. To start from the other side, use start_face = True"""
        assert source.sketch_class == Disk

        if start_face:
            s = source.sketch_1
        else:
            s = source.sketch_2

        return cls(s.center, s.radius_point, s.normal, sweep_angle, arc_center, rotation_axis, radius_2)
