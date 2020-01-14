cpdef bint contains_point(float[:, :] poly, float x, float y) except *:
    # http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
    assert poly.shape[1] == 2
    cdef bint inside = False
    cdef int i, j
    cdef float xi, yi, xj, yj
    for i in range(poly.shape[0]):
        j = i-1 if i > 0 else poly.shape[0] - 1
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersect = ((yi >= y) != (yj >= y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = -1
    return inside

cdef float shoelace(float[:, :] poly) except *:
    """ The shoelace algorithm for polgon area """
    cdef float area = 0.0
    cdef int i, j
    cdef int n = poly.shape[0]
    for i in range(n):
        j = (i + 1) % n
        area += (poly[j, 0] - poly[i, 0]) * \
                (poly[j, 1] + poly[i, 1])
    return area

cpdef float area(float[:, :] poly) except *:
    return abs(shoelace(poly)) / 2.0