// Shared JavaScript functionality for all pages

// Store last known price update time
let lastPriceUpdate = null;

// Fetch and update metal prices
function updateMetalPrices(forceRefresh = false) {
    const url = forceRefresh ? '/api/prices?refresh=true' : '/api/prices';
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.prices) {
                // Update gold price
                const goldEl = document.getElementById('goldPrice');
                if (goldEl && data.prices.gold) {
                    goldEl.textContent = '$' + data.prices.gold.toFixed(2);
                }
                
                // Update silver price
                const silverEl = document.getElementById('silverPrice');
                if (silverEl && data.prices.silver) {
                    silverEl.textContent = '$' + data.prices.silver.toFixed(2);
                }
                
                // Calculate and update Goldback rate
                // Formula: (gold_price / 1000) × 2
                const gbRateEl = document.getElementById('goldbackRate');
                if (gbRateEl && data.prices.gold) {
                    const gbRate = (data.prices.gold / 1000.0) * 2.0;
                    // Format with max 2 decimals, trim trailing zeros
                    const formatted = gbRate.toFixed(2).replace(/\.?0+$/, '');
                    gbRateEl.textContent = '$' + formatted;
                }
                
                // Update timestamp in widget header (just time, no "Updated:")
                const timestampEl = document.getElementById('widgetTimestamp');
                if (timestampEl && data.last_updated) {
                    const date = new Date(data.last_updated);
                    timestampEl.textContent = date.toLocaleTimeString();
                    
                    // Check if prices were updated (and this wasn't the first load)
                    if (lastPriceUpdate && data.last_updated !== lastPriceUpdate) {
                        console.log('Prices updated! Reloading page data...');
                        reloadPageData();
                    }
                    
                    lastPriceUpdate = data.last_updated;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching metal prices:', error);
        });
}

// Reload page-specific data without full page refresh
function reloadPageData() {
    // Check which page we're on and reload appropriate data
    const path = window.location.pathname;
    
    if (path === '/' || path === '/dashboard') {
        // Reload dashboard - simplest is to refresh the page
        window.location.reload();
    } else if (path === '/metals') {
        // Reload metals table
        window.location.reload();
    } else if (path === '/coins') {
        // Reload coins table
        window.location.reload();
    } else if (path === '/goldbacks') {
        // Reload goldbacks table
        window.location.reload();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load metal prices
    updateMetalPrices();
    
    // Check for price updates every 10 seconds
    setInterval(updateMetalPrices, 10000);
    
    // Add refresh button handler
    const refreshBtn = document.getElementById('refreshPrices');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Add spinning animation
            this.classList.add('spinning');
            
            // Update prices with force refresh
            updateMetalPrices(true);
            
            // Remove spinning animation after it completes
            setTimeout(() => {
                this.classList.remove('spinning');
            }, 600);
        });
    }
});


// Format number - remove .00 if no decimals needed
function formatNumber(value) {
    const num = parseFloat(value);
    if (num === Math.floor(num)) {
        return num.toString(); // No decimals needed
    }
    return num.toFixed(2); // Show 2 decimals
}
