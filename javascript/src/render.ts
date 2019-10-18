export class Renderer {
    ctx: any
    canvas: HTMLCanvasElement
    scale: number
    constructor({ ctx, canvas, scale }) {
        this.ctx = ctx
        this.canvas = canvas
        this.scale = scale
    }

    drawPartition(partition) {
        const { ctx, scale, canvas } = this
        for (let i = 0; i < partition.grid.shape[0]; i++) {
            for (let j = 0; j < partition.grid.shape[1]; j++) {
                const v = partition.grid.get(i, j)
                if (v > 0) {
                    ctx.beginPath()
                    ctx.fillStyle = partition.colors[v-1] + ''
                    ctx.rect(i*scale, j*scale, scale, scale)
                    ctx.fill()
                }
            }
        }
        // partition.frontiers
        // for (let v = 0; v < partition.num_areas; v++) {
            // console.log(partition.frontiers[v])
        partition.frontiers.forEach((front, v)  => {
            for (const [i, j] of front) {
                // ctx.beginPath()
                // ctx.strokeStyle = 'gray'
                // ctx.rect(i*scale, j*scale, scale, scale)
                // ctx.stroke()
            }
        })

    }

    drawWorld(world) {
        const { ctx, scale, canvas } = this
        const colors = [ 'blue', 'red' ]
        for (let i = 0; i < world.array.shape[0]; i++) {
            for (let j = 0; j < world.array.shape[1]; j++) {
                ctx.beginPath()
                ctx.strokeStyle = 'gray'
                ctx.rect(i*scale, j*scale, scale, scale)
                ctx.stroke()
                const v = world.array.get(i, j)
                if (v > 0) {
                    ctx.beginPath()
                    ctx.fillStyle = colors[v-1]
                    ctx.arc((i+.5)*scale, (j+.5)*scale, scale*0.3, 0, 2 * Math.PI, false)
                    ctx.closePath()
                    ctx.fill()
                }
            }
        }
    }
}