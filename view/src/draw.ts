import { District, State, TileEdge } from './types'
declare var d3: any;

function polygon(ctx, points: number[][]) {
    ctx.beginPath()
    ctx.moveTo(points[0][0], points[0][1])
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1])
    }
    ctx.lineTo(points[0][0], points[0][1])
    ctx.closePath()
}

export function draw_district(
    canvas: HTMLCanvasElement,
    ctx: any,
    state: State,
    district: District,
    bounding_hulls: number[][][],
    colors: string[],
    mode: string
) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const [ xmin, ymin, xmax, ymax ] = state.bbox
    const scale = Math.min(canvas.width/(xmax-xmin), canvas.height/(ymax-ymin))

    const pmap = ([x, y]: [number, number]): [number, number] => {
        return [(x-xmin) * scale, canvas.height - (y-ymin) * scale]
    }

    let tile_colors
    if (mode == 'voters') {
        // Colors are the normalized voter ratios.
        const ratios = state.voters.map(([ v1, v2 ]) => v1/(v1+v2))
        const rmin = Math.min(...ratios.filter(x => !isNaN(x)))
        const rmax = Math.max(...ratios.filter(x => !isNaN(x)))
        // console.log({rmin, rmax});
        const normed_ratios = ratios.map(r => (r-rmin) / (rmax-rmin))
        // console.log(normed_ratios);
        tile_colors = normed_ratios.map(v => isNaN(v) ? [0,0,0] : d3.interpolateRdBu(v))

    }  else if (mode == 'districts') {
        const n_tiles = state.shapes.length
        tile_colors = Array(n_tiles).fill(0).map((_, tid) => colors[district[tid]])
    } else {
        // Colors are the normalized voter ratios.
        const pmin = Math.min(...state.populations)
        const pmax = Math.max(...state.populations)
        const normed_pops = state.populations.map(r => (r-pmin) / (pmax-pmin))
        tile_colors = normed_pops.map(v => d3.interpolateGreens(v))
    }

    district.forEach((di:number, ti:number) => {
        ctx.lineWidth = 1
        ctx.fillStyle = tile_colors[ti]
        ctx.strokeStyle = 'darkgray'
        // console.log(state.shapes[ti].length);
        state.shapes[ti].forEach(poly => {
            polygon(ctx, poly.map(pmap))
            ctx.fill()
            ctx.stroke()
        })

    })

    ctx.lineWidth = 2
    ctx.strokeStyle = 'black'
    state.tile_edges.forEach((tile_edge_data, ti0) => {
        for (let ti1 of Object.keys(tile_edge_data))  {
            const edge_data: TileEdge = tile_edge_data[ti1]
            if (ti1 == 'boundry' || district[ti0] != district[ti1]) {
                for (const [ p1, p2 ] of edge_data.edges) {
                    ctx.beginPath()
                    ctx.moveTo(...pmap(p1))
                    ctx.lineTo(...pmap(p2))
                    ctx.closePath()
                    ctx.stroke()
                }
            }
        }
    })
    // bounding_hulls.forEach(hull => {
    //     ctx.lineWidth = 1
    //     ctx.strokeStyle = 'black'
    //     polygon(ctx, hull.map(([x, y]) => {
    //         return [(x-xmin) * scale, canvas.height - (y-ymin) * scale]
    //     }))
    //     ctx.stroke()
    // })
}