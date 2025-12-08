/**
 * Dark Mode Toggle System
 * Persists theme preference in localStorage
 * Applies theme before page render to prevent flash
 */

(function() {
    'use strict';
    
    // Theme constants
    const THEME_KEY = 'zerocarb-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';
    
    // Get saved theme or default to light
    function getSavedTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === THEME_DARK || saved === THEME_LIGHT) {
            return saved;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_DARK;
        }
        
        return THEME_LIGHT;
    }
    
    // Apply theme immediately (before DOM loads)
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
    }
    
    // Apply saved theme immediately to prevent flash
    applyTheme(getSavedTheme());
    
    // Initialize toggle button when DOM is ready
    function initializeThemeToggle() {
        const currentTheme = getSavedTheme();
        
        // Create toggle button
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.setAttribute('aria-label', 'Toggle dark mode');
        toggle.setAttribute('title', 'Toggle dark mode');
        
        // Update toggle button content
        function updateToggleButton(theme) {
            const icon = theme === THEME_DARK ? '○' : '●';
            const text = theme === THEME_DARK ? 'Light' : 'Dark';
            toggle.innerHTML = `
                <span class="theme-toggle-icon">${icon}</span>
                <span class="theme-toggle-text">${text}</span>
            `;
        }
        
        updateToggleButton(currentTheme);
        
        // Toggle theme on click
        toggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === THEME_DARK ? THEME_LIGHT : THEME_DARK;
            
            applyTheme(newTheme);
            updateToggleButton(newTheme);
            
            // Update charts if they exist
            if (window.updateChartsForTheme) {
                window.updateChartsForTheme(newTheme);
            }
            
            // Dispatch custom event for other components
            window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
        });
        
        // Insert toggle into header
        const headerMeta = document.querySelector('.header-meta');
        if (headerMeta) {
            // Insert before the first child (before status indicators)
            headerMeta.insertBefore(toggle, headerMeta.firstChild);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeThemeToggle);
    } else {
        initializeThemeToggle();
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            const saved = localStorage.getItem(THEME_KEY);
            if (!saved) {
                const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
                applyTheme(newTheme);
                
                // Update toggle button if it exists
                const toggle = document.querySelector('.theme-toggle');
                if (toggle) {
                    const icon = newTheme === THEME_DARK ? '○' : '●';
                    const text = newTheme === THEME_DARK ? 'Light' : 'Dark';
                    toggle.innerHTML = `
                        <span class="theme-toggle-icon">${icon}</span>
                        <span class="theme-toggle-text">${text}</span>
                    `;
                }
            }
        });
    }
    
    // Export theme utilities for other scripts
    window.ThemeManager = {
        getTheme: () => document.documentElement.getAttribute('data-theme'),
        setTheme: applyTheme,
        toggleTheme: () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === THEME_DARK ? THEME_LIGHT : THEME_DARK;
            applyTheme(newTheme);
            return newTheme;
        },
        isDark: () => document.documentElement.getAttribute('data-theme') === THEME_DARK,
        isLight: () => document.documentElement.getAttribute('data-theme') === THEME_LIGHT
    };
    
})();

/**
 * Chart.js Theme Support
 * Updates chart colors when theme changes
 */
window.updateChartsForTheme = function(theme) {
    const isDark = theme === 'dark';
    
    // Chart.js default colors for dark mode
    if (window.Chart) {
        Chart.defaults.color = isDark ? '#a3a3a3' : '#737373';
        Chart.defaults.borderColor = isDark ? '#262626' : '#e5e5e5';
        Chart.defaults.backgroundColor = isDark ? '#1a1a1a' : '#ffffff';
        
        // Update all existing charts
        Object.values(Chart.instances).forEach(chart => {
            if (chart && chart.options) {
                // Update grid colors
                if (chart.options.scales) {
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.grid) {
                            scale.grid.color = isDark ? '#262626' : '#e5e5e5';
                        }
                        if (scale.ticks) {
                            scale.ticks.color = isDark ? '#a3a3a3' : '#737373';
                        }
                    });
                }
                
                // Update legend colors
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels.color = isDark ? '#a3a3a3' : '#737373';
                }
                
                // Update tooltip colors
                if (chart.options.plugins && chart.options.plugins.tooltip) {
                    chart.options.plugins.tooltip.backgroundColor = isDark ? '#1a1a1a' : '#000000';
                    chart.options.plugins.tooltip.titleColor = isDark ? '#ffffff' : '#ffffff';
                    chart.options.plugins.tooltip.bodyColor = isDark ? '#ffffff' : '#ffffff';
                    chart.options.plugins.tooltip.borderColor = isDark ? '#404040' : '#000000';
                }
                
                chart.update();
            }
        });
    }
    
    // D3.js map theme update
    if (window.updateMapTheme) {
        window.updateMapTheme(theme);
    }
};

/**
 * D3.js Map Theme Support
 */
window.updateMapTheme = function(theme) {
    const isDark = theme === 'dark';
    
    // Update map background
    const mapContainer = document.getElementById('world-map-container');
    if (mapContainer) {
        mapContainer.style.background = isDark ? '#1a1a1a' : '#f8f9fa';
    }
    
    // Update map paths
    const svg = d3.select('#world-map');
    if (svg) {
        svg.selectAll('path.country')
            .style('fill', isDark ? '#262626' : '#e5e5e5')
            .style('stroke', isDark ? '#404040' : '#d4d4d4');
        
        svg.selectAll('path.region-marker')
            .style('stroke', isDark ? '#ffffff' : '#000000');
    }
    
    // Update legend
    const legend = document.getElementById('map-legend');
    if (legend) {
        legend.style.background = isDark ? '#1a1a1a' : '#ffffff';
        legend.style.color = isDark ? '#ffffff' : '#000000';
    }
    
    // Update controls
    const controls = document.getElementById('map-controls');
    if (controls) {
        const buttons = controls.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.style.background = isDark ? '#1a1a1a' : '#ffffff';
            btn.style.color = isDark ? '#ffffff' : '#000000';
            btn.style.borderColor = isDark ? '#262626' : '#e5e5e5';
        });
    }
};

// Listen for theme changes
window.addEventListener('themechange', (e) => {
    console.log(`🎨 Theme changed to: ${e.detail.theme}`);
});
