// Data loading function
async function loadData() {
    console.log("Starting data loading...");
    const dataFiles = {
        safeguardData: '../../../data/safeguard_evaluation_results.csv'
    };

    try {
        const response = await fetch(dataFiles.safeguardData);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvText = await response.text();
        const data = d3.csvParse(csvText);
        
        // Validate FPR data
        console.log('CSV columns:', Object.keys(data[0]));
        console.log('Sample row:', data[0]);
        
        return data;
    } catch (error) {
        console.error("Error loading data:", error);
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

    // Find best scores for each metric
    const bestScores = {
        detection_adv: Math.max(...data.map(item => parseFloat(item.harmful_jailbreaks))),
        detection_non_adv: Math.max(...data.map(item => parseFloat(item["harmful_non-adversarial"]))),
        fpr: Math.min(...data.map(item => parseFloat(item["benign_non-adversarial"]))), // Lower is better for FPR
        bells: Math.max(...data.map(item => parseFloat(item.BELLS_score)))
    };

    // Add color scale legend
    const legendDiv = document.createElement('div');
    legendDiv.className = 'score-legend';
    legendDiv.innerHTML = `
        <div class="legend-title">
            <i class="fas fa-palette"></i> Score Color Scale
        </div>
        <div class="legend-scale">
            <div class="legend-item">
                <div class="legend-color poor"></div>
                <span>Poor (0.0 - 0.5)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color fair"></div>
                <span>Fair (0.5 - 0.7)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color good"></div>
                <span>Good (0.7 - 0.9)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color excellent"></div>
                <span>Excellent (0.9 - 1.0)</span>
            </div>
        </div>
    `;
    rankingContainer.appendChild(legendDiv);

    // Create header row with tooltips
    const headerRow = document.createElement('div');
    headerRow.className = 'ranking-header';
    headerRow.innerHTML = `
        <div class="rank-column">Rank</div>
        <div class="safeguard-column">Safeguard</div>
        <div class="metric-column">
            Detection Rate<br/><span class="metric-subtext">Adversarial</span>
            <i class="fas fa-info-circle tooltip-icon" 
               data-tooltip="Measures the safeguard's ability to detect harmful content that uses sophisticated evasion techniques. Higher rates indicate better protection against advanced attacks."></i>
        </div>
        <div class="metric-column">
            Detection Rate<br/><span class="metric-subtext">Non-Adversarial</span>
            <i class="fas fa-info-circle tooltip-icon" 
               data-tooltip="Indicates how effectively the safeguard identifies straightforward harmful content without evasion attempts. Higher rates show better baseline protection."></i>
        </div>
        <div class="metric-column">
            False Positive Rate
            <i class="fas fa-info-circle tooltip-icon" 
               data-tooltip="The rate at which the safeguard incorrectly flags safe content as harmful. Lower rates mean fewer false alarms and better user experience."></i>
        </div>
        <div class="metric-column">
            BELLS Score
            <i class="fas fa-info-circle tooltip-icon" 
               data-tooltip="Our comprehensive metric that balances detection effectiveness with false positive control. Combines multiple factors into a single score - higher is better."></i>
        </div>
    `;
    rankingContainer.appendChild(headerRow);

    // Create ranking items
    sortedData.forEach((item, index) => {
        const bells_score = parseFloat(item.BELLS_score).toFixed(3);
        const detection_adv = parseFloat(item.harmful_jailbreaks).toFixed(3);
        const detection_non_adv = parseFloat(item["harmful_non-adversarial"]).toFixed(3);
        const fpr = parseFloat(item["benign_non-adversarial"]).toFixed(3);
        
        const rankingItem = document.createElement('div');
        rankingItem.className = 'ranking-item';
        rankingItem.innerHTML = `
            <div class="rank-column">
                <div class="rank-badge">#${index + 1}</div>
            </div>
            <div class="safeguard-column">
                <span class="safeguard-name">${item.safeguard}</span>
            </div>
            <div class="metric-column">
                <div class="score ${getScoreClass(detection_adv)} ${Math.abs(detection_adv - bestScores.detection_adv) < 0.001 ? 'best-score' : ''}">${detection_adv}</div>
            </div>
            <div class="metric-column">
                <div class="score ${getScoreClass(detection_non_adv)} ${Math.abs(detection_non_adv - bestScores.detection_non_adv) < 0.001 ? 'best-score' : ''}">${detection_non_adv}</div>
            </div>
            <div class="metric-column">
                <div class="score ${getScoreClass(1 - fpr)} ${Math.abs(fpr - bestScores.fpr) < 0.001 ? 'best-score' : ''}">${fpr}</div>
            </div>
            <div class="metric-column">
                <div class="score ${getScoreClass(bells_score)} ${Math.abs(bells_score - bestScores.bells) < 0.001 ? 'best-score' : ''}">${bells_score}</div>
            </div>
        `;
        rankingContainer.appendChild(rankingItem);
    });
}

function getScoreClass(value) {
    if (value >= 0.9) return 'score-excellent';
    if (value >= 0.7) return 'score-good';
    if (value >= 0.5) return 'score-fair';
    return 'score-poor';
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

function createJailbreakComparison(data) {
    const margin = { top: 60, right: 150, bottom: 100, left: 150 };
    const width = 1000 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    // Define source mappings for drill-down
    const sourceMapping = {
        'Generative': ['jailbreak_source_PAIR'],
        'Narrative': ['jailbreak_source_deep_inception', 'jailbreak_source_deck_of_many_prompts', 'jailbreak_source_huggingface'],
        'Syntactic': [
            'jailbreak_source_base64', 'jailbreak_source_disemvowel', 'jailbreak_source_rot13',
            'jailbreak_source_binary', 'jailbreak_source_hex', 'jailbreak_source_ascii',
            'jailbreak_source_leet', 'jailbreak_source_url_encoded', 'jailbreak_source_uppercase',
            'jailbreak_source_reverse'
        ]
    };

    function createTypeView() {
        const processedData = data.map(d => ({
            safeguard: d.safeguard,
            types: [
                { type: 'Generative', value: Math.min(100, parseFloat(d.jailbreak_type_generative || 0) * 100) },
                { type: 'Narrative', value: Math.min(100, parseFloat(d.jailbreak_type_narrative || 0) * 100) },
                { type: 'Syntactic', value: Math.min(100, parseFloat(d.jailbreak_type_syntactic || 0) * 100) }
            ]
        }));
        createVisualization(processedData, 'type');
    }

    function createSourceView(selectedType) {
        if (selectedType === 'Syntactic') {
            createSyntacticTable(data, sourceMapping.Syntactic);
            return;
        }

        const sources = sourceMapping[selectedType];
        const processedData = data.map(d => ({
            safeguard: d.safeguard,
            types: sources.map(source => ({
                type: source.replace('jailbreak_source_', '').replace(/_/g, ' '),
                value: Math.min(100, parseFloat(d[source] || 0) * 100)
            }))
        }));
        createVisualization(processedData, 'source', selectedType);
    }

    function createSyntacticTable(data, sources) {
        // Clear existing content
        const container = d3.select("#jailbreakPlot").html("");

        // Add back button
        const backButton = container.append("button")
            .attr("class", "back-button")
            .style("margin", "10px")
            .style("padding", "5px 10px")
            .text("← Back")
            .on("click", createTypeView);

        // Create table
        const table = container.append("table")
            .style("width", "100%")
            .style("border-collapse", "collapse")
            .style("margin-top", "20px");

        // Add header
        const header = table.append("thead").append("tr");
        header.append("th")
            .style("padding", "10px")
            .style("border", "1px solid #ddd")
            .style("background-color", "#f8f9fa")
            .text("Safeguard");

        sources.forEach(source => {
            header.append("th")
                .style("padding", "10px")
                .style("border", "1px solid #ddd")
                .style("background-color", "#f8f9fa")
                .text(source.replace('jailbreak_source_', '').replace(/_/g, ' '));
        });

        // Add data rows
        const tbody = table.append("tbody");
        data.forEach(d => {
            const row = tbody.append("tr");
            row.append("td")
                .style("padding", "10px")
                .style("border", "1px solid #ddd")
                .style("font-weight", "bold")
                .text(d.safeguard);

            sources.forEach(source => {
                const value = parseFloat(d[source] || 0) * 100;
                row.append("td")
                    .style("padding", "10px")
                    .style("border", "1px solid #ddd")
                    .style("background-color", value > 0 ? "#e6f3ff" : "white")
                    .text(`${value.toFixed(1)}%`);
            });
        });
    }

    function createVisualization(processedData, viewType, selectedType = null) {
        console.log("Creating visualization with:", {
            viewType,
            selectedType,
            dataLength: processedData.length,
            sampleData: processedData[0]
        });

        // Validate data structure
        if (!processedData || !processedData.length) {
            console.error("No data provided");
            return;
        }

        if (!processedData[0].types || !processedData[0].types.length) {
            console.error("Invalid data structure - missing types array");
            return;
        }

        // Clear existing content
        d3.select("#jailbreakPlot").html("");

        // Adjust margins for source view to accommodate more labels
        const adjustedMargin = viewType === 'source' ? 
            { ...margin, bottom: 160 } : // More space for rotated labels
            margin;

        const svg = d3.select("#jailbreakPlot")
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", `0 0 ${width + adjustedMargin.left + adjustedMargin.right} ${height + adjustedMargin.top + adjustedMargin.bottom}`)
            .attr("preserveAspectRatio", "xMidYMid meet")
            .style("background", "#ffffff")
            .append("g")
            .attr("transform", `translate(${adjustedMargin.left},${adjustedMargin.top})`);

        // Add back button for source view
        if (viewType === 'source') {
            const backButton = svg.append("g")
                .attr("class", "back-button")
                .attr("transform", "translate(-130, -40)")
                .style("cursor", "pointer")
                .on("click", createTypeView);

            backButton.append("rect")
                .attr("width", 80)
                .attr("height", 30)
                .attr("rx", 5)
                .attr("fill", "#e2e8f0");

            backButton.append("text")
                .attr("x", 40)
                .attr("y", 20)
                .attr("text-anchor", "middle")
                .text("← Back");
        }

        // Get unique types for the domain
        const types = processedData[0].types.map(d => d.type);
        console.log("Types for visualization:", types);

        if (types.length === 0) {
            console.error("No types found in data");
            return;
        }

        // Adjust padding based on number of types
        const x0Padding = viewType === 'source' ? 0.2 : 0.1;
        const x1Padding = viewType === 'source' ? 0.1 : 0.05;

        // Scales with adjusted padding
        const x0 = d3.scaleBand()
            .domain(processedData.map(d => d.safeguard))
            .range([0, width])
            .padding(x0Padding);

        const x1 = d3.scaleBand()
            .domain(types)
            .range([0, x0.bandwidth()])
            .padding(x1Padding);

        const y = d3.scaleLinear()
            .domain([0, 100])
            .range([height, 0]);

        // Use a different color scheme for source view with more categories
        const color = d3.scaleOrdinal()
            .domain(types)
            .range(viewType === 'type' ? 
                ['#0567a5', '#4a90e2', '#7cb9e8'] : 
                d3.schemeBlues[Math.max(types.length, 3)]);

        // Add grid lines
        svg.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(y)
                .tickSize(-width)
                .tickFormat("")
                .ticks(5))
            .style("stroke-opacity", 0.1);

        // Add bars
        processedData.forEach(d => {
            const safeguardGroup = svg.append("g")
                .attr("transform", `translate(${x0(d.safeguard)},0)`);

            safeguardGroup.selectAll("rect")
                .data(d.types)
                .enter()
                .append("rect")
                .attr("x", d => x1(d.type))
                .attr("y", d => y(d.value))
                .attr("width", x1.bandwidth())
                .attr("height", d => height - y(d.value))
                .attr("fill", d => color(d.type))
                .attr("rx", 6)
                .attr("ry", 6)
                .style("cursor", viewType === 'type' ? "pointer" : "default")
                .on("click", function(event, d) {
                    if (viewType === 'type') {
                        createSourceView(d.type);
                    }
                });

            // Add value labels
            safeguardGroup.selectAll(".value-label")
                .data(d.types)
                .enter()
                .append("text")
                .attr("class", "value-label")
                .attr("x", d => x1(d.type) + x1.bandwidth()/2)
                .attr("y", d => {
                    const yPos = y(d.value) - 5;
                    return yPos < 0 ? y(d.value) + 15 : yPos;
                })
                .attr("text-anchor", "middle")
                .style("font-size", "12px")
                .style("fill", d => y(d.value) < 15 ? "white" : "black")
                .text(d => `${d.value.toFixed(1)}%`);
        });

        // Adjust x-axis labels for better readability in source view
        svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x0))
            .selectAll("text")
            .attr("transform", `rotate(-45)`)
            .style("text-anchor", "end")
            .style("font-size", viewType === 'source' ? "10px" : "12px");  // Smaller font for source view

        svg.append("g")
            .attr("class", "y-axis")
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickFormat(d => d + "%"));

        // Add title
        const title = viewType === 'type' ? 
            "Jailbreak Detection Rate by Type" : 
            `${selectedType} Jailbreak Sources Detection Rate`;

        svg.append("text")
            .attr("class", "plot-title")
            .attr("x", width/2)
            .attr("y", -adjustedMargin.top/2)
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .style("font-weight", "bold")
            .text(title);

        // Add legend
        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${width + 20}, 0)`);

        processedData[0].types.forEach((type, i) => {
            const legendRow = legend.append("g")
                .attr("transform", `translate(0, ${i * 25})`);
            
            legendRow.append("rect")
                .attr("width", 15)
                .attr("height", 15)
                .attr("fill", color(type.type));
                
            legendRow.append("text")
                .attr("x", 25)
                .attr("y", 12)
                .style("font-size", "12px")
                .text(type.type);
        });
    }

    // Initialize with type view
    createTypeView();
}

// Initialize everything when the document is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log("DOM Content Loaded");
    try {
        const data = await loadData();
        console.log("Data loaded successfully:", data.length, "rows");
        if (data) {
            console.log("Creating visualizations...");
            createRankingList(data);
            createCustomHeatmap(data);
            createFPRComparison(data);
            console.log("About to create jailbreak comparison...");
            createJailbreakComparison(data);
            console.log("All visualizations created");
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

// Also check if the div exists in the HTML
document.addEventListener('DOMContentLoaded', function() {
    const jailbreakPlot = document.getElementById('jailbreakPlot');
    console.log("Jailbreak plot div exists:", !!jailbreakPlot);
}); 