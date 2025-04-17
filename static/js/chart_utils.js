/**
 * C-Recenzione - Chart Utilities
 * Manages chart creation and updates for the reports page
 */

/**
 * Initialize the reports page charts
 * @param {Object} data - Data for the charts
 */
function initializeCharts(data) {
    // Create the main status chart
    createStatusChart(data.stats);
    
    // Create category charts
    createCategoryCharts(data.category_stats);
}

/**
 * Create main status chart showing request statistics
 * @param {Object} stats - Statistics data
 */
function createStatusChart(stats) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    // Create chart
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Consegnati', 'Aperti', 'Risposti'],
            datasets: [{
                data: [stats.delivered, stats.opened, stats.responded],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.formattedValue || '';
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((context.raw / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Create rates chart
    const ratesCtx = document.getElementById('ratesChart').getContext('2d');
    new Chart(ratesCtx, {
        type: 'bar',
        data: {
            labels: ['% Consegna', '% Apertura', '% Risposta'],
            datasets: [{
                label: 'Percentuale',
                data: [
                    stats.delivery_rate, 
                    stats.open_rate, 
                    stats.response_rate
                ],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.formattedValue}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create category comparison charts
 * @param {Object} categoryStats - Statistics by category
 */
function createCategoryCharts(categoryStats) {
    const categories = Object.keys(categoryStats);
    
    if (categories.length === 0) {
        document.getElementById('categoryChartsContainer').innerHTML = 
            '<div class="alert alert-info">Nessun dato disponibile per categorie.</div>';
        return;
    }
    
    // Prepare data for the chart
    const totalData = [];
    const deliveredData = [];
    const openedData = [];
    const respondedData = [];
    
    categories.forEach(category => {
        const stats = categoryStats[category];
        totalData.push(stats.total);
        deliveredData.push(stats.delivered);
        openedData.push(stats.opened);
        respondedData.push(stats.responded);
    });
    
    // Create category comparison chart
    const ctx = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Totale',
                    data: totalData,
                    backgroundColor: 'rgba(201, 203, 207, 0.5)',
                    borderColor: 'rgba(201, 203, 207, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Consegnati',
                    data: deliveredData,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Aperti',
                    data: openedData,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Risposti',
                    data: respondedData,
                    backgroundColor: 'rgba(153, 102, 255, 0.5)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Categoria'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Numero di richieste'
                    }
                }
            }
        }
    });
    
    // Create category performance chart (response rates by category)
    const performanceCtx = document.getElementById('categoryPerformanceChart').getContext('2d');
    
    // Calculate response rates for each category
    const responseRates = categories.map(category => {
        const stats = categoryStats[category];
        const openRate = stats.delivered > 0 ? (stats.opened / stats.delivered) * 100 : 0;
        const responseRate = stats.opened > 0 ? (stats.responded / stats.opened) * 100 : 0;
        return {
            category,
            openRate: parseFloat(openRate.toFixed(1)),
            responseRate: parseFloat(responseRate.toFixed(1))
        };
    });
    
    new Chart(performanceCtx, {
        type: 'radar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Tasso di apertura (%)',
                    data: responseRates.map(r => r.openRate),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                },
                {
                    label: 'Tasso di risposta (%)',
                    data: responseRates.map(r => r.responseRate),
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    pointBackgroundColor: 'rgba(153, 102, 255, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(153, 102, 255, 1)'
                }
            ]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });
}

/**
 * Update charts with new data
 * @param {Object} newData - Updated data for the charts
 */
function updateCharts(newData) {
    // Clear existing charts
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        container.innerHTML = '';
        
        // Recreate canvas elements
        const canvas = document.createElement('canvas');
        canvas.id = container.dataset.chartId;
        container.appendChild(canvas);
    });
    
    // Reinitialize charts with new data
    initializeCharts(newData);
}
