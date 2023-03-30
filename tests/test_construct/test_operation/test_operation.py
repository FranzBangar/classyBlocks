import unittest

import numpy as np

from classy_blocks.construct.edges import Arc, Project
from classy_blocks.construct.flat.face import Face
from classy_blocks.construct.operations.loft import Loft
from classy_blocks.util import functions as f
from tests.fixtures.block import BlockTestCase


class OperationTests(BlockTestCase):
    """Stuff on Operation"""

    def setUp(self):
        self.loft = self.make_loft(0)

    def test_add_side_edge_assert(self):
        """Fail if the user supplies an inappropriate corner to add_side_edge()"""
        with self.assertRaises(AssertionError):
            self.loft.add_side_edge(5, Arc([0, 0.5, 0]))

    def test_set_patch_single(self):
        """Set patch of a single side"""
        self.loft.set_patch("left", "terrain")

        self.assertEqual(len(self.loft.patch_names), 1)

    def test_set_patch_multiple(self):
        """Set patch of multiple sides"""
        self.loft.set_patch(["left", "bottom", "top"], "terrain")

        self.assertEqual(len(self.loft.patch_names), 3)

    def test_project_side(self):
        """Project side without edges"""
        self.loft.project_side("bottom", "terrain", edges=False)
        self.assertEqual(len(self.loft.projections.sides), 1)
        self.assertEqual(len(self.loft.projections.edges), 0)

    def test_project_side_edges(self):
        """Project side with edges"""
        self.loft.project_side("bottom", "terrain", edges=True)
        self.assertEqual(len(self.loft.projections.sides), 1)
        self.assertEqual(len(self.loft.projections.edges), 4)

    def test_edges(self):
        """An ad-hoc Frame object with edges"""
        self.loft.project_side("bottom", "terrain", edges=True)
        self.loft.add_side_edge(0, Arc([0.1, 0.1, 0.5]))

        edges = self.loft.edges

        self.assertIsInstance(edges[0][4], Arc)
        self.assertIsInstance(edges[0][1], Project)
        self.assertIsInstance(edges[1][2], Project)
        self.assertIsInstance(edges[2][3], Project)
        self.assertIsInstance(edges[3][0], Project)

    def test_faces(self):
        """A dict of fresh faces"""
        self.assertEqual(len(self.loft.faces), 6)

        for _, face in self.loft.faces.items():
            self.assertIsInstance(face, Face)

    def test_patch_from_corner_empty(self):
        """No patches defined at any corner"""

    def test_patch_from_corner_single(self):
        """A single Patch at a specified corner"""
        self.loft.set_patch("bottom", "terrain")

        for i in (0, 1, 2, 3):
            self.assertSetEqual(self.loft.get_patches_at_corner(i), {"terrain"})

    def test_patch_from_corner_multiple(self):
        """Multiple patches from faces on this corner"""
        self.loft.set_patch("bottom", "terrain")
        self.loft.set_patch("front", "wall")
        self.loft.set_patch("left", "atmosphere")

        self.assertSetEqual(self.loft.get_patches_at_corner(0), {"terrain", "wall", "atmosphere"})
        self.assertSetEqual(self.loft.get_patches_at_corner(1), {"terrain", "wall"})


class OperationTransformTests(unittest.TestCase):
    """Loft inherits directly from Operation with no additional
    whatchamacallit; Loft tests therefore validate Operation"""

    def setUp(self):
        bottom_points = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
        bottom_edges = [Arc([0.5, -0.25, 0]), None, None, None]

        bottom_face = Face(bottom_points, bottom_edges)
        top_face = bottom_face.copy().translate([0, 0, 1]).rotate(np.pi / 4, [0, 0, 1])

        # create a mid face to take points from
        mid_face = bottom_face.copy().translate([0, 0, 0.5]).rotate(np.pi / 3, [0, 0, 1])

        self.loft = Loft(bottom_face, top_face)

        for i, point in enumerate(mid_face.points):
            self.loft.add_side_edge(i, Arc(point))

    def test_construct(self):
        """Create a Loft object"""
        _ = self.loft

    def test_translate(self):
        translate_vector = np.array([0, 0, 1])

        original_op = self.loft
        translated_op = self.loft.copy().translate(translate_vector)

        np.testing.assert_almost_equal(
            original_op.bottom_face.points + translate_vector, translated_op.bottom_face.points
        )

        np.testing.assert_almost_equal(
            original_op.side_edges[0].point + translate_vector, translated_op.side_edges[0].point
        )

    def test_rotate(self):
        axis = [0.0, 1.0, 0.0]
        origin = [0.0, 0.0, 0.0]
        angle = np.pi / 2

        original_op = self.loft
        rotated_op = self.loft.copy().rotate(angle, axis, origin)

        def extrude_direction(op):
            return op.top_face.center - op.bottom_face.center

        np.testing.assert_almost_equal(
            f.angle_between(extrude_direction(original_op), extrude_direction(rotated_op)), angle
        )
