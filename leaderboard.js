// Data loading function
async function loadData() {
    const dataFiles = {
        safeguardData: '../../../data/safeguard_evaluation_results.csv'
    };

    try {
        console.log('Starting data loading...');
        const response = await fetch(dataFiles.safeguardData);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvText = await response.text();
        const safeguardData = d3.csvParse(csvText);
        
        // Validate FPR data
        console.log('CSV columns:', Object.keys(safeguardData[0]));
        console.log('Sample row:', safeguardData[0]);
        
        return safeguardData;
    } catch (error) {
        console.error('Error in loadData:', error);
        throw error;
    }
}

// Visualization functions (from original scripts.js)
function createStatsCards(data) {
    // ... (copy the existing createStatsCards function)
}

function createBELLSScorePlot(data) {
    // Sort data by BELLS score
    const sortedData = [...data].sort((a, b) => parseFloat(b.bells_score) - parseFloat(a.bells_score));

    const trace = {
        x: sortedData.map(d => parseFloat(d.bells_score)),
        y: sortedData.map(d => d.safeguard),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: '#4A90E2',
            opacity: 0.8
        }
    };

    const layout = {
        title: 'BELLS Score Comparison',
        xaxis: {
            title: 'BELLS Score',
            range: [0, 1]
        },
        yaxis: {
            title: 'Safeguard'
        },
        margin: { l: 150 },  // Increase left margin for safeguard names
        height: 400,
        showlegend: false
    };

    Plotly.newPlot('bellsScorePlot', [trace], layout);
}

function createRadarPlot(data) {
    const metrics = [
        'tpr_harmful_adversarial',
        'tpr_harmful_non-adversarial',
        'tpr_borderline_adversarial',
        'tpr_borderline_non-adversarial',
        '1-fpr_benign'  // Using 1-FPR for consistency (higher is better)
    ];

    const metricLabels = [
        'TPR Harmful Adversarial',
        'TPR Harmful Non-Adversarial',
        'TPR Borderline Adversarial',
        'TPR Borderline Non-Adversarial',
        'TNR Benign'
    ];

    const traces = data.map(safeguard => ({
        type: 'scatterpolar',
        r: metrics.map(m => m === '1-fpr_benign' ? 
            1 - parseFloat(safeguard.fpr_benign) : 
            parseFloat(safeguard[m])),
        theta: metricLabels,
        name: safeguard.safeguard,
        fill: 'toself',
        opacity: 0.5
    }));

    const layout = {
        polar: {
            radialaxis: {
                visible: true,
                range: [0, 1]
            }
        },
        showlegend: true,
        title: 'Detection Performance Across Categories',
        height: 500
    };

    Plotly.newPlot('radarPlot', traces, layout);
}

function createHarmPreventionPlot(data) {
    // Prepare data for harm prevention plot
    const categories = ['harmful', 'borderline', 'benign'];
    const types = ['adversarial', 'non-adversarial'];
    
    const traces = data.map(safeguard => {
        const adversarialData = categories.map(cat => parseFloat(safeguard[`tpr_${cat}_adversarial`]));
        const nonAdversarialData = categories.map(cat => 
            cat === 'benign' ? 1 - parseFloat(safeguard.fpr_benign) : parseFloat(safeguard[`tpr_${cat}_non-adversarial`])
        );

        return {
            name: safeguard.safeguard,
            x: [...categories, ...categories],
            y: [...adversarialData, ...nonAdversarialData],
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                dash: ['solid', 'dash'][0]
            }
        };
    });

    const layout = {
        title: 'Harm Prevention Performance',
        xaxis: {
            title: 'Content Category',
            showgrid: true
        },
        yaxis: {
            title: 'Detection Rate',
            range: [0, 1],
            showgrid: true
        },
        showlegend: true,
        height: 500
    };

    Plotly.newPlot('harmPreventionPlot', traces, layout);
}

function createRankingList(data) {
    const sortedData = [...data].sort((a, b) => parseFloat(b.BELLS_score) - parseFloat(a.BELLS_score));
    
    const rankingContainer = document.getElementById('rankingList');
    if (!rankingContainer) {
        console.error('Ranking list container not found');
        return;
    }

    rankingContainer.innerHTML = '';

    sortedData.forEach((item, index) => {
        const score = parseFloat(item.BELLS_score).toFixed(3);
        const rankingItem = document.createElement('div');
        rankingItem.className = `ranking-item ${index === 0 ? 'first-place' : ''}`;
        rankingItem.innerHTML = `
            <div class="rank-number">
                ${index === 0 ? 
                    '<i class="fas fa-trophy" style="color: #FFD700;"></i>' : 
                    `#${index + 1}`}
            </div>
            <div class="safeguard-name">${item.safeguard}</div>
            <div class="score-container">
                <div class="score-label">BELLS Score</div>
                <div class="bells-score">${score}</div>
            </div>
        `;
        rankingContainer.appendChild(rankingItem);
    });
}

function createCustomHeatmap(data) {
    // Configuration
    const margin = { top: 50, right: 200, bottom: 140, left: 150 };  // Increased right margin further
    const width = 1200 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Clear existing content
    d3.select("#customHeatmap").html("");

    // Categories with better labels
    const categories = [
        'Physical_harm', 'Economic_harm', 'Privacy', 'Harassment/Discrimination',
        'Disinformation', 'Expert_advice', 'Sexual/Adult_content', 'Malware/Hacking',
        'Fraud/Deception', 'Government_decision_making', 'CBRN'
    ];

    // Format category labels
    const formatCategoryLabel = (cat) => {
        return cat.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    };

    // Create SVG with responsive container
    const svg = d3.select("#customHeatmap")
        .append("svg")
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleBand()
        .range([0, width])
        .domain(categories)
        .padding(0.05);

    const y = d3.scaleBand()
        .range([height, 0])
        .domain(data.map(d => d.safeguard))
        .padding(0.05);

    // Custom color scale
    const colorScale = d3.scaleSequential()
        .interpolator(d3.interpolateRdBu)
        .domain([0.2, 0.8]);

    // Create cells
    const cells = svg.selectAll("rect")
        .data(data.flatMap(d => 
            categories.map(cat => ({
                safeguard: d.safeguard,
                category: cat,
                value: parseFloat(d[cat])
            }))
        ))
        .enter()
        .append("rect")
        .attr("x", d => x(d.category))
        .attr("y", d => y(d.safeguard))
        .attr("width", x.bandwidth())
        .attr("height", y.bandwidth())
        .attr("class", "heatmap-cell")
        .style("fill", d => colorScale(d.value))
        .attr("rx", 2)
        .attr("ry", 2);

    // Add cell values
    svg.selectAll("text.cell-value")
        .data(data.flatMap(d => 
            categories.map(cat => ({
                safeguard: d.safeguard,
                category: cat,
                value: parseFloat(d[cat])
            }))
        ))
        .enter()
        .append("text")
        .attr("class", "cell-value")
        .attr("x", d => x(d.category) + x.bandwidth() / 2)
        .attr("y", d => y(d.safeguard) + y.bandwidth() / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .style("font-size", "11px")
        .style("fill", d => d.value > 0.5 ? "#000" : "#fff")
        .text(d => (d.value * 100).toFixed(0) + "%");

    // Add axes with formatted labels
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("class", "axis-label")
        .style("text-anchor", "end")
        .attr("dx", "-.8em")
        .attr("dy", "1em")
        .attr("transform", "rotate(-45)")
        .text(d => formatCategoryLabel(d));

    svg.append("g")
        .call(d3.axisLeft(y))
        .selectAll("text")
        .attr("class", "axis-label");

    // After creating the axes, add axis labels
    // X-axis label
    svg.append("text")
        .attr("class", "axis-title")
        .attr("text-anchor", "middle")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 20)  // Position below the x-axis labels
        .text("Harm Categories");

    // Y-axis label
    svg.append("text")
        .attr("class", "axis-title")
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(-90)")  // Rotate for vertical text
        .attr("x", -height / 2)
        .attr("y", -margin.left + 50)  // Position to the left of the y-axis
        .text("Safeguards");

    // Add tooltip behavior
    const tooltip = d3.select(".heatmap-tooltip");
    
    cells.on("mouseover", function(event, d) {
        d3.select(this)
            .style("stroke", "#2c3e50")
            .style("stroke-width", "2");

        tooltip.style("opacity", 1)
            .html(`
                <strong>${d.safeguard}</strong><br/>
                ${formatCategoryLabel(d.category)}<br/>
                Score: ${(d.value * 100).toFixed(1)}%
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", function() {
        d3.select(this)
            .style("stroke", "none");
        tooltip.style("opacity", 0);
    });

    // Add legend
    const legendWidth = 40;
    const legendHeight = height;
    
    const legendScale = d3.scaleLinear()
        .domain([0, 100])  // Changed domain to 0-100 for percentages
        .range([legendHeight, 0]);

    const legendAxis = d3.axisRight(legendScale)
        .tickSize(6)
        .ticks(6)  // Reduced number of ticks to prevent overlap
        .tickFormat(d => d + "%");

    const legend = svg.append("g")
        .attr("class", "heatmap-legend")
        .attr("transform", `translate(${width + 100},0)`);  // Increased spacing from heatmap

    const defs = legend.append("defs");
    const gradient = defs.append("linearGradient")
        .attr("id", "legend-gradient")
        .attr("x1", "0%")
        .attr("x2", "0%")
        .attr("y1", "100%")  // Start from bottom
        .attr("y2", "0%");   // End at top

    gradient.selectAll("stop")
        .data([
            { offset: "0%", color: colorScale(0) },    // Red at bottom
            { offset: "50%", color: colorScale(0.5) }, // White in middle
            { offset: "100%", color: colorScale(1) }   // Blue at top
        ])
        .enter()
        .append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);

    legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#legend-gradient)")
        .style("stroke", "#e2e8f0")
        .style("stroke-width", "1px");

    legend.append("g")
        .attr("transform", `translate(${legendWidth},0)`)
        .attr("class", "legend-axis")
        .call(legendAxis);

    // Legend label
    legend.append("text")
        .attr("class", "axis-title")
        .attr("text-anchor", "middle")
        .attr("transform", `rotate(-90) translate(${-legendHeight/2}, ${-legendWidth +5})`)  // Adjusted rotation and position
        .text("Detection Rate");
}

function createFPRComparison(data) {
    // Configuration
    const margin = { top: 60, right: 30, bottom: 100, left: 150 };
    const width = 1000 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    // Process data
    const processedData = data.map(d => ({
        safeguard: d.safeguard,
        fpr: Math.min(100, parseFloat(d['benign_non-adversarial']) * 100)
    })).sort((a, b) => a.fpr - b.fpr);

    // Create SVG
    d3.select("#fprPlot").html("");
    const svg = d3.select("#fprPlot")
        .append("svg")
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Define scales
    const x = d3.scaleBand()
        .range([0, width])
        .domain(processedData.map(d => d.safeguard))
        .padding(0.4);

    const y = d3.scaleLinear()
        .range([height, 0])
        .domain([0, 100]);

    // Add grid lines
    svg.append("g")
        .attr("class", "grid-lines")
        .call(d3.axisLeft(y)
            .tickSize(-width)
            .tickFormat("")
            .ticks(5));

    // Add bars with gradient based on performance
    svg.selectAll("rect.bar")
        .data(processedData)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.safeguard))
        .attr("y", d => y(d.fpr))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d.fpr))
        .attr("rx", 6)
        .attr("ry", 6)
        .style("fill", d => {
            const color = d3.scaleLinear()
                .domain([0, 50, 100])
                .range(["#0567a5", "#f6a4a4", "#dc2626"]);
            return color(d.fpr);
        });

    // Add X axis
    svg.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y)
            .ticks(5)
            .tickFormat(d => d + "%"));

    // Add value labels
    svg.selectAll(".value-label")
        .data(processedData)
        .enter()
        .append("text")
        .attr("class", "value-label")
        .attr("x", d => x(d.safeguard) + x.bandwidth() / 2)
        .attr("y", d => y(d.fpr) - 10)
        .attr("text-anchor", "middle")
        .text(d => `${d.fpr.toFixed(1)}%`);

    // Add title with consistent styling
    svg.append("text")
        .attr("class", "plot-title")
        .attr("x", width / 2)
        .attr("y", -margin.top / 2)
        .attr("text-anchor", "middle")
        .text("False Positive Rate (Lower is Better)");

    // Add subtitle with consistent styling
    svg.append("text")
        .attr("class", "plot-subtitle")
        .attr("x", width / 2)
        .attr("y", -margin.top / 2 + 25)
        .attr("text-anchor", "middle")
        .text("Percentage of benign inputs incorrectly flagged as harmful");
}

// Initialize everything when the document is ready
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const data = await loadData();
        if (data) {
            createRankingList(data);
            createCustomHeatmap(data);
            createFPRComparison(data);
        }
    } catch (error) {
        console.error('Initialization error:', error);
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Initialization Error</h4>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
}); 