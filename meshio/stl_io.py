# -*- coding: utf-8 -*-
#
'''
I/O for the STL format, cf.
<https://en.wikipedia.org/wiki/STL_(file_format)>.

.. moduleauthor:: Nico Schlömer <nico.schloemer@gmail.com>
'''
import numpy


def read(filename):
    '''Reads a Gmsh msh file.
    '''
    with open(filename, 'rb') as f:
        out = read_buffer(f)
    return out


def read_buffer(f):
    line = f.readline().decode('utf-8')
    assert line[:5] == 'solid'

    facets = []
    while True:
        line = f.readline().decode('utf-8')

        if line[:8] == 'endsolid':
            break

        line = line.strip()
        assert line[:5] == 'facet'
        facets.append(_read_facet(f))
        line = f.readline().decode('utf-8')
        assert line.strip() == 'endfacet'

    # Now, all facets contain the point coordinate. Try to identify individual
    # points and build the data arrays.
    # TODO equip `unique()` with a tolerance
    points, idx = \
        numpy.unique(numpy.concatenate(facets), axis=0, return_inverse=True)
    cells = {'triangle': idx.reshape(-1, 3)}

    return points, cells, {}, {}, {}


def _read_facet(f):
    line = f.readline().decode('utf-8')
    assert line.strip() == 'outer loop'

    facet = numpy.empty((3, 3))

    flt = numpy.vectorize(float)
    for k in range(3):
        parts = f.readline().decode('utf-8').split()
        assert len(parts) == 4
        assert parts[0] == 'vertex'
        facet[k] = flt(parts[1:])

    line = f.readline().decode('utf-8')
    assert line.strip() == 'endloop'
    return facet


def write(
        filename,
        points,
        cells,
        point_data=None,
        cell_data=None,
        field_data=None,
        write_binary=False,
        ):
    assert not point_data, \
        'STL cannot write point data.'
    assert not field_data, \
        'STL cannot write field data.'
    assert len(cells.keys()) == 1 and list(cells.keys())[0] == 'triangle', \
        'STL can only write triangle cells.'

    pts = points[cells['triangle']]
    # compute normals
    normals = numpy.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
    nrm = numpy.sqrt(numpy.einsum('ij,ij->i', normals, normals))
    normals = (normals.T / nrm).T

    with open(filename, 'wb') as fh:
        fh.write('solid\n'.encode('utf-8'))

        for local_pts, normal in zip(pts, normals):
            # facet normal 0.455194 -0.187301 -0.870469
            #  outer loop
            #   vertex 266.36 234.594 14.6145
            #   vertex 268.582 234.968 15.6956
            #   vertex 267.689 232.646 15.7283
            #  endloop
            # endfacet
            fh.write('facet normal {} {} {}\n'.format(*normal).encode('utf-8'))
            fh.write(' outer loop\n'.encode('utf-8'))
            for pt in local_pts:
                fh.write('  vertex {} {} {}\n'.format(*pt).encode('utf-8'))
            fh.write(' endloop\n'.encode('utf-8'))
            fh.write('endfacet\n'.encode('utf-8'))

        fh.write('endsolid\n'.encode('utf-8'))

    return
