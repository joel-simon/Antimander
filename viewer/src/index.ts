import * as randomColor from 'randomColor'

const canvas = document.getElementById('c') as HTMLCanvasElement
const ctx = canvas.getContext('2d')

const getJson = (p) => fetch(p).then(r => r.json())

type TileMap = {
    tile_vertices: number[][][],
    tile_populations: number[][]
}
type Partition = number[]

function polygon(ctx, points: number[][], scale:number=1) {
    ctx.beginPath()
    ctx.moveTo(scale*points[0][0], scale*points[0][1])
    for (var i = 1; i < points.length; i++) {
        ctx.lineTo(scale*points[i][0], scale*points[i][1])
    }
    ctx.lineTo(scale*points[0][0], scale*points[0][1])
    ctx.closePath()
}

function draw_partition(map:TileMap, partition: Partition, colors: string[], scale:number=1) {
    partition.forEach((district_idx:number, tile_idx:number) => {
        ctx.fillStyle = colors[district_idx]
        polygon(ctx, map.tile_vertices[tile_idx], scale)
        ctx.fill()
        ctx.stroke()
    })
}

getJson('data/rundata.json').then(data => {
    let idx = 0
    console.log(data)
    const colors: string[] = Array(5).fill(0).map(randomColor)
    setInterval(() => {
        draw_partition(data.map, data.solutions[idx], colors, 400)
        idx = (idx + 1) % data.solutions.length
    }, 2000)
})