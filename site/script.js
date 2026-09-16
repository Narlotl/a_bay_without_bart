// Scroll fade functions
const getScrollPercent = element => (window.scrollY - element.offsetTop) / element.scrollHeight;

const registerScrollFade = (
    scrollElement,
    fadeElement,
    opacityFunction = scrollPercent => 1 - scrollPercent,
    dNone = true // Whether or not to set display to none at 0 opacity
) =>
    window.addEventListener('scroll', () => {
        const scrollPercent = getScrollPercent(scrollElement);
        if (scrollPercent < -0.5 || scrollPercent > 1.5)
            return;

        const opacity = opacityFunction(scrollPercent);
        fadeElement.style.opacity = opacity;
        if (dNone) {
            if (opacity <= 0)
                fadeElement.style.display = 'none';
            else
                fadeElement.style.display = 'initial';
        }
    });


// Set up fade for title
registerScrollFade(
    document.getElementById('title-scroll'),
    document.getElementById('title'),
    scrollPercent => 1 - (scrollPercent - 0.25) * 4
);


// Set up fade for shutdown phase maps
const phaseDescriptions = document.querySelectorAll('#service-cut-descriptions > p'),
    phaseMaps = document.querySelectorAll('#service-cut-maps img');
for (let i = 0; i < phaseDescriptions.length - 1; i++)
    registerScrollFade(phaseDescriptions[i], phaseMaps[i])


const bartIcon = L.icon({
    iconUrl: 'assets/bart.png',
    iconSize: [20, 16.7]
});
// 11-color ramp using MTC colors: https://mtc.ca.gov/sites/default/files/documents/2026-02/RegionalNetworkIdentityDesignGuide260217.pdf#page=5
const colorRamp = [
    '#011E41',
    '#1D4062',
    '#396184',
    '#5583A5',
    '#71A4C7',
    '#8DC6E8',
    '#A3C3BD',
    '#BAC193',
    '#D0BE68',
    '#E7BC3E',
    '#FDB913',
];
/* Returns the color for the class of a value.
 * @param {number} value - Value to classify.
 * @param {array} classes - Array of lower bounds of each class.
 * @param {boolean} fill - Whether to color the fill or border.
 */
const featureColor = (value, classes, fill = true, fillOpacity = 0.8, weight = 1, opacity = 0.8) => {
    if (classes.length !== colorRamp.length)
        throw new RangeError('Must have ' + colorRamp.length + ' classes.');

    for (let i = classes.length - 1; i >= 0; i--)
        if (value >= classes[i]) {
            const style = {
                fillOpacity,
                weight,
                opacity,
            };
            if (fill) {
                style.fillColor = colorRamp[i];
                style.color = 'black';
            }
            else
                style.color = colorRamp[i];
            return style;
        }
};

/* Creates a legend window for given class bounds.
 * @param {array} classes - Array of lower bounds of classes.
 */
const createLegend = (title, classes) => {
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = () => {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML = '<b>' + title + '</b><br>';
        for (let i = 0; i < colorRamp.length - 1; i++)
            div.innerHTML += `
                <span style="background-color: ${colorRamp[i]}" class="legend-color">　</span>
                <span>${classes[i]} - ${classes[i + 1]}</span>
                <br>
            `;
        div.innerHTML += `
            <span style="background-color: ${colorRamp[colorRamp.length - 1]}" class="legend-color">　</span>
            <span>${classes[classes.length - 1]}+</span>
            <br>
        `;
        return div;
    };

    return legend;
};

// Group highlight functions
const addToGroups = (feature, layer, groups) => {
    if (feature.properties.tags)
        for (const tag of feature.properties.tags) {
            if (!tag)
                continue;

            const obj = { feature, layer };
            if (groups[tag])
                groups[tag].push(obj);
            else
                groups[tag] = [obj];
        }
};
// Register highlight events for description hover
const registerGroupMouseEvents = (groups, section, geojson, highlightLayer, highlightedLayer, originalStyle) => {
    for (const tag in groups) {
        const span = document.getElementById(tag + '-' + section);
        const features = groups[tag];
        span.addEventListener('mouseover', () => {
            for (const feature of features)
                highlightLayer(feature.feature, feature.layer);
        });
        span.addEventListener('mouseout', () => {
            for (const feature of features)
                if (feature.layer !== highlightedLayer[0]) {
                    if (originalStyle)
                        feature.layer.setStyle(originalStyle);
                    else
                        geojson.resetStyle(feature.layer);
                }
        });
    }
};
// Highlight features on click
const registerClickHighlight = (geojson, map, highlightLayer, highlightedLayer, originalStyle) => {
    geojson.on('click', e => {
        // Remove highlight on currently highlighted layer
        if (e.layer != highlightedLayer[0])
            geojson.resetStyle(highlightedLayer[0]);

        highlightLayer(e.layer.feature, e.layer);
        highlightedLayer[0] = e.layer;
    });
    map.on('click', () => {
        if (!highlightedLayer[0])
            return;

        if (originalStyle)
            highlightedLayer[0].setStyle(originalStyle);
        else
            geojson.resetStyle(highlightedLayer[0]);
    });
};


// Communities affected map

const caMap = L.map('communities-map').setView([37.4964295, -121.868408], 9);
L.tileLayer('http://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    minZoom: 9,
    maxZoom: 13,
    attribution: '&copy; <a href="https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer">ArcGIS</a>'
}).addTo(caMap);

fetch('data/data_acs_square.geojson').then(res => res.json()).then(data => {
    const classes = [0, 5, 10, 15, 20, 30, 50, 75, 125, 200, 400];
    createLegend('BART Commuters / km²', classes).addTo(caMap);

    // Set up groups to be highlighted when their names are hovered in the description
    const groups = {};

    const geojson = L.geoJSON(data, {
        style: feature => featureColor(feature.properties.density, classes),
        onEachFeature: (feature, layer) => {
            const popup = layer.bindPopup(feature.properties.density.toFixed(1) + ' BART commuters / km² (' + feature.properties.total + ' total)');
            // Remove highlight when popup closed
            popup.on('popupclose', () => geojson.resetStyle(layer));

            addToGroups(feature, layer, groups);
        }
    }).addTo(caMap);

    const highlightLayer = (feature, layer) =>
        layer.setStyle(featureColor(feature.properties.density, classes, true, 1.0, 1.5));

    const highlightedLayer = []; // Must be stored in array so it can be modified across scopes (like a pointer)
    registerGroupMouseEvents(groups, 'ca', geojson, highlightLayer, highlightedLayer);
    registerClickHighlight(geojson, caMap, highlightLayer, highlightedLayer);
});

registerScrollFade(document.getElementById('communities-description'), document.getElementById('communities-map'), scrollPercent => 1 - (scrollPercent - 0.5) * 4);


// Traffic section

const tMap = L.map('traffic-map').setView([37.6, -122], 10);
L.tileLayer('http://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    minZoom: 9,
    maxZoom: 15,
    attribution: '&copy; <a href="https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer">ArcGIS</a>'
}).addTo(tMap);

const bindHighwayPopup = (feature, layer) => {
    const route = feature.properties.route;
    let routePrefix;
    if (route.endsWith('0') || route.endsWith('5') || route === '238')
        routePrefix = 'I-';
    else if (route === '101')
        routePrefix = 'US ';
    else
        routePrefix = 'SR ';

    layer.bindPopup(`
        <b>${routePrefix}${route}</b>
        <br>
        Current peak hour: ${feature.properties.current_peak} cars
        <br>
        Additional peak hour: ${feature.properties.additional_peak} cars (+${feature.properties.increase_percent.toFixed(1)}%)
    `);
}

fetch('data/traffic_simplified.geojson').then(res => res.json()).then(data => {
    const totalClasses = [0, 3000, 5000, 7500, 10000, 11500, 12500, 13000, 14000, 15000, 16500];
    createLegend('Cars During Peak Hour', totalClasses).addTo(tMap);

    const groups = {};

    const additionalTraffic = L.geoJSON(data, {
        onEachFeature: (feature, layer) => {
            bindHighwayPopup(feature, layer);
            addToGroups(feature, layer, groups);
        },
        style: feature => featureColor(feature.properties.current_peak, totalClasses, false, 0, 4)
    });

    // Interpolate between current and additional color on scroll
    const scrollElement = document.getElementById('current-traffic-description');
    window.addEventListener('scroll', () => {
        const scrollPercent = getScrollPercent(scrollElement);
        if (scrollPercent < 0 || scrollPercent > 1)
            return;

        additionalTraffic.setStyle(feature =>
            featureColor(feature.properties.current_peak + feature.properties.additional_peak * scrollPercent, totalClasses, false, 0, 4)
        );
    });

    additionalTraffic.addTo(tMap);

    const highlightedLayer = [];
    const highlightLayer = (_, layer) =>
        layer.setStyle({ weight: 8 });

    registerClickHighlight(additionalTraffic, tMap, highlightLayer, highlightedLayer, { weight: 4 });
    registerGroupMouseEvents(groups, 'traffic', additionalTraffic, highlightLayer, highlightedLayer, { weight: 4 });
});


// Set up chart styles
const
    skyBlue = {
        backgroundColor: colorRamp[5] + 'cc',
        borderColor: colorRamp[5],
        borderWidth: 2
    },
    goldenYellow = {
        backgroundColor: colorRamp[10] + 'cc',
        borderColor: colorRamp[10],
        borderWidth: 2
    };
Chart.defaults.color = '#ffffff';
Chart.defaults.borderColor = 'rgba(255,255,255,0.2)';


// Bus replacement section

fetch('data/buses.csv').then(res => res.text()).then(csv => {
    csv = csv.split('\n').map(r => r.split(',')).sort((a, b) => parseInt(b[1]) - parseInt(a[1]));
    csv.shift();
    csv.pop();

    // Fill fallback table
    const table = document.getElementById('bus-table-body');

    const labels = [], current = [], additional = [];
    for (const row of csv) {
        labels.push(row[0]);
        current.push(parseInt(row[1]));
        additional.push(parseInt(row[2]));

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row[0]}</td>
            <td>${row[1]}</td>
            <td>${row[2]}</td>
        `;
        table.appendChild(tr);
    }

    // Fill bar chart
    new Chart(document.getElementById('bus-count-canvas'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Current Fleet Size',
                    data: current,
                    ...skyBlue
                },
                {
                    label: 'Additional Buses Needed',
                    data: additional,
                    ...goldenYellow
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        padding: { top: 16 },
                        text: 'Agency'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Buses'
                    }
                }
            }
        }
    });
});


// AC Transit cost chart

new Chart(document.getElementById('bus-cost-canvas'), {
    type: 'bar',
    data: {
        labels: ['Capital Budget', 'Operations'],
        datasets: [
            {
                label: 'Current',
                data: [407.6, 349.4],
                ...skyBlue
            },
            {
                label: 'Additional',
                data: [327.9, 67.5],
                ...goldenYellow
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                title: {
                    display: true,
                    padding: { top: 16 },
                    text: 'Budget Category'
                }
            },
            y: {
                title: {
                    display: true,
                    padding: { bottom: 16 },
                    text: 'Expenses (millions of dollars)'
                }
            }
        }
    }
});

registerScrollFade(document.getElementById('xhe60-description'), document.getElementById('xhe60-image'), scrollPercent => 1 - scrollPercent * 2);
registerScrollFade(document.getElementById('bus-count-description'), document.getElementById('bus-count-canvas'), scrollPercent => 1 - scrollPercent * 2);
registerScrollFade(document.getElementById('bus-cost-description'), document.getElementById('bus-cost-canvas'), scrollPercent => 1 - scrollPercent * 2);


// Connecting routes section

const shuffle = arr => {
    const ret = [];
    for (let i = 0; i < arr.length; i++)
        ret.push(arr.splice(Math.floor(Math.random() * arr.length), 1)[0]);
    return ret;
};
const darkBlueHue = 212.8 / 360; // Default to dark blue
// https://gist.github.com/mjackson/5311256
const hexToHue = hex => {
    if (!hex)
        return darkBlueHue;

    const r = parseInt(hex.substring(0, 2), 16) / 255,
        g = parseInt(hex.substring(2, 4), 16) / 255,
        b = parseInt(hex.substring(4), 16) / 255;

    let max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = (max + min) / 2;

    if (max === min)
        h = s = 0; // achromatic
    else {
        const d = max - min;

        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }

        h /= 6;
    }

    return h;
}

fetch('data/connecting_routes.csv').then(res => res.text()).then(data => {
    data = data.split('\n').map(r => r.split(','));
    data.shift();
    data.pop();
    data = data.sort((a, b) => hexToHue(a[3]) - hexToHue(b[3]))

    // Alternate between sides
    const scrollSections = document.querySelectorAll('#connecting-routes > .w30');
    for (let i = 0; i < data.length; i++) {
        const route = data[i];
        let name;
        if (route[0]) {
            // Prefix with short name if it exists
            name =
                `<b class="line-pill" style="
                    background-color: ${route[3] ? '#' + route[3] : 'var(--dark-blue)'};
                    color: ${(route[3] && route[4]) ? '#' + route[4] : 'white'}
                ">`
                + route[0] + '</b>';
            // Add route name
            if (route[1] && route[1] !== route[0])
                name += ' ' + route[1];
        }
        else
            name = route[1];
        // Add agency name
        name += ' (' + route[2] + ')';

        scrollSections[i % 2].innerHTML += '<p>' + name + '</p>';
    }

    for (const child of scrollSections)
        registerScrollFade(
            document.getElementById('connecting-routes-description'),
            child,
            scrollPercent => 1 - (scrollPercent * 2),
            false
        );
});


// Restaurants and shops (destinations) section

const destinationsList = document.getElementById('destinations-list');
Promise.all(
    [
        fetch('data/restaurants.csv'),
        fetch('data/shops.csv')
    ].map(f => f.then(r => r.text()))
).then(data => {
    data = data.map(d => d.split('\n').slice(1)).flat() // Merge both files
        .map(r => {
            // Split rows into columns
            const index = r.lastIndexOf(',');

            let name = r.substring(0, index);
            if (name.startsWith('"') && name.endsWith('"'))
                name = name.substring(1, name.length - 1);

            const station = r.substring(index + 1);

            return [name, station];
        })
        .filter(r => r[0])
        .sort((a, b) => (a[0] + a[1]).localeCompare((b[0] + b[1])));

    for (const destination of data) {
        const p = document.createElement('p');
        p.innerText = destination[0] + ' (' + destination[1] + ')';
        destinationsList.appendChild(p);
    }
});

const contentsArrow = document.getElementById('contents-arrow'),
    contentsButton = document.getElementById('contents-button'),
    contentsList = document.getElementById('contents-list');
const toggleContents = () => {
    const hidden = contentsList.classList.toggle('hidden');
    contentsArrow.innerText = hidden ? '⮝' : '⮟';
    contentsArrow.title = hidden ? 'Expand' : 'Collapse';
};
contentsButton.addEventListener('click', toggleContents);
contentsList.addEventListener('click', toggleContents);
