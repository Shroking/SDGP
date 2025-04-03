document.addEventListener("DOMContentLoaded", function () {
    fetch("/patients") // Fetch patient data from Flask API
        .then(response => response.json())
        .then(data => processData(data))
        .catch(error => console.error("Error fetching patient data:", error));
});

function processData(patientData) {
    const tableBody = document.querySelector("#all-patients tbody");
    const noDataList = document.querySelector("#patients-without-data ul");
    let totalCO2 = 0, totalFeed = 0, totalOxygen = 0, totalBMI = 0, count = 0;

    patientData.forEach(patient => {
        if (!patient.end_tidal_co2 || !patient.feed_vol || !patient.oxygen_flow_rate || !patient.bmi) {
            const li = document.createElement("li");
            li.textContent = `Patient ID: ${patient.encounterId}`;
            noDataList.appendChild(li);
            return;
        }
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${patient.encounterId}</td>
            <td>${patient.end_tidal_co2.toFixed(2)}</td>
            <td>${patient.feed_vol.toFixed(2)}</td>
            <td>${patient.oxygen_flow_rate.toFixed(2)}</td>
            <td>${patient.bmi.toFixed(2)}</td>
            <td>${patient.referral === 1 ? "✔" : "✘"}</td>
        `;
        tableBody.appendChild(row);

        // Calculate averages
        totalCO2 += patient.end_tidal_co2;
        totalFeed += patient.feed_vol;
        totalOxygen += patient.oxygen_flow_rate;
        totalBMI += patient.bmi;
        count++;
    });

    // Display average values
    if (count > 0) {
        document.getElementById("avg-co2").textContent = (totalCO2 / count).toFixed(2);
        document.getElementById("avg-feed").textContent = (totalFeed / count).toFixed(2);
        document.getElementById("avg-oxygen").textContent = (totalOxygen / count).toFixed(2);
        document.getElementById("avg-bmi").textContent = (totalBMI / count).toFixed(2);
    }

    // Fetch referred patients and display separately
    fetch("/patients/referred")
        .then(response => response.json())
        .then(data => {
            const referredTableBody = document.querySelector("#referred-patients tbody");
            referredTableBody.innerHTML = "";
            data.forEach(patient => {
                const row = `<tr>
                    <td>${patient.encounterId}</td>
                    <td>${patient.bmi || 'N/A'}</td>
                    <td>${patient.oxygen_flow_rate || 'N/A'}</td>
                    <td>${patient.feed_vol || 'N/A'}</td>
                    
                    <td>
                        ${patient.referral
                             ? "✅ Needs Dietitian"
                             : patient.watch_flag
                              ? "⚠️ Watch Closely"
                              : "-"}
                    </td>

                </tr>`;
                referredTableBody.innerHTML += row;
            });
        })
        .catch(error => console.error("Error fetching referred patients:", error));
}