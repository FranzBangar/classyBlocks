import os

import classy_blocks as cb
from classy_blocks.modify.clamps.free import FreeClamp
from classy_blocks.modify.optimizer import Optimizer

mesh = cb.Mesh()

size = 0.1

# Create a rapidly expanding diffuser that will cause high non-orthogonality
# at the beginning of the contraction; then, move inner vertices so that
# this problem is avoided

small_pipe = cb.Cylinder([0, 0, 0], [2, 0, 0], [0, 1, 0])
small_pipe.chop_axial(start_size=size)
small_pipe.chop_radial(start_size=size)
small_pipe.chop_tangential(start_size=size)
mesh.add(small_pipe)

diffuser = cb.Frustum.chain(small_pipe, 0.5, 2)
diffuser.chop_axial(start_size=size)
mesh.add(diffuser)

big_pipe = cb.Cylinder.chain(diffuser, 5)
big_pipe.chop_axial(start_size=size)
mesh.add(big_pipe)

mesh.set_default_patch("walls", "wall")

# Assemble the mesh before making changes
mesh.assemble()

# Find inside vertices (start and stop surfaces of cylinders and frustum);
# this is a bit clumsy at the moment, position and radius were
# defined experimentally; better tools will be developed in the future.
finder = cb.VertexFinder(mesh)
inner_vertices = finder.by_position([3.5, 0, 0], radius=1.75)

# Release those vertices so that optimization can find a better position for them
optimizer = Optimizer(mesh)

for vertex in inner_vertices:
    clamp = FreeClamp(vertex)
    optimizer.release_vertex(clamp)

optimizer.optimize()

mesh.write(os.path.join("..", "case", "system", "blockMeshDict"), debug_path="debug.vtk")
