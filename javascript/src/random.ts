export function choice(list: any[]): any {
    return list[Math.floor(Math.random()*list.length)]
}

export function randint(min: number, max:number): number {
    min = Math.ceil(min)
    max = Math.floor(max) // Exclusive
    return Math.floor(Math.random()*(max-min)) + min
}

export function random(min: number, max: number): number {
    return min + (max-min)*Math.random()
}

export function randstring(n: number): string {
    return [...Array(n)].map(i=>(~~(Math.random()*36)).toString(36)).join('')
}
