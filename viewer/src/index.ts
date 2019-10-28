import * as randomColor from 'randomColor'
import { make_chart } from './pareto_front_chart'
import { Partition, TileMap } from './types'
import { draw_partition } from './draw'

const canvas_pf = document.getElementById('pareto_front') as HTMLCanvasElement
const ctx_pf = canvas_pf.getContext('2d')
const canvas_partition = document.getElementById('partition') as HTMLCanvasElement
const ctx_partition = canvas_partition.getContext('2d')

const div_text = document.getElementById('partition_text')

function update_text(div: HTMLElement, data, p_idx: number, colors: string[]) {
    // const {map:TileMap = data.map, p: Partition
    div.innerHTML = ''
    const district_voters = new Array(data.n_districts).fill(0).map(() => [0, 0])

    const partition = data.solutions[p_idx]

    partition.forEach((district_idx:number, tile_idx:number) => {
        district_voters[district_idx][0] += data.map.tile_populations[tile_idx][0]
        district_voters[district_idx][1] += data.map.tile_populations[tile_idx][1]
    })
    for (let i = 0; i < data.n_districts; i++) {
        const p = document.createElement('p')
        p.innerHTML = `${district_voters[i][0]} | ${district_voters[i][1]}`
        p.style.color = colors[i]
        div.appendChild(p)
    }
}

fetch('data/rundata.json').
    then(r => r.json()).
    then(data => {
        const colors: string[] = Array(data.n_districts).fill(0).map(randomColor)

        // const m: TileMap = data.map
        // console.log(data)

        draw_partition(ctx_partition, data.map, data.solutions[0], colors, 400)
        update_text(div_text, data, 0, colors)

        make_chart(
            {
                onHover: p_i => {
                    draw_partition(ctx_partition, data.map, data.solutions[p_i], colors, 400)
                    update_text(div_text, data, p_i, colors)
                }
            },
            ctx_pf,
            data.values,
            0, 1,
            [ 'Compactness', 'Efficiency Gap' ]
        )
    })