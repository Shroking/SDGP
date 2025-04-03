document.getElementById('analyze-btn').addEventListener('click', function() {
    const analysisType = document.getElementById('analysis-type').value;

    // Fetch patient data from Flask API
    fetch("/patients")
        .then(response => response.json())
        .then(data => {
            let labels = [];
            let chartData = [];

            if (analysisType === 'trend') {
                labels = data.map((p, index) => `Patient ${index + 1}`);
                chartData = data.map(p => p.oxygen_flow_rate || 0);
            } else if (analysisType === 'bmi') {
                labels = data.map((p, index) => `Patient ${index + 1}`);
                chartData = data.map(p => p.bmi || 0);
            } else if (analysisType === 'co2') {
                labels = data.map((p, index) => `Patient ${index + 1}`);
                chartData = data.map(p => p.end_tidal_co2 || 0);
            }

            // Clear previous chart
            const ctx = document.getElementById('analysis-chart').getContext('2d');
            if (window.chartInstance) {
                window.chartInstance.destroy();
            }

            // Create new chart
            window.chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: analysisType === 'trend' ? 'Oxygen Flow Rate' : analysisType === 'bmi' ? 'BMI' : 'End Tidal CO2',
                        data: chartData,
                        backgroundColor: '#007bff',
                        borderColor: '#0056b3',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => console.error("Error fetching patient data:", error));
});

