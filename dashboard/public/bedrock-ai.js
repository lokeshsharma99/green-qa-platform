/**
 * ZeroCarb - Amazon Bedrock AI Integration
 * Provides AI-powered carbon insights and recommendations
 */

// ============================================
// Bedrock Configuration
// ============================================

const BEDROCK_CONFIG = {
    // Bedrock API token (base64 encoded signed URL)
    apiToken: null,
    region: 'eu-west-2',
    model: 'anthropic.claude-3-sonnet-20240229-v1:0',
    maxTokens: 500,
    enabled: false
};

// ============================================
// AI State
// ============================================

const aiState = {
    isLoading: false,
    lastInsight: null,
    conversationHistory: [],
    autoInsightInterval: null
};

// ============================================
// Initialize Bedrock AI
// ============================================

function initBedrockAI(apiToken) {
    if (!apiToken) {
        console.log('ℹ️ Bedrock AI: No API token provided, AI features disabled');
        return false;
    }
    
    BEDROCK_CONFIG.apiToken = apiToken;
    BEDROCK_CONFIG.enabled = true;
    
    console.log('✅ Bedrock AI: Initialized successfully');
    
    // Generate initial insight
    generateAutoInsight();
    
    // Set up periodic insights (every 5 minutes)
    aiState.autoInsightInterval = setInterval(generateAutoInsight, 5 * 60 * 1000);
    
    return true;
}

// ============================================
// Build Context for AI
// ============================================

function buildCarbonContext() {
    const regions = typeof state !== 'undefined' ? state.regions : {};
    const regionData = Object.entries(regions).map(([id, data]) => ({
        region: id,
        location: data.location || AWS_REGIONS[id]?.location || id,
        intensity: data.intensity,
        index: data.index || getIntensityIndex(data.intensity),
        source: data.source
    }));
    
    // Sort by intensity
    regionData.sort((a, b) => a.intensity - b.intensity);
    
    const optimalRegion = regionData[0];
    const worstRegion = regionData[regionData.length - 1];
    
    // Get current selection
    const selectedRegion = document.getElementById('comparison-region-select')?.value || 'eu-west-2';
    const selectedData = regions[selectedRegion] || {};
    
    // Get pipeline history summary
    const history = typeof state !== 'undefined' ? state.pipelineHistory : [];
    const recentRuns = history.slice(0, 10);
    const totalSavings = recentRuns.reduce((sum, r) => sum + (r.savings_g || 0), 0);
    
    return {
        timestamp: new Date().toISOString(),
        regions: regionData,
        optimal: optimalRegion,
        worst: worstRegion,
        selected: {
            region: selectedRegion,
            intensity: selectedData.intensity || 'unknown',
            location: AWS_REGIONS[selectedRegion]?.location || selectedRegion
        },
        recentActivity: {
            totalRuns: recentRuns.length,
            totalSavingsG: totalSavings.toFixed(2),
            avgIntensity: recentRuns.length > 0 
                ? (recentRuns.reduce((sum, r) => sum + (r.carbon_intensity || r.intensity || 0), 0) / recentRuns.length).toFixed(1)
                : 'N/A'
        },
        thresholds: {
            veryLow: '≤25 gCO₂/kWh',
            low: '≤75 gCO₂/kWh',
            moderate: '≤150 gCO₂/kWh',
            high: '>150 gCO₂/kWh'
        }
    };
}

// ============================================
// Call Bedrock API
// ============================================

async function callBedrockAPI(prompt, systemPrompt = null) {
    if (!BEDROCK_CONFIG.enabled || !BEDROCK_CONFIG.apiToken) {
        throw new Error('Bedrock AI not initialized');
    }
    
    aiState.isLoading = true;
    updateAILoadingState(true);
    
    try {
        // Decode the API token to get the signed URL
        const signedUrl = atob(BEDROCK_CONFIG.apiToken.replace('bedrock-api-key-', ''));
        
        const requestBody = {
            anthropic_version: "bedrock-2023-05-31",
            max_tokens: BEDROCK_CONFIG.maxTokens,
            messages: [
                {
                    role: "user",
                    content: prompt
                }
            ]
        };
        
        if (systemPrompt) {
            requestBody.system = systemPrompt;
        }
        
        const response = await fetch(signedUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Bedrock API error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        
        // Extract text from Claude response
        const aiResponse = data.content?.[0]?.text || data.completion || 'No response generated';
        
        aiState.lastInsight = {
            response: aiResponse,
            timestamp: new Date().toISOString()
        };
        
        return aiResponse;
        
    } catch (error) {
        console.error('❌ Bedrock API error:', error);
        throw error;
    } finally {
        aiState.isLoading = false;
        updateAILoadingState(false);
    }
}

// ============================================
// Generate Insights
// ============================================

async function generateAutoInsight() {
    if (!BEDROCK_CONFIG.enabled) return;
    
    const context = buildCarbonContext();
    
    const systemPrompt = `You are a carbon sustainability expert for the ZeroCarb platform, helping Defra GDS teams reduce their cloud computing carbon footprint. 
Be concise, friendly, and actionable. Use simple language. 
Focus on practical recommendations based on the current data.
Keep responses under 100 words.`;
    
    const prompt = `Based on the current carbon intensity data across AWS regions, provide a brief insight or recommendation.

Current Data:
- Optimal region: ${context.optimal?.region} (${context.optimal?.location}) at ${context.optimal?.intensity} gCO₂/kWh
- Worst region: ${context.worst?.region} (${context.worst?.location}) at ${context.worst?.intensity} gCO₂/kWh
- User's selected region: ${context.selected.region} (${context.selected.location}) at ${context.selected.intensity} gCO₂/kWh
- Recent pipeline runs: ${context.recentActivity.totalRuns}
- Total carbon saved: ${context.recentActivity.totalSavingsG}g CO₂

Provide ONE actionable insight about:
1. Whether the user should consider switching regions, OR
2. The best time to run workloads, OR
3. A congratulation if they're already using an optimal region

Start with an emoji. Be encouraging.`;

    try {
        const insight = await callBedrockAPI(prompt, systemPrompt);
        displayAIInsight(insight, 'auto');
    } catch (error) {
        displayAIError('Unable to generate insight. AI service may be temporarily unavailable.');
    }
}

async function askAIQuestion(question) {
    if (!BEDROCK_CONFIG.enabled) {
        displayAIError('AI features are not enabled. Please configure the Bedrock API token.');
        return;
    }
    
    if (!question || question.trim().length === 0) {
        return;
    }
    
    const context = buildCarbonContext();
    
    const systemPrompt = `You are a carbon sustainability expert for the ZeroCarb platform at Defra GDS.
You help teams understand and reduce their cloud computing carbon footprint.
Be concise, helpful, and use simple language.
Base your answers on the provided real-time data.
If asked about something outside carbon/sustainability, politely redirect to relevant topics.
Keep responses under 150 words.`;

    const prompt = `Current Carbon Data:
${JSON.stringify(context, null, 2)}

User Question: ${question}

Provide a helpful, accurate response based on the data above.`;

    try {
        // Add to conversation history
        aiState.conversationHistory.push({ role: 'user', content: question });
        
        const response = await callBedrockAPI(prompt, systemPrompt);
        
        aiState.conversationHistory.push({ role: 'assistant', content: response });
        
        displayAIResponse(question, response);
        
    } catch (error) {
        displayAIError('Sorry, I couldn\'t process your question. Please try again.');
    }
}

// ============================================
// Explain Scheduling Decision
// ============================================

async function explainSchedulingDecision(decision, currentIntensity, optimalIntensity, optimalTime) {
    if (!BEDROCK_CONFIG.enabled) return null;
    
    const systemPrompt = `You are explaining carbon-aware scheduling decisions to developers.
Be brief and clear. Use simple language. One short paragraph max.`;

    const prompt = `Explain this scheduling recommendation in simple terms:
- Decision: ${decision}
- Current carbon intensity: ${currentIntensity} gCO₂/kWh
- Optimal intensity: ${optimalIntensity} gCO₂/kWh
- Optimal time: ${optimalTime || 'Now'}

Why is this the recommendation? What's happening with the electricity grid?`;

    try {
        return await callBedrockAPI(prompt, systemPrompt);
    } catch (error) {
        return null;
    }
}

// ============================================
// Generate Impact Narrative
// ============================================

async function generateImpactNarrative(savedCO2g, equivalentKm, equivalentTrees) {
    if (!BEDROCK_CONFIG.enabled) return null;
    
    const systemPrompt = `You create engaging, brief narratives about environmental impact.
Make the numbers relatable and meaningful. Be positive and encouraging.
One or two sentences only.`;

    const prompt = `Create a brief, engaging narrative for this carbon savings:
- CO₂ saved: ${savedCO2g}g
- Equivalent to driving: ${equivalentKm} km
- Trees needed to absorb: ${equivalentTrees}

Make it personal and meaningful for a developer at Defra.`;

    try {
        return await callBedrockAPI(prompt, systemPrompt);
    } catch (error) {
        return null;
    }
}

// ============================================
// UI Functions
// ============================================

function updateAILoadingState(isLoading) {
    const loadingIndicator = document.getElementById('ai-loading');
    const insightContent = document.getElementById('ai-insight-content');
    
    if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? 'flex' : 'none';
    }
    if (insightContent) {
        insightContent.style.opacity = isLoading ? '0.5' : '1';
    }
}

function displayAIInsight(insight, type = 'auto') {
    const container = document.getElementById('ai-insight-text');
    if (!container) return;
    
    container.innerHTML = insight;
    container.className = `ai-insight-text ${type}`;
    
    // Update timestamp
    const timestamp = document.getElementById('ai-insight-timestamp');
    if (timestamp) {
        timestamp.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }
}

function displayAIResponse(question, response) {
    const chatContainer = document.getElementById('ai-chat-messages');
    if (!chatContainer) return;
    
    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'ai-chat-message user';
    userMsg.innerHTML = `<span class="message-content">${escapeHtml(question)}</span>`;
    chatContainer.appendChild(userMsg);
    
    // Add AI response
    const aiMsg = document.createElement('div');
    aiMsg.className = 'ai-chat-message assistant';
    aiMsg.innerHTML = `<span class="message-content">${response}</span>`;
    chatContainer.appendChild(aiMsg);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Clear input
    const input = document.getElementById('ai-question-input');
    if (input) input.value = '';
}

function displayAIError(message) {
    const container = document.getElementById('ai-insight-text');
    if (container) {
        container.innerHTML = `<span class="ai-error">⚠️ ${message}</span>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Event Handlers
// ============================================

function handleAIQuestionSubmit(event) {
    if (event) event.preventDefault();
    
    const input = document.getElementById('ai-question-input');
    if (!input) return;
    
    const question = input.value.trim();
    if (question) {
        askAIQuestion(question);
    }
}

function handleAIQuestionKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleAIQuestionSubmit();
    }
}

// Quick question buttons
function askQuickQuestion(questionType) {
    const questions = {
        'best-region': 'Which region should I use right now for the lowest carbon footprint?',
        'best-time': 'When is the best time to run my pipeline today?',
        'explain-savings': 'Can you explain my carbon savings this month?',
        'compare-regions': 'How do eu-west-2 and eu-north-1 compare right now?'
    };
    
    const question = questions[questionType];
    if (question) {
        const input = document.getElementById('ai-question-input');
        if (input) input.value = question;
        askAIQuestion(question);
    }
}

// ============================================
// Export for global access
// ============================================

window.BedrockAI = {
    init: initBedrockAI,
    askQuestion: askAIQuestion,
    generateInsight: generateAutoInsight,
    explainDecision: explainSchedulingDecision,
    generateImpactNarrative: generateImpactNarrative,
    isEnabled: () => BEDROCK_CONFIG.enabled,
    handleSubmit: handleAIQuestionSubmit,
    askQuick: askQuickQuestion
};
