def shoelace(vertices):
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(vertices)
    for i in range(n):
        j = (i + 1) % n
        area += (vertices[j][0] - vertices[i][0]) * \
                (vertices[j][1] + vertices[i][1])
    return area

def area(vertices):
    return abs(shoelace(vertices)) / 2


def centroid(point_list):
    x = [p[0] for p in point_list]
    y = [p[1] for p in point_list]
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)

    dx = maxx/2 + minx/2
    dy = maxy/2 + miny/2
    return (dx, dy)