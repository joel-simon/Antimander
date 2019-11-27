
export type Partition = number[]

export type TileEdge = {
    adjacent_cell: number,
    vertices: [ number, number ]
}

export type TileMap = {
    tract_vertices: number[][][],
    tract_neighbours: number[][],
    tract_populations: number[][],
    // tract_edges: TileEdge[][]
}

