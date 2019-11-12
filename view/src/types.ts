
export type Partition = number[]

export type TileEdge = {
    adjacent_cell: number,
    vertices: [ number, number ]
}

export type TileMap = {
    tile_vertices: number[][][],
    tile_neighbours: number[][],
    tile_populations: number[][],
    tile_edges: TileEdge[][]
}

