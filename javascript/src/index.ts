import * as ndarray from 'ndarray'
import { Renderer } from './render'
import * as random from './random'
import { World } from './classes/World'
import { Partition } from './classes/Partition'

// const ndarray = require('ndarray')
// const RENDER  = require('./render.js')
// const random = require('./random.js')
// const World = require('./classes/World.js')
// const Partition = require('./classes/Partition.js')
// Math.seedrandom('3')

const width:number = 16
const height:number = 16

const canvas = document.getElementById('c') as HTMLCanvasElement
canvas.width = Math.min(400, window.outerWidth)
canvas.height = Math.min(400, window.outerWidth)
const ctx = canvas.getContext('2d')
const render = new Renderer({ canvas, ctx, scale: canvas.width / width })

console.time('setup')
const world = World.createRandom({ width, height })
// let partition = Partition.createRandom({ world, n_areas: 4 })
console.timeEnd('setup')

// // setInterval(() => {
// ctx.clearRect(0, 0, canvas.width, canvas.height)
// Partition.makeChild({parent: partition})
// render.drawPartition(partition)
// render.drawWorld(world)
// // }, 50)

