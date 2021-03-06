#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Nathanaël Jourdane
# This file is part of Zazouck.
# Zazouck is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Zazouck is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with Zazouck. If not, see
# <http://www.gnu.org/licenses/>.

'Module to build a construction with rods and 3d printed corners'

from os import path as op
import xml.etree.ElementTree as ET
import math
import solid, utils

class Roddy:
    'Module to build a construction with rods and 3d printed corners'

    def __init__(self, xml_path, input_stl_path, infos_path):
        
        self.solid = solid.Solid(input_stl_path)
        self.solid.display(infos_path)

        self.xml_root = ET.Element("model")

        project_name = op.splitext(op.basename(input_stl_path))[0]
        self.xml_root.set('id', project_name)
        self.xml_root.set('unit', 'mm')
        self.xml_root.set('img', 'yes')
        self.xml_root.set('desc', 'Build a construction with rods and 3d printed corners.')

        self._build_corners_tree()
        self._build_edges_tree()

        tree = ET.ElementTree(self.xml_root)
        utils.indent(self.xml_root)
        tree.write(xml_path, encoding = "UTF-8", xml_declaration = True)

        # infos = str(self.solid.get_nb_corners()) + " corners," + str(self.solid.get_nb_polygons())
        # + " polygons," + str(self.solid.get_nb_edges()) + " edges\n"

    def _build_corners_tree(self):
        'Make the xml tree of all the corners of the model.'

        xml_corner = ET.SubElement(self.xml_root, "family")

        xml_corner.set('id', 'corner')
        xml_corner.set('file', "corner.scad")
        xml_corner.set('light_file', "corner_light.scad")
        xml_corner.set('type', 'stl')
        xml_corner.set('img', '0,0,0,45,0,45,140')
        xml_corner.set('desc',
            '3D printed parts representing the vertices of the model. They connect rods together.')

        # TODO: .corner = ugly!!!
        for corner in self.solid.corners:
            part = ET.SubElement(xml_corner, "part")
            part.set('id', str(corner.get_id()))
            part.set('pos', ','.join(str(p) for p in corner.get_position()))
            part.set('data', self._corner_data(corner))
            part.set('connections', ';'.join(str(x) for x in corner.get_connected_corners()))

    def _build_edges_tree(self):
        'Make the xml tree of all the edges of the model.'

        xml_edge = ET.SubElement(self.xml_root, "family")
        xml_edge.set('id', 'edge')
        xml_edge.set('file', "edge.scad")
        xml_edge.set('type', 'dxf')
        xml_edge.set('img', 'yes')
        xml_edge.set('desc', 'Rods representing the edges of the model. You can get it with a ' +
                'laser cutting or simply by cutting rods by hands.')

        for edge in self.solid.edges: # ugly!!!
            part = ET.SubElement(xml_edge, "part")
            part.set('id', str(edge.get_id()))

            part.set('pos', ','.join(str(p) for p in edge.get_position()))
            part.set('rot', ','.join(str(r) for r in edge.get_rotation()))
            part.set('data', 'length=' + str(edge.get_length()))
            part.set('connections', str(edge.get_corner_start().get_id()) + ';' +
                    str(edge.get_corner_end().get_id()))

    def _corner_data(self, corner):
        'Return angles of the corner in a data string.'

        angles = list()
        for target in corner.get_connected_corners():
            target_corner = self.solid.get_corner_by_id(target).get_position()
            angles += _positions_to_angles(corner.get_position(), target_corner)

        return "angles='" + ','.join(str(angle) for angle in angles) + "'"

    def __str__(self):
        'Return informations about the module.'

        string = str(self.solid.get_nb_corners()) + " corners, "
        string += str(self.solid.get_nb_polygons()) + " polygons, "
        string += str(self.solid.get_nb_edges()) + " edges."
        return string

def _positions_to_angles(init_position, target_position):
    'Calculate the angles between two positions.'

    #for i in range(3):
    init_x = target_position[0] - init_position[0]
    init_y = target_position[1] - init_position[1]
    init_z = target_position[2] - init_position[2]

    relative_pos = (init_x, init_y, init_z)
    
    #calcul angle_v
    hypot = math.hypot(relative_pos[0], relative_pos[1])
    if hypot == 0:
        angle_v = 0 if relative_pos[2] > 0 else 180
    else:
        angle_v = 90-math.degrees(math.atan(relative_pos[2] / hypot))

    # calcul angle_h
    if relative_pos[0] == 0:
        angle_h = 90 if relative_pos[1] >= 0 else -90
    elif relative_pos[1] == 0:
        angle_h = 0 if relative_pos[0] >= 0 else 180
    else:
        angle_h = math.degrees(math.atan(relative_pos[0] / relative_pos[1]))
        if relative_pos[0] < 0 and relative_pos[1] < 0:
            angle_h -= 180
    angle_h = angle_h+360 if angle_h < 0 else angle_h
    
    return int(round(angle_v)), int(round(angle_h))