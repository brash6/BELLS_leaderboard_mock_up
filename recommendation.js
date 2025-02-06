// Data loading function
async function loadData() {
    const dataFiles = {
        safeguardData: '/data/safeguard_evaluation_results.csv'
    };

    try {
        console.log('Starting data loading...');
        
        const response = await fetch(dataFiles.safeguardData);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvText = await response.text();
        const safeguardData = d3.csvParse(csvText);
        console.log('Successfully loaded safeguard data:', safeguardData);

        return {
            safeguardData: safeguardData
        };
    } catch (error) {
        console.error('Error in loadData:', error);
        throw error;
    }
}

// Recommendation System functionality
function initializeRecommendationSystem() {
    const form = document.getElementById('recommendationForm');
    form.addEventListener('submit', handleRecommendation);
}

function handleRecommendation(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const preferences = {
        systemType: formData.get('systemType'),
        ragEnabled: formData.get('ragEnabled'),
        interactionTypes: formData.getAll('interactionTypes'),
        requestVolume: formData.get('requestVolume'),
        riskLevel: formData.get('riskLevel')
    };
    
    // Generate recommendation based on preferences
    const recommendation = generateRecommendation(preferences);
    displayRecommendation(recommendation);
}

function generateRecommendation(preferences) {
    const safeguards = window.loadedData.safeguardData;
    
    // Define weight factors for different criteria
    const weights = {
        systemCompatibility: 3,
        ragCompatibility: 2,
        performance: {
            Low: 1,
            Medium: 2,
            High: 3
        },
        riskLevel: {
            'Very Low': 1,
            'Low': 2,
            'Medium': 3,
            'High': 4
        },
        interactionTypes: {
            'General chat': 1,
            'Content generation': 1.5,
            'Code generation': 2,
            'Data analysis': 1.5,
            'Expert advice': 2,
            'Customer service': 1
        }
    };

    // Score each safeguard
    const scoredSafeguards = safeguards.map(safeguard => {
        let score = 0;
        let scoreBreakdown = {};

        // System compatibility score
        const systemScore = calculateSystemCompatibilityScore(safeguard, preferences.systemType);
        score += systemScore * weights.systemCompatibility;
        scoreBreakdown.systemCompatibility = systemScore;

        // RAG compatibility score
        const ragScore = calculateRagCompatibilityScore(safeguard, preferences.ragEnabled);
        score += ragScore * weights.ragCompatibility;
        scoreBreakdown.ragCompatibility = ragScore;

        // Performance and risk scores
        const performanceScore = calculatePerformanceScore(safeguard, preferences.requestVolume);
        const riskScore = calculateRiskScore(safeguard, preferences.riskLevel);
        
        score += performanceScore * weights.performance[preferences.requestVolume];
        score += riskScore * weights.riskLevel[preferences.riskLevel];
        
        scoreBreakdown.performance = performanceScore;
        scoreBreakdown.riskLevel = riskScore;

        return {
            safeguard: safeguard.safeguard,
            score: score,
            details: safeguard,
            scoreBreakdown: scoreBreakdown
        };
    });

    // Normalize scores
    const maxScore = Math.max(...scoredSafeguards.map(s => s.score));
    scoredSafeguards.forEach(s => {
        s.normalizedScore = (s.score / maxScore) * 100;
    });

    // Sort by normalized score
    scoredSafeguards.sort((a, b) => b.normalizedScore - a.normalizedScore);

    return {
        topRecommendations: scoredSafeguards.slice(0, 3),
        explanation: generateDetailedExplanation(preferences, scoredSafeguards[0]),
        scoreBreakdown: scoredSafeguards[0].scoreBreakdown
    };
}

// Helper functions for scoring
function calculateSystemCompatibilityScore(safeguard, systemType) {
    if (systemType === 'Black Box API' && safeguard.api_available) return 1;
    if (systemType === 'Direct Access' && safeguard.self_hosted) return 1;
    return 0.3;
}

function calculateRagCompatibilityScore(safeguard, ragEnabled) {
    if (ragEnabled === 'Yes' && safeguard.rag_compatible) return 1;
    if (ragEnabled === 'No') return 1;
    return 0.5;
}

function calculatePerformanceScore(safeguard, requestVolume) {
    const volumeScores = {
        'Low': 1,
        'Medium': safeguard.performance_score,
        'High': safeguard.performance_score * safeguard.performance_score
    };
    return volumeScores[requestVolume];
}

function calculateRiskScore(safeguard, riskLevel) {
    const riskScores = {
        'Very Low': safeguard.BELLS_score,
        'Low': safeguard.BELLS_score * 1.2,
        'Medium': safeguard.BELLS_score * 1.5,
        'High': safeguard.BELLS_score * 2
    };
    return riskScores[riskLevel];
}

function generateDetailedExplanation(preferences, topSafeguard) {
    return `
        <div class="recommendation-explanation">
            <h4>Analysis Based on Your Requirements</h4>
            <div class="requirements-summary">
                <h5>Your Requirements:</h5>
                <ul>
                    <li>System Type: ${preferences.systemType}</li>
                    <li>RAG Integration: ${preferences.ragEnabled}</li>
                    <li>Request Volume: ${preferences.requestVolume}</li>
                    <li>Risk Level: ${preferences.riskLevel}</li>
                    <li>Use Cases: ${preferences.interactionTypes.join(', ')}</li>
                </ul>
            </div>
            <div class="recommendation-rationale">
                <h5>Why ${topSafeguard.safeguard}?</h5>
                <ul>
                    <li>BELLS Score: ${topSafeguard.details.BELLS_score} 
                        (${getScoreQualification(topSafeguard.details.BELLS_score)})</li>
                    <li>Performance Rating: Handles ${preferences.requestVolume} volume efficiently</li>
                    <li>Risk Protection: Suitable for ${preferences.riskLevel} risk environments</li>
                    ${preferences.ragEnabled === 'Yes' ? 
                        `<li>RAG Compatible: Seamless integration with retrieval-augmented generation</li>` : ''}
                </ul>
            </div>
        </div>
    `;
}

function getScoreQualification(score) {
    if (score >= 0.9) return "Excellent";
    if (score >= 0.8) return "Very Good";
    if (score >= 0.7) return "Good";
    if (score >= 0.6) return "Fair";
    return "Basic";
}

function displayRecommendation(recommendation) {
    const resultDiv = document.getElementById('recommendationResult');
    resultDiv.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h4 class="card-title">Recommended Safeguards</h4>
                <div class="row mb-4">
                    ${recommendation.topRecommendations.map((rec, index) => `
                        <div class="col-md-4">
                            <div class="card ${index === 0 ? 'border-primary' : ''}">
                                <div class="card-body">
                                    <h5 class="card-title">
                                        ${index === 0 ? '🏆 ' : ''}${rec.safeguard}
                                    </h5>
                                    <div class="score-details">
                                        <div class="score-item">
                                            <span>BELLS Score:</span>
                                            <strong>${rec.details.BELLS_score}</strong>
                                        </div>
                                        <div class="score-item">
                                            <span>Match Score:</span>
                                            <strong>${rec.normalizedScore.toFixed(1)}%</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="recommendation-details">
                    ${recommendation.explanation}
                </div>
            </div>
        </div>
    `;
}

// Initialize everything when the document is ready
document.addEventListener('DOMContentLoaded', async function() {
    try {
        const data = await loadData();
        window.loadedData = data;
        initializeRecommendationSystem();
    } catch (error) {
        console.error('Initialization error:', error);
        document.querySelector('.dashboard-container').innerHTML = `
            <div class="alert alert-danger">
                <h4>Initialization Error</h4>
                <p>${error.message}</p>
            </div>
        `;
    }
}); 