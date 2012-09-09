# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

"""
This script imports Raw Triangle File format files.

Adapted from Blender's RAW importer

The raw triangle format is very simple; it has no verts or faces lists.
It's just a simple ascii text file with the vertices of each triangle
listed on each line. In addition, a line with 12 values will be
imported as a quad.

Notes:
Generates the standard verts and faces lists, but without duplicate
verts. Only *exact* duplicates are removed, there is no way to specify a
tolerance.
"""

def readMeshRAW(filename):
    filehandle = open(filename, "rb")

    def line_to_face(line):
        # Each triplet is an xyz float
        line_split = line.split()
        try:
            line_split_float = map(float, line_split)
        except:
            return None

        if len(line_split) in (9, 12):
            return zip(*[iter(line_split_float)] * 3)  # group in 3's
        else:
            return None

    faces = []
    for line in filehandle.readlines():
        face = line_to_face(line)
        if face:
            faces.append(face)

    filehandle.close()

    # Generate verts and faces lists, without duplicates
    verts = []
    coords = {}
    index_tot = 0
    faces_indices = []

    for f in faces:
        fi = []
        for i, v in enumerate(f):
            index = coords.get(v)

            if index is None:
                index = coords[v] = index_tot
                index_tot += 1
                verts.append(v)

            fi.append(index)

        faces_indices.append(fi)

    return verts, faces_indices


