/*
 * script.js
 *
 * This file contains the client‑side logic for the Daily Beat Activity Report
 * application.  It handles dynamic table row creation for the reports section,
 * collects all form values into a JSON object, and submits the data to the
 * backend endpoint for PDF generation.  The returned PDF is opened in a
 * new browser tab.
 */

document.addEventListener('DOMContentLoaded', () => {
    const reportsTableBody = document.getElementById('reportsBody');
    const addReportRowButton = document.getElementById('addReportRow');
    const generatePdfButton = document.getElementById('generatePdf');

    // Adds a new row to the Reports Generated table.
    function addReportRow() {
        const row = document.createElement('tr');

        // RMS number cell
        const rmsCell = document.createElement('td');
        const rmsInput = document.createElement('input');
        rmsInput.type = 'text';
        rmsInput.classList.add('rms-number');
        rmsInput.placeholder = 'Report #';
        rmsCell.appendChild(rmsInput);
        row.appendChild(rmsCell);

        // Submitted cell (checkbox)
        const submittedCell = document.createElement('td');
        const submittedInput = document.createElement('input');
        submittedInput.type = 'checkbox';
        submittedInput.classList.add('report-submitted');
        submittedCell.appendChild(submittedInput);
        row.appendChild(submittedCell);

        // Description cell
        const descCell = document.createElement('td');
        const descInput = document.createElement('input');
        descInput.type = 'text';
        descInput.classList.add('report-description');
        descInput.placeholder = 'Brief description of the report';
        descCell.appendChild(descInput);
        row.appendChild(descCell);

        // Action cell with remove button
        const actionCell = document.createElement('td');
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.textContent = 'Remove';
        removeButton.classList.add('small-button');
        removeButton.addEventListener('click', () => {
            row.remove();
        });
        actionCell.appendChild(removeButton);
        row.appendChild(actionCell);

        reportsTableBody.appendChild(row);
    }

    // Add initial blank row on page load
    addReportRow();

    // When the Add Report button is clicked, append a new row
    addReportRowButton.addEventListener('click', addReportRow);

    // Collects all input values and sends them to the backend to generate a PDF.
    async function generatePdf() {
        // Gather simple form fields
        const data = {
            location: document.getElementById('location').value,
            officerName: document.getElementById('officerName').value,
            badgeNumber: document.getElementById('badgeNumber').value,
            keySet: document.getElementById('keySet').value,
            reportDate: document.getElementById('reportDate').value,
            radioNumber: document.getElementById('radioNumber').value,
            patrols: document.getElementById('patrols').value,
            oicName: document.getElementById('oicName').value,
            dispatchers: document.getElementById('dispatchers').value,

            // Post Specific / Completion Times
            inventoryComplete: document.getElementById('inventoryComplete').value,
            hhsLockUp: document.getElementById('hhsLockUp').value,
            basement: document.getElementById('basement').value,
            roof: document.getElementById('roof').value,
            upperLevels: document.getElementById('upperLevels').value,
            midLevels: document.getElementById('midLevels').value,
            lowerLevels: document.getElementById('lowerLevels').value,
            parkingLots: document.getElementById('parkingLots').value,
            alarms: document.getElementById('alarms').value,
            specialAssignments: document.getElementById('specialAssignments').value,
            otherTasks: document.getElementById('otherTasks').value,

            // Vehicle Inspection fields
            beginningMileage: document.getElementById('beginningMileage').value,
            endingMileage: document.getElementById('endingMileage').value,
            exteriorDamage: document.getElementById('exteriorDamage').value,
            interiorDamage: document.getElementById('interiorDamage').value,
            fluidLevels: document.getElementById('fluidLevels').value,
            tireCondition: document.getElementById('tireCondition').value,
            vehicleOther: document.getElementById('vehicleOther').value,

            // Notes and signature
            notes: document.getElementById('notes').value,
            receivedBy: document.getElementById('receivedBy').value,
            signatureDate: document.getElementById('signatureDate').value,

            // Placeholder arrays to be filled below
            reports: [],
            vehicles: []
        };

        // Collect Reports Generated rows
        const reportRows = reportsTableBody.querySelectorAll('tr');
        reportRows.forEach(row => {
            const rms = row.querySelector('.rms-number').value;
            const submitted = row.querySelector('.report-submitted').checked;
            const description = row.querySelector('.report-description').value;
            // Only include the row if it has at least one field filled in
            if (rms || description) {
                data.reports.push({
                    rms,
                    submitted,
                    description
                });
            }
        });

        // Collect Vehicle Report Card data for four cards
        for (let i = 1; i <= 4; i++) {
            // Determine pass/fail selection
            const statusInputs = document.getElementsByName(`vehicle${i}Status`);
            let status = 'Pass';
            for (const input of statusInputs) {
                if (input.checked) {
                    status = input.value;
                    break;
                }
            }
            data.vehicles.push({
                index: i,
                status: status,
                make: document.getElementById(`vehicle${i}Make`).value,
                time: document.getElementById(`vehicle${i}Time`).value,
                lic: document.getElementById(`vehicle${i}Lic`).value,
                reason: document.getElementById(`vehicle${i}Reason`).value,
                ow: document.getElementById(`vehicle${i}OW`).value,
                loc: document.getElementById(`vehicle${i}Loc`).value
            });
        }

        try {
            // Use a relative URL so that the request is sent to the same host/port
            // that served the page.  This avoids cross‑origin issues when the
            // frontend is served by the Python backend.
            const response = await fetch('generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            const blob = await response.blob();
            // Create a URL for the PDF blob and open it in a new tab
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (error) {
            alert('Error generating PDF: ' + error.message);
        }
    }

    // Attach click handler for PDF generation
    generatePdfButton.addEventListener('click', generatePdf);
});