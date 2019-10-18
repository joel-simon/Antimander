// import * as ndarray from 'ndarray'
import { randint } from '../random'
import { array2d } from '../utils'

interface Point {
    x: number,
    y: number
}

interface WorldElement {
    position: Point,
    voter: number
}

export class World {
    // readonly width: number
    // readonly height:number
    readonly data:  Array<Array<WorldElement>>
    readonly border:Array<WorldElement>

    constructor(
        readonly width: number,
        readonly height: number
    ) {
        this.width = width
        this.height = height
        this.data = array2d(width, height, (x, y) => {
            return { position: {x, y}, voter:0 }
        })
        this.border = []
        for (let x = 0; x < width-1; x++) {
            this.border.push(this.data[x][0])
            this.border.push(this.data[x][height-1])
        }
        for (let y = 1; y < height-2; y++) {
            this.border.push(this.data[0][y])
            this.border.push(this.data[width-1][y])
        }
    }

    static createRandom({ width, height, n_classes=2, p=.05 }):World {
        const world = new World( width, height )
        for (let x = 0; x < width; x++) {
            for (let y = 0; y < width; y++) {
                if (Math.random() < p) {
                    world.data[x][y].voter = randint(0, n_classes)
                }
            }
        }
        return world
    }
}


// const array = ndarray(new Uint8Array(width * height), [ width, height ])
// for (let i = 0; i < width*height; i++) {
//     const r = Math.random()
//     if (r < .15) {
//         array.data[i] = 1
//     } else if (r < .30) {
//         array.data[i] = 2
//     }
// }
// return new World({ array })