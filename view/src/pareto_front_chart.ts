import { Chart } from 'chart.js'
type Point = { x: number, y: number}

export function update_chart(
    chart, values:number[], names:string[], idx1:number, idx2: number
){
    // const slider_values = sliders.map(s => parseFloat(s.value))
    // const values_filtered = values.map(v => {
    //     for (var i = 0; i < v.length; i++) {
    //         if (v[i] < slider_values[i]) return false
    //     }
    //     return true
    // })
    chart.data.datasets[0].data.forEach((v, i) => {
        // if (!values_filtered[i]) {
        //     v.x = null
        //     v.y = null
        // } else {
        v.x = values[i][idx1]
        v.y = values[i][idx2]
        // }
    });
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