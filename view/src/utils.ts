export function fetch_json(url: string, params?:object): Promise<any> {
    return fetch(url).then(resp => resp.ok ? resp.json() : null )
}
export function sum(arr) { return arr.reduce((a, b) => a+b) }
export function mean(arr) { return sum(arr) / arr.length }