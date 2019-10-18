import * as randomColor from 'randomColor'
import * as random from '../random.js'
import { World } from './World'
import { array2d } from '../utils'

interface Point {
    x: number;
    y: number;
}

interface PartitionElement {
    position: Point,
    district: number
}

export class Partition {
    /* Store a partition of World.
    */
    world: World
    data: Array<Array<PartitionElement>>
    frontiers: Array<Array<PartitionElement>>
    readonly colors: Array<any>

    constructor({ world, data, frontiers,  colors }) {
        this.world = world
        this.data = data
        this.colors = colors
        this.frontiers = frontiers
    }

    static createRandom({ world, n_areas }) {
        // const data = ndarray(new Uint8Array(world.array.size), world.array.shape)
        const colors = []
        let frontiers = []

        const data = array2d(world.width, world.height, (x, y) => {
            return { position: {x, y}, district:-1 }
        })

        for (let i = 0; i < n_areas; i++) {
            // Pick a unique border position as a seed.
            let seed
            do {
                seed = random.choice(world.border)
            } while ( data[seed.position.x][seed.position.x].district != -1 )
            data[seed.position.x][seed.position.x].district = i
            frontiers.push([ seed ])
            colors.push( randomColor() )
        }

        /* Fill space
        */
        let filled = n_areas
        while (filled < world.array.size) {
            for (let i = 0; i < n_areas; i++) {
                const grow_src = random.choice(frontiers[i])
                const dst_opts = Array.from(open_neighbors_idxs(data, grow_src[0], grow_src[1]))
                if (dst_opts.length == 0) continue;
                const grow_dst = random.choice(dst_opts)
                data.set(grow_dst[0], grow_dst[1], i+1)
                filled ++
            }
            frontiers = frontiers.map(() => [])
            for (let i = 0; i < data.shape[0]; i++) {
                for (let j = 0; j < data.shape[1]; j++) {
                    const v = data.get(i, j)
                    if (v > 0) {
                        if (is_frontier(data, i, j, v)) {
                            frontiers[v-1].push([i, j])
                        }
                    }
                }
            }
        }
        return new this({ data, colors, frontiers })
    }

    static makeChild({ parent, mutation_amount }) {
        const random_front = random.choice(parent.frontiers)
        const v = parent.frontiers.indexOf(random_front)

        const [i, j] = random.choice(random_front)

        const neighbors = Array.from(neighbor_values(parent.data, i, j))

        const options = neighbors.filter(v2 => v2 != v)
        const same_neighbors = neighbors.filter(v2 => v2 == v)
        console.log(same_neighbors.length)
        if (same_neighbors.length == 2) {
            /* Dont allow breaking connectivity. */
            return
        }

        if (options.length == 0) return
        const derp = random.choice(options)

        parent.data.set(i, j, derp)

        parent.frontiers = parent.frontiers.map(() => [])
        for (let i = 0; i < parent.data.shape[0]; i++) {
            for (let j = 0; j < parent.data.shape[1]; j++) {
                const v = parent.data.get(i, j)
                if (v > 0) {
                    if (is_frontier(parent.data, i, j, v)) {
                        parent.frontiers[v-1].push([i, j])
                    }
                }
            }
        }
    }
}

function is_frontier(data, i, j, v1):boolean {
    for (const v2 of neighbor_values(data, i, j)) {
        if (v1 != v2) return true
    }
    return false
}

function* open_neighbors_idxs(nda, i, j): Array<> {
    if (i > 0 && nda.get(i-1, j) == 0) yield [i-1, j]
    if (i < nda.shape[0]-1 && nda.get(i+1, j) == 0) yield [i+1, j]
    if (j > 0 && nda.get(i, j-1) == 0) yield [i, j-1]
    if (j < nda.shape[1]-1 && nda.get(i, j+1) == 0) yield [i, j+1]
}
function* neighbor_values(nda, i, j) {
    if (i > 0) yield nda.get(i-1, j)
    if (j > 0) yield nda.get(i, j-1)
    if (i < nda.shape[0]-1) yield nda.get(i+1, j)
    if (j < nda.shape[1]-1) yield nda.get(i, j+1)
}