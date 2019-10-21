import { Chart } from 'chart.js'
console.log(Chart)
type Point = { x: number, y: number}

export function make_chart(
    config,
    chart_ctx,
    values: number[],
    idx1: number,
    idx2: number,
    names: string[]
) {
    const data: Point[] = values.map(v => ({ x: v[idx1], y: v[idx2] }))
    const options = {
        title: {
            display: false,
            text: ''
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
    return new Chart(chart_ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '',
                data: data
            }]
        },
        options
    })
}