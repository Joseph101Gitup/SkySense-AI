/**
 * SKYsense AI - Chart.js Initializers and Visualizers
 * Precision Meteorological Visualizations with Dark Theme Palette
 */

// Global Chart.js dark-mode defaults
if (window.Chart) {
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.font.family = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

/**
 * 1. Category Distribution Doughnut Chart
 */
function renderDistributionDonut(canvasId, lowCount, medCount, noCount) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Check if all counts are 0
    const total = lowCount + medCount + noCount;
    if (total === 0) {
        return;
    }

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low to Medium Rain', 'Medium to Heavy Rain', 'No to Low Rain'],
            datasets: [{
                data: [lowCount, medCount, noCount],
                backgroundColor: [
                    '#F59E0B', // Amber-500
                    '#F43F5E', // Rose-500
                    '#10B981', // Emerald-500
                ],
                borderColor: '#0F172A',
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#CBD5E1',
                        font: { size: 11, weight: '500' },
                        padding: 14,
                        boxWidth: 12,
                        boxHeight: 12,
                        borderRadius: 3,
                        useBorderRadius: true
                    }
                },
                tooltip: {
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#F8FAFC',
                    bodyColor: '#CBD5E1',
                    padding: 10,
                    callbacks: {
                        label: (context) => {
                            const val = context.raw || 0;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${val} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * 2. Predictions Over Time (Activity Timeline Line/Area Chart)
 */
function renderTimelineChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Create subtle gradient fill
    const canvas = ctx.getContext ? ctx.getContext('2d') : null;
    let gradient = 'rgba(14, 165, 233, 0.15)';
    if (canvas) {
        gradient = canvas.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(14, 165, 233, 0.35)');
        gradient.addColorStop(1, 'rgba(14, 165, 233, 0.00)');
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cloud Inferences',
                data: data,
                borderColor: '#38BDF8',
                backgroundColor: gradient,
                borderWidth: 2.5,
                tension: 0.35,
                fill: true,
                pointBackgroundColor: '#0284C7',
                pointBorderColor: '#38BDF8',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#38BDF8',
                pointHoverBorderColor: '#FFFFFF',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0F172A',
                    borderColor: '#38BDF8',
                    borderWidth: 1,
                    titleColor: '#F8FAFC',
                    bodyColor: '#38BDF8',
                    callbacks: {
                        label: (context) => ` ${context.raw} analyses recorded`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(51, 65, 85, 0.2)' },
                    ticks: {
                        color: '#94A3B8',
                        font: { size: 11 }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(51, 65, 85, 0.2)' },
                    ticks: {
                        color: '#94A3B8',
                        precision: 0,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

/**
 * 3. Confidence Distribution Histogram (Bar Chart)
 */
function renderConfidenceHistogram(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Analyses Count',
                data: data,
                backgroundColor: [
                    'rgba(244, 63, 94, 0.75)',   // <50% (Rose)
                    'rgba(245, 158, 11, 0.75)',  // 50-60% (Amber)
                    'rgba(56, 189, 248, 0.75)',  // 60-70% (Sky)
                    'rgba(99, 102, 241, 0.75)',  // 70-85% (Indigo)
                    'rgba(16, 185, 129, 0.75)'   // 85-100% (Emerald)
                ],
                borderColor: [
                    '#F43F5E',
                    '#F59E0B',
                    '#38BDF8',
                    '#6366F1',
                    '#10B981'
                ],
                borderWidth: 1.5,
                borderRadius: 6,
                maxBarThickness: 36
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0F172A',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#F8FAFC',
                    bodyColor: '#CBD5E1',
                    callbacks: {
                        title: (items) => `Confidence Bracket: ${items[0].label}`,
                        label: (context) => ` ${context.raw} records`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#94A3B8',
                        font: { size: 11 }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(51, 65, 85, 0.2)' },
                    ticks: {
                        color: '#94A3B8',
                        precision: 0,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

/**
 * 4. Result Page Horizontal Probability Vector
 */
function renderProbabilityBarChart(canvasId, lowProb, medProb, noProb) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Low to Medium Rain', 'Medium to Heavy Rain', 'No to Low Rain'],
            datasets: [{
                label: 'Softmax Probability (%)',
                data: [lowProb, medProb, noProb],
                backgroundColor: [
                    'rgba(245, 158, 11, 0.85)',
                    'rgba(244, 63, 94, 0.85)',
                    'rgba(16, 185, 129, 0.85)'
                ],
                borderColor: [
                    '#F59E0B',
                    '#F43F5E',
                    '#10B981'
                ],
                borderWidth: 1.5,
                borderRadius: 8,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => ` ${context.raw}% Probability`
                    }
                }
            },
            scales: {
                x: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: {
                        color: '#94A3B8',
                        callback: (value) => value + '%'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: '#CBD5E1',
                        font: { family: 'Outfit', size: 12, weight: '500' }
                    }
                }
            }
        }
    });
}
