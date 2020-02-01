import { Chart } from 'chart.js'
type Point = { x: number, y: number}

export function update_chart(
    chart,
    values: number[][],
    names:string[],
    idx1:number,
    idx2: number,
    ranges: [number, number][]
){
    const min_max = []
    for (let i = 0; i < values[0].length; ++i) {
        const v = values.map(v => v[i])
        min_max.push([ Math.min(...v), Math.max(...v) ])
    }

    // const thresholds = min_max.map(([min, max], idx) => {
    //     return min + (max-min) * (1.0 - filters[idx])
    // })
    const values_filtered = values.map(v => {
        for (let i = 0; i < v.length; i++) {
            if (v[i] < ranges[i][0] || v[i] > ranges[i][1]) {
                return false
            }
        }
        return true
    })
    chart.data.datasets[0].data.forEach((v, i) => {
        if (!values_filtered[i]) {
            v.x = null
            v.y = null
        } else {
            v.x = values[i][idx1]
            v.y = values[i][idx2]
        }
    })
    chart.options.scales.xAxes[0].scaleLabel.labelString = names[idx1]
    chart.options.scales.yAxes[0].scaleLabel.labelString = names[idx2]
    chart.update()
}

export function make_chart(
    config,
    chart_ctx,
    values: number[],
    idx1: number,
    idx2: number,
    names: string[]
) {
    const data: Point[] = values.map(v => ({ x: v[idx1], y: v[idx2] }))
    return new Chart(chart_ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '',
                data: data,
                fill: false
            }]
        },
        options: {
            title: {
                display: false,
                text: ''
            },
            legend: {
                display: false
            },
            responsive: true,
            aspectRatio: 1.0,
            // maintainAspectRatio: false,
            tooltips : {
                callbacks: {
                }
            },
            scales: {
                xAxes: [{
                    type: 'linear',
                    // position: 'bottom',
                    gridLines: { display: false },
                    scaleLabel: {
                        display: true,
                        labelString: names[idx1]
                    }
                }],
                yAxes: [{
                    type: 'linear',
                    // position: 'bottom',
                    gridLines: { display: false },
                    scaleLabel: {
                        display: true,
                        labelString: names[idx2]
                    }
                }]
            },
            onClick (evt, [item]) {
                if (item && config.onClick) {
                    config.onClick(item._index)
                }
            },
            onHover (evt, [item]) {
                if (item && config.onHover) {
                    config.onHover(item._index)
                }
            },
        }
    })
}