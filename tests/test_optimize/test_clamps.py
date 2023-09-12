import unittest
from typing import List

import numpy as np

from classy_blocks.items.vertex import Vertex
from classy_blocks.modify.clamps.curve import LineClamp, ParametricCurveClamp, RadialClamp
from classy_blocks.modify.clamps.free import FreeClamp
from classy_blocks.modify.clamps.surface import ParametricSurfaceClamp, PlaneClamp
from classy_blocks.types import NPPointType
from classy_blocks.util import functions as f


class ClampTestsBase(unittest.TestCase):
    def setUp(self):
        self.vertex = Vertex([0, 0, 0], 0)


class FreeClampTests(ClampTestsBase):
    def setUp(self):
        super().setUp()

    def test_free_init(self):
        """Initialization of FreeClamp"""
        clamp = FreeClamp(self.vertex)

        np.testing.assert_array_equal(clamp.params, self.vertex.position)

    def test_free_update(self):
        """Update params of a free clamp"""
        clamp = FreeClamp(self.vertex)
        clamp.update_params([1, 0, 0])

        np.testing.assert_array_equal(self.vertex.position, [1, 0, 0])


class CurveClampTests(ClampTestsBase):
    def setUp(self):
        super().setUp()

        def function(params: List[float]) -> NPPointType:
            t = params[0]
            return f.vector(np.sin(t), np.cos(t), t)

        self.function = function

    def test_line_init(self):
        """Initialization of LineClamp"""
        clamp = LineClamp(self.vertex, [0, 0, 0], [1, 1, 1])

        self.assertAlmostEqual(clamp.params[0], 0)

    def test_line_init_noncoincident(self):
        """Initialization of LineClamp with a non-coincident vertex;
        update vertex with closest point"""
        clamp = LineClamp(self.vertex, [1, 1, 1], [2, 1, 1])

        # don't be too strict about initial parameters,
        # optimization will move everything away anyhow
        np.testing.assert_array_almost_equal(clamp.point, [0, 1, 1], decimal=3)

    def test_line_init_far(self):
        """Initialization that will yield t < 0"""
        clamp = LineClamp(self.vertex, [1, 1, 1], [2, 2, 2])

        self.assertAlmostEqual(clamp.params[0], -1)

    def test_line_value(self):
        clamp = LineClamp(self.vertex, [0, 0, 0], [1, 1, 1])

        clamp.update_params([0.5])

        np.testing.assert_array_almost_equal(clamp.point, [0.5, 0.5, 0.5])

    def test_line_bounds_lower(self):
        self.vertex.move_to([-1, -1, -1])
        clamp = LineClamp(self.vertex, [0, 0, 0], [1, 1, 1], [0, 1])

        self.assertAlmostEqual(clamp.params[0], 0)

    def test_line_bounds_upper(self):
        self.vertex.move_to([2, 2, 2])
        clamp = LineClamp(self.vertex, [0, 0, 0], [1, 1, 1], [0, 1])

        self.assertAlmostEqual(clamp.params[0], 1)

    def test_analytic_init(self):
        clamp = ParametricCurveClamp(self.vertex, self.function)

        self.assertAlmostEqual(clamp.params[0], 0, places=3)

    def test_analytic_init_noncoincident(self):
        self.vertex.move_to([0, 0, 1])
        clamp = ParametricCurveClamp(self.vertex, self.function)

        self.assertAlmostEqual(clamp.params[0], 1, places=3)

    def test_analytic_bounds_lower(self):
        self.vertex.move_to([-1, -1, -1])
        clamp = ParametricCurveClamp(self.vertex, self.function, [0, 1])

        self.assertAlmostEqual(clamp.params[0], 0, places=3)

    def test_analytic_bounds_upper(self):
        self.vertex.move_to([0, 0, 2])
        clamp = ParametricCurveClamp(self.vertex, self.function, [0, 1])

        self.assertAlmostEqual(clamp.params[0], 1, places=3)

    def test_radial_init(self):
        self.vertex.move_to([1, 0, 0])
        clamp = RadialClamp(self.vertex, [0, 0, -1], [0, 0, 1])

        np.testing.assert_array_almost_equal(clamp.point, [1, 0, 0])

    def test_radial_rotate(self):
        self.vertex.move_to([1, 0, 0])
        clamp = RadialClamp(self.vertex, [0, 0, -1], [0, 0, 1])

        clamp.update_params([np.pi / 2])

        np.testing.assert_array_almost_equal(clamp.point, [0, 1, 0])


class SurfaceClampTests(ClampTestsBase):
    def setUp(self):
        super().setUp()

        def function(params) -> NPPointType:
            """A simple extruded sinusoidal surface"""
            u = params[0]
            v = params[1]

            return f.vector(u, v, np.sin(u))

        self.function = function

    def test_plane_clamp(self):
        clamp = PlaneClamp(self.vertex, [0, 0, 0], [1, 1, 1])

        np.testing.assert_array_almost_equal(clamp.params, [0, 0])

    def test_plane_move_u(self):
        clamp = PlaneClamp(self.vertex, [0, 0, 0], [1, 0, 0])

        clamp.update_params([1, 0])

        self.assertAlmostEqual(self.vertex.position[0], 0)

    def test_plane_move_v(self):
        clamp = PlaneClamp(self.vertex, [0, 0, 0], [1, 0, 0])

        clamp.update_params([0, 1])

        self.assertAlmostEqual(self.vertex.position[0], 0)

    def test_plane_move_uv(self):
        clamp = PlaneClamp(self.vertex, [0, 0, 0], [1, 0, 0])

        clamp.update_params([1, 1])

        self.assertAlmostEqual(self.vertex.position[0], 0)

    def test_parametric_init(self):
        clamp = ParametricSurfaceClamp(self.vertex, self.function)

        np.testing.assert_array_almost_equal(clamp.params, [0, 0], decimal=3)

    def test_parametric_initial_unbounded(self):
        clamp = ParametricSurfaceClamp(self.vertex, self.function)

        np.testing.assert_array_almost_equal(clamp.initial_params, [0, 0])

    def test_parametric_initial_bounded(self):
        clamp = ParametricSurfaceClamp(self.vertex, self.function, [[0, 1], [0, 1]])

        np.testing.assert_array_almost_equal(clamp.initial_params, [0.5, 0.5])

    def test_parametric_move(self):
        clamp = ParametricSurfaceClamp(self.vertex, self.function)

        clamp.update_params([np.pi / 2, 1])

        np.testing.assert_array_almost_equal(clamp.point, [np.pi / 2, 1, 1])

    def test_parametric_bounds_upper(self):
        self.vertex.move_to([4, 4, 0])
        clamp = ParametricSurfaceClamp(self.vertex, self.function, [[0.0, np.pi], [0.0, np.pi]])

        np.testing.assert_array_almost_equal(clamp.params, [np.pi, np.pi])
