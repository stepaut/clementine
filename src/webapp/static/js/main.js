// Common utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString();
}

function formatTime(time) {
    return new Date(time).toLocaleTimeString();
}

// Chart configuration
const chartConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false
};

// Error handling
function handleError(error) {
    console.error('Error:', error);
    // You can add more sophisticated error handling here
}

// Data fetching utilities
async function fetchData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        handleError(error);
        return null;
    }
} 