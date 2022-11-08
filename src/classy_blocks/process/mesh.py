from typing import Optional

from classy_blocks.util import constants, tools
from classy_blocks.util import functions as g

from classy_blocks.process.lists.vertices import VertexList
from classy_blocks.process.lists.blocks import BlockList
from classy_blocks.process.lists.edges import EdgeList
from classy_blocks.process.lists.boundary import Boundary
from classy_blocks.process.lists.faces import FaceList
from classy_blocks.process.lists.geometry import GeometryList

class Mesh:
    """contains blocks, edges and all necessary methods for assembling blockMeshDict"""
    def __init__(self):
        self.vertices = VertexList()
        self.edges = EdgeList()
        self.blocks = BlockList()
        self.boundary = Boundary()
        self.faces = FaceList()
        self.geometry = GeometryList()

        self.settings = {
            # TODO: test output
            'prescale': None,
            'scale': 1,
            'transform': None,
            'mergeType': None, # use 'points' to fall back to the older point-based block merging 
            'checkFaceCorrespondence': None, # true by default, turn off if blockMesh fails (3-sided pyramids etc.)
            'verbose': None,
        }

        self.patches = {
            'default': None,
            'merged': [],
        }

    def add(self, item) -> None:
        """Add a classy_blocks entity to the mesh;
        can be a block, created from points (Block.create_from_points()),
        Operation, Shape or Object."""
        if hasattr(item, "block"):
            self.blocks.add(item.block)
        elif hasattr(item, "blocks"):
            for block in item.blocks:
                self.blocks.add(block)
        else:
            self.blocks.add(item)

        # TODO: TEST
        if hasattr(item, "geometry"):
            self.add_geometry(item.geometry)

    def merge_patches(self, master:str, slave:str) -> None:
        """Merges two non-conforming named patches using face merging;
        https://www.openfoam.com/documentation/user-guide/4-mesh-generation-and-conversion/4.3-mesh-generation-with-the-blockmesh-utility#x13-470004.3.2
        (breaks the 100% hex-mesh rule)"""
        self.patches['merged'].append([master, slave])

    def set_default_patch(self, name:str, ptype:str) -> None:
        """Adds the 'defaultPatch' entry to the mesh; any non-specified block boundaries
        will be assigned this patch"""
        assert ptype in ("patch", "wall", "empty", "wedge")

        self.patches['default'] = {"name": name, "type": ptype}

    def add_geometry(self, geometry:dict) -> None:
        """Adds named entry in the 'geometry' section of blockMeshDict;
        'g' is in the form of dictionary {'geometry_name': [list of properties]};
        properties are as specified by searchable* class in documentation.
        See examples/advanced/project for an example."""
        self.geometry.add(geometry)

    def write(self, output_path:str, debug_path:Optional[str]=None) -> None:
        """Writes a blockMeshDict to specified location. If debug_path is specified,
        a VTK file is created first where each block is a single cell, to see simplified
        blocking in case blockMesh fails with an unfriendly error message."""
        self.vertices.collect(self.blocks, self.patches['merged'])

        if debug_path is not None:
            self.to_vtk(debug_path)

        self.edges.collect(self.blocks)
        self.blocks.assemble()

        self.boundary.collect(self.blocks)

        # TODO: move all this writing to a better place
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(constants.MESH_HEADER)

            for key, value in self.settings.items():
                if value is not None:
                    f.write(f"{key} {value};\n")
            f.write('\n')
            
            f.write(self.geometry.output())

            f.write(self.vertices.output())
            f.write(self.blocks.output())
            f.write(self.edges.output())
            f.write(self.boundary.output())
            f.write(self.faces.output(self.blocks))

            # patches: output manually
            if len(self.patches['merged']) > 0:
                f.write("mergePatchPairs\n(\n")
                for pair in self.patches['merged']:
                    f.write(f"\t({pair[0]} {pair[1]})\n")
                
                f.write(");\n\n")

            if self.patches['default'] is not None:
                f.write("defaultPatch\n{\n")
                f.write(f"\tname {self.patches['default']['name']};\n")
                f.write(f"\ttype {self.patches['default']['type']};")
                f.write("\n}\n\n");


    def to_vtk(self, output_path):
        """Creates a VTK file with each mesh.block represented as a hexahedron,
        useful for debugging when Mesh.write() succeeds but blockMesh fails.
        Can only be called after Mesh.write() has been successfully finished!"""
        context = {
            "points": [v.point for v in self.vertices],
            "cells": [[v.mesh_index for v in b.vertices] for b in self.blocks],
        }

        tools.template_to_dict("vtk.template", output_path, context)