
export type Partition = number[]

export type TileEdge = {
    adjacent_cell: number,
    vertices: [ number, number ]
}

export type TileMap = {
    vertices: number[][][],
    neighbours: number[][],
    populations: number[],
    boundaries: number[],
    voters: number[][],
    population: number,
    bbox: number[]
    // tile_edges: TileEdge[][]
}
