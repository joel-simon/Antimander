export function array2d(width: number, height: number, create_fn: any): Array<Array<any>> {
    const array = []
    for (let x = 0; x < width; x++) {
        const row = []
        for (let y = 0; y < width; y++) {
            row.push(create_fn(x, y))
        }
        array.push(row)
    }
    return array
}