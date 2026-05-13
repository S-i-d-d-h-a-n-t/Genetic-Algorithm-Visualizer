// static/script.js
document.addEventListener('DOMContentLoaded', function () {
    const startButton = document.getElementById('startButton');
    const statusElement = document.getElementById('status');
    let makespanChart;
    let ganttChart;
    let eventSource;

    // --- Initialize Charts ---
    // 1. Line Chart for Makespan
    const ctx = document.getElementById('makespanChart').getContext('2d');
    makespanChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Minimum Makespan',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            animation: {
                duration: 200 // Faster animation
            }
        }
    });

    // 2. Google Gantt Chart
    google.charts.load('current', {'packages':['gantt']});
    google.charts.setOnLoadCallback(() => {
        ganttChart = new google.visualization.Gantt(document.getElementById('ganttChart'));
    });

    // --- Event Listener for the Start Button ---
    startButton.addEventListener('click', () => {
        if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
            eventSource.close();
        }

        // Reset charts and status
        makespanChart.data.labels = [];
        makespanChart.data.datasets[0].data = [];
        makespanChart.update();
        statusElement.textContent = "Status: Running...";

        // Connect to the Flask event stream
        eventSource = new EventSource('/run-ga');

        eventSource.onmessage = function (event) {
            const data = JSON.parse(event.data);

            // Update line chart with every message
            makespanChart.data.labels.push(data.generation);
            makespanChart.data.datasets[0].data.push(data.minMakespan);
            makespanChart.update();

            // Update Gantt chart only when data is available
            if (data.ganttData) {
                drawGanttChart(data.ganttData);
                statusElement.textContent = `Status: Generation ${data.generation}, Best Makespan: ${data.minMakespan}`;
            }
        };

        eventSource.onerror = function () {
            statusElement.textContent = "Status: Finished or Error.";
            eventSource.close();
        };
    });


    // --- Function to Draw Gantt Chart ---
    function drawGanttChart(ganttData) {
        if (!google.visualization || !ganttChart || !ganttData) {
            console.error("Google Charts not ready or no data provided.");
            return;
        }

        const dataTable = new google.visualization.DataTable();

        // Define all the columns the Gantt chart expects
        dataTable.addColumn('string', 'Task ID');
        dataTable.addColumn('string', 'Task Name');
        dataTable.addColumn('string', 'Resource'); // This column is what groups tasks on the Y-axis
        dataTable.addColumn('date', 'Start Date');
        dataTable.addColumn('date', 'End Date');
        dataTable.addColumn('number', 'Duration');
        dataTable.addColumn('number', 'Percent Complete');
        dataTable.addColumn('string', 'Dependencies');
        // This is the special "style" column that allows custom colors
        dataTable.addColumn({ type: 'string', role: 'style' });

        // The Python data now sends 9 items per task, which we map to the columns
        const rows = ganttData.map(row => [
            row[0],             // Task ID (e.g., "Machine 1")
            row[1],             // Task Name (e.g., "(2,1,2)")
            row[0],             // Resource (also "Machine 1" to group by machine)
            new Date(row[3]),   // Start Date
            new Date(row[4]),   // End Date
            row[5],             // Duration
            row[6],             // Percent Complete
            row[7],             // Dependencies
            row[8]              // The Style string (e.g., "fill-color: #4285F4")
        ]);

        dataTable.addRows(rows);

        const options = {
            height: 450,
            gantt: {
                trackHeight: 30,
                // We tell the chart to color the bars based on the 'style' role column
                barCornerRadius: 2,
                barStyle: {
                    stroke: '#000',
                    strokeWidth: 1
                }
            }
        };

        ganttChart.draw(dataTable, options);
    }
});