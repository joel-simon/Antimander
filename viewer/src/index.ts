import * as randomColor from 'randomColor'
import { make_chart } from './pareto_front_chart'

const canvas_pf = document.getElementById('pareto_front') as HTMLCanvasElement
const ctx_pf = canvas_pf.getContext('2d')

const canvas_partition = document.getElementById('partition') as HTMLCanvasElement
const ctx_partition = canvas_partition.getContext('2d')

type Partition = number[]
type TileMap = { tile_vertices: number[][][], tile_populations: number[][] }

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
        ctx_partition.fillStyle = colors[district_idx]
        polygon(ctx_partition, map.tile_vertices[tile_idx], scale)
        ctx_partition.fill()
        ctx_partition.stroke()
    })
}

fetch('data/rundata.json').
then(r => r.json()).
then(data => {
    // const colors: string[] = Array(data.n_districts).fill(0).map(randomColor)
    const colors = ['#CE1483', '#E0A890', '#70B77E', '#129490', '#065143']

    console.log(data)
    draw_partition(data.map, data.solutions[0], colors, 400)
    make_chart({
        onHover: idx => draw_partition(data.map, data.solutions[idx], colors, 400)
    }, ctx_pf, data.values, 0, 1, ['Concavity', 'Equality'])
})