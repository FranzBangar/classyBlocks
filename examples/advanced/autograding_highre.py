import os

import classy_blocks as cb
from classy_blocks.grading.autograding.grader import HighReGrader

mesh = cb.Mesh()

base = cb.Grid([0, 0, 0], [3, 2, 0], 3, 2)

shape = cb.ExtrudedShape(base, 1)
mesh.add(shape)
mesh.assemble()
finder = cb.GeometricFinder(mesh)

move_points = [[0, 1, 1], [2, 1, 1], [3, 1, 1]]

for point in move_points:
    vertex = list(finder.find_in_sphere(point))[0]
    vertex.translate([0, 0.8, 0])

mesh.set_default_patch("walls", "wall")

# TODO: Hack! mesh.assemble() won't work here but wires et. al. must be updated
mesh.block_list.update()

grader = HighReGrader(mesh, 0.05)
grader.grade()

mesh.write(os.path.join("..", "case", "system", "blockMeshDict"), debug_path="debug.vtk")
