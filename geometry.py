"""Procedural meshes used by the cockpit and the space scene."""

from __future__ import annotations

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
)


def make_uv_sphere(
    name: str,
    radius: float = 1.0,
    rings: int = 24,
    sectors: int = 48,
    inside_out: bool = False,
) -> NodePath:
    """Z-up UV sphere. `inside_out` is for a sky dome you view from inside."""
    vertex_format = GeomVertexFormat.get_v3n3t2()
    vdata = GeomVertexData(name, vertex_format, Geom.UHStatic)
    vdata.set_num_rows((rings + 1) * (sectors + 1))

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    texcoord = GeomVertexWriter(vdata, "texcoord")

    for ring in range(rings + 1):
        v = ring / rings
        phi = math.pi * v
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        for sector in range(sectors + 1):
            u = sector / sectors
            theta = 2.0 * math.pi * u
            x = radius * sin_phi * math.cos(theta)
            y = radius * sin_phi * math.sin(theta)
            z = radius * cos_phi
            vertex.add_data3(x, y, z)
            sign = -1.0 if inside_out else 1.0
            normal.add_data3(sign * x / radius, sign * y / radius, sign * z / radius)
            texcoord.add_data2(u, 1.0 - v)

    prim = GeomTriangles(Geom.UHStatic)
    for ring in range(rings):
        for sector in range(sectors):
            a = ring * (sectors + 1) + sector
            b = a + 1
            c = a + (sectors + 1)
            d = c + 1
            if inside_out:
                prim.add_vertices(a, c, b)
                prim.add_vertices(b, c, d)
            else:
                prim.add_vertices(a, b, c)
                prim.add_vertices(b, d, c)

    geom = Geom(vdata)
    geom.add_primitive(prim)
    node = GeomNode(name)
    node.add_geom(geom)
    return NodePath(node)


def make_ring_disc(
    name: str,
    inner: float,
    outer: float,
    segments: int = 96,
) -> NodePath:
    """Horizontal annulus in the XZ plane, UV u=angle, v=radius."""
    vertex_format = GeomVertexFormat.get_v3n3t2()
    vdata = GeomVertexData(name, vertex_format, Geom.UHStatic)
    vdata.set_num_rows((segments + 1) * 2)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    texcoord = GeomVertexWriter(vdata, "texcoord")

    for i in range(segments + 1):
        u = i / segments
        angle = 2.0 * math.pi * u
        ca, sa = math.cos(angle), math.sin(angle)
        vertex.add_data3(inner * ca, 0, inner * sa)
        normal.add_data3(0, 1, 0)
        texcoord.add_data2(u, 0)
        vertex.add_data3(outer * ca, 0, outer * sa)
        normal.add_data3(0, 1, 0)
        texcoord.add_data2(u, 1)

    prim = GeomTriangles(Geom.UHStatic)
    for i in range(segments):
        a = i * 2
        b = a + 1
        c = a + 2
        d = a + 3
        prim.add_vertices(a, c, b)
        prim.add_vertices(b, c, d)
        # Underside so the rings read from below
        prim.add_vertices(a, b, c)
        prim.add_vertices(b, d, c)

    geom = Geom(vdata)
    geom.add_primitive(prim)
    node = GeomNode(name)
    node.add_geom(geom)
    return NodePath(node)
