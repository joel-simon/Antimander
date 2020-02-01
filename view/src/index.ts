import * as randomColor from 'randomColor'
import { make_chart, update_chart } from './pareto_front_chart'
import { District, State } from './types'
import { draw_district } from './draw'
import { generateTable, makeSlider } from './make_dom'
import { fetch_json, sum } from './utils'
declare var d3: any;

const canvas_pf = document.getElementById('pareto_front') as HTMLCanvasElement
const ctx_pf = canvas_pf.getContext('2d')
const canvas_partition = document.getElementById('partition') as HTMLCanvasElement
const ctx_partition = canvas_partition.getContext('2d')
const div_text = document.getElementById('partition_text')
const metrics_a = document.getElementById('metric_option_a')
const metrics_b = document.getElementById('metric_option_b')
const sliders_container = document.getElementById('sliders_container')
const partition_draw_mode = <HTMLInputElement>document.getElementById('partition_draw_mode')
let chart

canvas_partition.width  = window.innerWidth;
canvas_partition.height = window.innerWidth * 0.4;


function update_text(div: HTMLElement, data, p_idx: number, colors: string[]) {
    const { state, solutions, values, metrics_data } = data
    const { n_districts, metrics } = data.config
    const ideal_pop = state.population / n_districts
    const party_1 = new Array(n_districts).fill(0)
    const party_2 = new Array(n_districts).fill(0)
    const district_populations = new Array(n_districts).fill(0)
    const partition = solutions[p_idx]
    partition.forEach((di:number, tile_idx:number) => {
        party_1[di] += state.voters[tile_idx][0]
        party_2[di] += state.voters[tile_idx][1]
        district_populations[di] += state.populations[tile_idx]
    })
    const table = document.getElementById('info_table')
    table.innerHTML = ''
    const table_data = Array(n_districts).fill(0).map((_, idx ) => {
        const win_margin = Math.abs(party_1[idx] - party_2[idx]) / (party_1[idx] + party_2[idx])
        return {
            'p1': party_1[idx],
            'p2': party_2[idx],
            'lost_p1': metrics_data.lost_votes[p_idx][idx][0],
            'lost_p2': metrics_data.lost_votes[p_idx][idx][1],
            'lost_votes': Math.abs(metrics_data.lost_votes[p_idx][idx][0] - metrics_data.lost_votes[p_idx][idx][1]),
            'win_margin': (100*win_margin).toFixed(2)+'%',
            'equality': (100*Math.abs(district_populations[idx] - ideal_pop)/ideal_pop).toFixed(2)+'%',
            'pop': district_populations[idx],
        }
    })
    const total_lost_p1 = sum(metrics_data.lost_votes[p_idx].map(a => a[0]))
    const total_lost_p2 = sum(metrics_data.lost_votes[p_idx].map(a => a[1]))
    generateTable(table, table_data)
    table.querySelectorAll('tbody tr').forEach((row:HTMLElement, idx) => {
        row.style.color = colors[idx]
    })
    const total = sum(party_1) + sum(party_2)
    const p = document.getElementById('lost_votes_summary')
    p.innerHTML = `Lost votes party 1: ${total_lost_p1} <br> Lost votes party 2: ${total_lost_p2}`
}

function update_pareto_plot(data, ranges) {
    const { values } = data
    const { n_districts, metrics } = data.config
    const idx1 = 0
    const idx2 = 1
    // const idx1 = +(metrics_a.querySelector('.selected') as HTMLElement).dataset.idx
    // const idx2 = +(metrics_b.querySelector('.selected') as HTMLElement).dataset.idx
    // const filters = [ ]
    // for (const slider of sliders_container.children) {
    //     const name = (slider as HTMLElement).dataset.name
    //     const value = parseFloat(slider.querySelector('input').value) / 100
    //     filters.push(value)
    // }
    update_chart(chart, values, metrics, idx1, idx2, ranges)
}

// function draw_ui(data) {
//     const { state, solutions, values } = data
//     const { n_districts, metrics } = data.config
//     metrics.forEach((metric:string, idx) => {
//         const option_a:HTMLButtonElement = document.createElement('button')
//         option_a.innerHTML = metric
//         option_a.dataset.idx = idx
//         const option_b = option_a.cloneNode(true) as HTMLButtonElement
//         metrics_a.append(option_a)
//         metrics_b.append(option_b)
//         option_a.onclick = () => {
//             metrics_a.querySelector('.selected').classList.remove('selected')
//             option_a.classList.add('selected')
//             update_pareto_plot(data)
//         }
//         option_b.onclick = () => {
//             metrics_b.querySelector('.selected').classList.remove('selected')
//             option_b.classList.add('selected')
//             update_pareto_plot(data)
//         }
//         const slider:HTMLElement = makeSlider(metric)
//         sliders_container.append(slider)
//         slider.querySelector('input').oninput = () => {
//             update_pareto_plot(data)
//         }
//     })
//     metrics_a.children[0].classList.add('selected')
//     metrics_b.children[1].classList.add('selected')
// }

function create_parcoords(data, on_change) {
    const parcoords = d3.parcoords({
        dimensionTitles: data.config.metrics
    })("#parcoords").alpha(0.2)
    parcoords
        .data(data.values)
        // .hideAxis(["name"])
        .composite("darker")
        .render()
        .shadows()
        .reorderable()
        .brushMode("1D-axes")  // enable brushing
       // parcoords.smoothness(0.3)

    parcoords.on("brush", (values) => {
        // Convert values to ranges.
        let n = values[0].length
        let ranges = Array(n).fill(0).map(() => [Infinity, -Infinity])
        values.forEach(x => {
            x.forEach((v, i) => {
                ranges[i][0] = Math.min(ranges[i][0], v)
                ranges[i][1] = Math.max(ranges[i][1], v)
            })
        })
        on_change(ranges)
    })
    return parcoords
}

const urlParams = new URLSearchParams(window.location.search)

if (!urlParams.has('run') || !urlParams.has('stage')) {
    alert('Query must have run and stage. i.e http://localhost:3000/?run=t1000&stage=3')
} else {
    const run   = urlParams.get('run')
    const stage = urlParams.get('stage')
    const url   = `data/${run}/rundata_${stage}.json`

    let mode  = partition_draw_mode.value
    let district_idx = 0


    fetch_json(url).then(data => {
        if (!data) return alert(url + ' Not found.')
        console.log('Got data:', data)
        const { state, solutions, values, metrics_data } = data
        const { n_districts, metrics } = data.config
        const colors: string[] = Array(n_districts).fill(0).map(randomColor)
        // let ranges = Array(values[0].length).map(() => [Infinity, -Infinity])

        function update() {
            draw_district(
                canvas_partition,
                ctx_partition,
                state,
                solutions[district_idx],
                metrics_data.bounding_hulls[district_idx],
                colors,
                mode
            )
            update_text(div_text, data, district_idx, colors)
        }

        const chart_config = {
            onHover: p_i => {
                district_idx = p_i
                update()
            }
        }
        chart = make_chart(chart_config, ctx_pf, values, 1, 0, metrics )

        create_parcoords(data, ranges => {
            update_pareto_plot(data, ranges)
        })

        partition_draw_mode.onchange = (event: Event) => {
            mode = partition_draw_mode.value
            update()
        }

        update()
    })
}