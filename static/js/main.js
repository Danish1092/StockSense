function loadBundle(bundleId) {
    fetch(`http://localhost:5000/bundle/${bundleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Bundle not found');
                return;
            }
            displayBundle(data);
        })
        .catch(error => console.error('Error:', error));
}

function displayBundle(bundle) {
    const contentDiv = document.getElementById('bundle-content');
    let html = `
        <h2 class="text-2xl font-bold mb-4">${bundle.title}</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    `;
    
    bundle.stocks.forEach(stock => {
        html += `
            <div class="glass-card p-4">
                <h3 class="text-lg font-bold">${stock.name}</h3>
                <p class="text-gray-400">${stock.symbol}</p>
                <p class="text-xl mt-2">₹${stock.price}</p>
            </div>
        `;
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
}
