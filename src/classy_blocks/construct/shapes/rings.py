from typing import List

import numpy as np

from classy_blocks.types import PointType, OrientType
from classy_blocks.construct.flat.face import Face
from classy_blocks.construct.flat.annulus import Annulus
from classy_blocks.construct.operations.operation import Operation
from classy_blocks.construct.shapes.round import RoundShape
from classy_blocks.construct.operations.revolve import Revolve

from classy_blocks.util import functions as f

class ExtrudedRing(RoundShape):
    """A ring, created by specifying its base, then extruding it"""
    sketch_class = Annulus
    inner_patch:OrientType = 'left'

    def transform_function(self, **kwargs):
        return self.sketch_1.copy().translate(kwargs['displacement'])

    def __init__(
        self, axis_point_1:PointType, axis_point_2:PointType,
        outer_radius_point_1:PointType, inner_radius:float, n_segments:int=8):

        self.axis = np.asarray(axis_point_2) - np.asarray(axis_point_1)

        super().__init__(
            [axis_point_1, outer_radius_point_1, self.axis, inner_radius, n_segments],
            {"displacement": self.axis}
        )

    def chop_tangential(self, **kwargs) -> None:
        """Circumferential chop"""
        # Ring has no 'core' so tangential chops must be defined explicitly
        for operation in self.shell:
            operation.chop(self.tangential_axis, **kwargs)

    def set_inner_patch(self, name:str) -> None:
        """Assign the faces of inside surface to a named patch"""
        for operation in self.shell:
            operation.set_patch(self.inner_patch, name)

    @classmethod
    def chain(cls, source:RoundShape, length:float) -> 'ExtrudedRing':
        """Creates a new cylinder on start or end face of a round source Shape;
        Use length > 0 to go 'forward' from source's end face or
        length < 0 to go 'backward' from source's start face"""
        # TODO: TEST
        assert isinstance(source, ExtrudedRing)

        if length > 0:
            sketch = source.sketch_2
        else:
            sketch = source.sketch_1

        return cls(
            sketch.center,
            sketch.center + f.unit_vector(sketch.normal) * length,
            sketch.outer_radius_point,
            sketch.inner_radius,
            n_segments=sketch.n_segments,
        )

    @classmethod
    def expand(cls, source, thickness: float) -> 'ExtrudedRing':
        """Create a new concentric Ring with radius, enlarged by 'thickness';
        Can be used on Cylinder or ExtrudedRing"""
        # TODO: TEST
        s1 = source.sketch_1
        s2 = source.sketch_2

        new_radius_point = s1.center_point + f.unit_vector(s1.radius_point - s1.center_point) * (s1.radius + thickness)

        return cls(s1.center_point, s2.center_point, new_radius_point, s1.radius, n_segments=s1.n_segments)

    @classmethod
    def contract(cls, source, inner_radius: float):
        # TODO: TEST
        assert source.__class__ == cls

        s1 = source.sketch_1
        s2 = source.sketch_2
        assert inner_radius < s1.inner_radius

        return cls(s1.center_point, s2.center_point, s1.inner_radius_point, inner_radius)

class RevolvedRing(ExtrudedRing):
    """A ring specified by its cross-section; can be of arbitrary shape.
    Face points must be specified in the following order:
            p3---___
           /        ---p2
          /              \\
         p0---------------p1

    0---- -- ----- -- ----- -- ----- -- --->> axis

    In this case, chop_*() will work as intended, otherwise
    the axes will be swapped or blocks will be inverted.

    Because of RevolvedRing's arbitrary shape, there is no
    'start' or 'end' sketch and .expand()/.contract() methods
    are not available.

    This shape is useful when building more complex shapes
    of revolution (with non-orthogonal blocks)
    from known 2d-blocking in cross-section."""
    axial_axis = 0
    radial_axis = 1
    tangential_axis = 2

    start_patch:OrientType = 'left'
    end_patch:OrientType = 'right'
    inner_patch:OrientType = 'front'
    outer_patch:OrientType = 'back'

    def transform_function(self, **kwargs):
        # No transforms for this one
        pass

    def __init__(self,
                 axis_point_1:PointType,
                 axis_point_2:PointType,
                 cross_section:Face, n_segments:int=8):

        self.axis_point_1 = np.asarray(axis_point_1)
        self.axis_point_2 = np.asarray(axis_point_2)
        self.axis = self.axis_point_2 - self.axis_point_1
        self.center_point = self.axis_point_1

        angle = 2 * np.pi / n_segments

        revolve = Revolve(cross_section, angle, self.axis, self.axis_point_1)

        self.revolves = [revolve.copy().rotate(i*angle, self.axis, self.center_point)
            for i in range(n_segments)
        ]

    def set_inner_patch(self, name:str) -> None:
        """Assign the faces of inside surface to a named patch"""
        for operation in self.shell:
            operation.set_patch(self.inner_patch, name)

    # methods/properties that differ from a lofted-sketch type of shape
    @property
    def operations(self) -> List[Operation]:
        return self.revolves

    @property
    def shell(self) -> List[Operation]:
        return self.operations

    @property
    def core(self) -> List[Operation]:
        return []
