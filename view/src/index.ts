import * as randomColor from 'randomColor'
import { make_chart, update_chart } from './pareto_front_chart'
import { Partition, TileMap } from './types'
import { draw_partition } from './draw'

const canvas_pf = document.getElementById('pareto_front') as HTMLCanvasElement
const ctx_pf = canvas_pf.getContext('2d')
const canvas_partition = document.getElementById('partition') as HTMLCanvasElement
const ctx_partition = canvas_partition.getContext('2d')
const div_text = document.getElementById('partition_text')
const metrics_a = document.getElementById('metric_option_a')
const metrics_b = document.getElementById('metric_option_b')
let chart

function update_text(div: HTMLElement, data, p_idx: number, colors: string[]) {
    div.innerHTML = ''
    const district_voters = new Array(data.n_districts).fill(0).map(() => [0, 0])

    const partition = data.solutions[p_idx]

    partition.forEach((district_idx:number, tile_idx:number) => {
        district_voters[district_idx][0] += data.state.tile_populations[tile_idx][0]
        district_voters[district_idx][1] += data.state.tile_populations[tile_idx][1]
    })
    for (let i = 0; i < data.n_districts; i++) {
        const p = document.createElement('p')
        p.innerHTML = `${district_voters[i][0]} | ${district_voters[i][1]}`
        p.style.color = colors[i]
        div.appendChild(p)
    }
}

function update_pareto_plot(data) {
    const idx1 = +(metrics_a.querySelector('.selected') as HTMLElement).dataset.idx
    const idx2 = +(metrics_b.querySelector('.selected') as HTMLElement).dataset.idx
    update_chart(chart, data.values, data.metrics, idx1, idx2)
}

function draw_ui(data) {
    data.metrics.forEach((metric, idx) => {
        const option_a:HTMLButtonElement = document.createElement('button')
        option_a.innerHTML = metric
        option_a.dataset.idx = idx
        const option_b = option_a.cloneNode(true) as HTMLButtonElement

        metrics_a.append(option_a)
        metrics_b.append(option_b)
        option_a.onclick = () => {
            metrics_a.querySelector('.selected').classList.remove('selected')
            option_a.classList.add('selected')
            update_pareto_plot(data)
        }
        option_b.onclick = () => {
            metrics_b.querySelector('.selected').classList.remove('selected')
            option_b.classList.add('selected')
            update_pareto_plot(data)
        }
    })
    metrics_a.children[0].classList.add('selected')
    metrics_b.children[1].classList.add('selected')
}

fetch('data/rundata.json').
    then(r => r.json()).
    then(data => {
        const colors: string[] = Array(data.n_districts).fill(0).map(randomColor)
        // const m: TileMap = data.map
        // console.log(data)
        const chart_config = {
            onHover: p_i => {
                draw_partition(ctx_partition, data.state, data.solutions[p_i], colors, 400)
                update_text(div_text, data, p_i, colors)
            }
        }
        chart = make_chart(chart_config, ctx_pf, data.values, 1, 0, data.metrics )
        draw_ui(data)
        draw_partition(ctx_partition, data.state, data.solutions[0], colors, 400)
        update_text(div_text, data, 0, colors)
        // update_pareto_plot(data, colors)

    })