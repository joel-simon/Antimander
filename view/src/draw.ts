import { District, State, TileEdge } from './types'
declare var d3: any;

const BLUE = d3.color('rgba(4, 26, 232, 1.0)')
const PURPLE = d3.color('rgba(132, 31, 245, 1.0)')
const RED = d3.color('rgba( 188, 0, 26, 1.0)')

function polygon(ctx, points: number[][]) {
    ctx.beginPath()
    ctx.moveTo(points[0][0], points[0][1])
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1])
    }
    ctx.lineTo(points[0][0], points[0][1])
    ctx.closePath()
}

function norm(array) {
    const min = Math.min(...array.filter(x => !isNaN(x)))
    const max = Math.max(...array.filter(x => !isNaN(x)))
    return array.map(x => (x-min) / (max-min))
}

export function draw_district(
    canvas: HTMLCanvasElement,
    ctx: any,
    state: State,
    district: District,
    n_districts: number,
    bounding_hulls: number[][][],
    mode: string
) {
    console.time('draw')
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
        tile_colors = norm(ratios).map(v => isNaN(v) ? [0,0,0] : d3.interpolateRdBu(v))

    }  else if (mode == 'districts') {
        // const color_fn = d3.scale.linear().domain([ 0, 0.5, 1.0 ])
        //         .interpolate(d3.interpolateHcl)
        //         .range([ BLUE, PURPLE, RED ])
        const color_fn = d3.interpolateRdBu

        const party_1 = new Array(n_districts).fill(0)
        const party_2 = new Array(n_districts).fill(0)
        district.forEach((di:number, tile_idx:number) => {
            party_1[di] += state.voters[tile_idx][0]
            party_2[di] += state.voters[tile_idx][1]
        })
        const ratios = party_1.map((v, idx) => (v-party_2[idx]) / (v+party_2[idx]))
        // const dist_colors = norm(ratios).map(v => color_fn(v))
        const dist_colors = ratios.map(v => color_fn(3*v+ 0.5))
        const n_tiles = state.shapes.length
        tile_colors = Array(n_tiles).fill(0).map((_, tid) => dist_colors[district[tid]])
        // tile_colors = .map((_, tid) => colors[district[tid]])

    } else {
        // Colors are the normalized voter ratios.
        const pmin = Math.min(...state.populations)
        const pmax = Math.max(...state.populations)
        const normed_pops = state.populations.map(r => (r-pmin) / (pmax-pmin))
        tile_colors = normed_pops.map(v => d3.interpolateGreens(v))
    }

    district.forEach((di:number, ti:number) => {
        ctx.lineWidth = 2
        ctx.fillStyle = tile_colors[ti]
        ctx.strokeStyle = tile_colors[ti]
        // ctx.strokeStyle = 'darkgray'
        state.shapes[ti].forEach(poly => {
            polygon(ctx, poly.map(pmap))
            ctx.fill()
            ctx.stroke()
        })
    })

    state.tile_edges.forEach((tile_edge_data, ti0) => {
        for (let ti1 of Object.keys(tile_edge_data))  {
            const edge_data: TileEdge = tile_edge_data[ti1]
            // if (ti1 == 'boundry') {
            //     continue
            // }
            if (ti1 == 'boundry' || district[ti0] != district[ti1]) {
                ctx.lineWidth = 2
                ctx.strokeStyle = 'white'
            } else {
                ctx.lineWidth = 1
                ctx.strokeStyle = 'gray'
                // continue
            }
            for (const [ p1, p2 ] of edge_data.edges) {
                ctx.beginPath()
                ctx.moveTo(...pmap(p1))
                ctx.lineTo(...pmap(p2))
                ctx.closePath()
                ctx.stroke()
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
    console.timeEnd('draw')
}