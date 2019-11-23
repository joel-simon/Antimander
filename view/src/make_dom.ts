function generateTableHead(table, data) {
    let thead = table.createTHead();
    let row = thead.insertRow();
    for (let key of data) {
        let th = document.createElement("th");
        let text = document.createTextNode(key);
        th.appendChild(text);
        row.appendChild(th);
    }
}

function generateTableBody(table, data) {
    for (let element of data) {
        let row = table.insertRow();
        for (let key in element) {
            let cell = row.insertCell();
            let text = document.createTextNode(element[key]);
            cell.appendChild(text);
        }
    }
}

function string2dom(s: string):HTMLElement {
    const dom = new DOMParser().parseFromString(s, "text/html")
    return dom.body.firstChild as HTMLElement
}

export function generateTable(table, data) {
    const headers = Object.keys(data[0])
    generateTableBody(table, data)
    generateTableHead(table, headers)
}

export function makeSlider(name):HTMLElement {
    return string2dom(`
    <div class="slidecontainer" data-name="${name}">
        <p>${name}</p>
        <input class="slider" id="myRange" type="range" min="0" max="100" value="0" step="any" />
    </div>
    `)
}
