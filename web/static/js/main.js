// List of US states
const states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
];

// Populate state dropdown
document.addEventListener('DOMContentLoaded', function() {
    const stateSelect = document.getElementById('state');
    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        stateSelect.appendChild(option);
    });
});

// Handle form submission
document.getElementById('rateLookupForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const state = document.getElementById('state').value;
    const procedureCode = document.getElementById('procedureCode').value;
    
    if (!state || !procedureCode) {
        alert('Please select a state and enter a procedure code');
        return;
    }
    
    // Show loading state
    const resultsBody = document.getElementById('resultsBody');
    resultsBody.innerHTML = '<tr><td colspan="3" class="loading"></td></tr>';
    
    try {
        const response = await fetch(`/api/rates/${state}/${procedureCode}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Clear and populate results
        resultsBody.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.provider || 'N/A'}</td>
                <td>$${item.rate?.toFixed(2) || 'N/A'}</td>
                <td>${item.date || 'N/A'}</td>
            `;
            resultsBody.appendChild(row);
        });
        
        if (data.length === 0) {
            resultsBody.innerHTML = '<tr><td colspan="3">No results found</td></tr>';
        }
    } catch (error) {
        resultsBody.innerHTML = `<tr><td colspan="3" class="text-danger">Error: ${error.message}</td></tr>`;
    }
}); 