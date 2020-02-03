
export type District = number[]

export type Edge = [ number, number ]

export type TileEdge = {
    length: number,
    edges: Edge[][]
}

export type State = {
    shapes: [number, number][][][],
    neighbors: number[][],
    populations: number[],
    boundaries: number[],
    voters: number[][],
    population: number,
    bbox: number[]
    tile_edges: TileEdge[]
}
