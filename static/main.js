    // Fetches the list of files from the server and populates the dropdown
function populateDropdown() {
        fetch('/get_files')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(files => {
            const dropdown = document.getElementById('fileDropdown');
            files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.text = file;
                dropdown.add(option);
            });
        })
        .catch(error => {
            console.log('There was a problem with the fetch operation:', error.message);
        });
    }

// Downloads the selected file
function downloadFile() {
        const dropdown = document.getElementById('fileDropdown');
        const selectedFile = dropdown.value;
        if (selectedFile) {
            window.location.href = `/download_excel_from_file?filename=${selectedFile}`;
        } else {
            alert('Please select a file to download.');
        }
}

function deleteAllExcelFiles() {
    var confirmation = confirm("Are you sure you want to delete all Excel files?");
    if (confirmation) {
        fetch("/delete-all-excel-files", {
            method: "POST",
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            if (data.message) {
                alert(data.message);
                // Optionally, clear the dropdown:
                var dropdown = document.getElementById("fileDropdown");
                while (dropdown.firstChild) {
                    dropdown.removeChild(dropdown.firstChild);
                }
            } else if (data.error) {
                alert(data.error);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("There was an error deleting the files.");
        });
    }
}


// Call the populateDropdown function on page load
document.addEventListener("DOMContentLoaded", function() {
    populateDropdown();
});


// Stop Processing Button
function stopProcessing() {
    if (!confirm("Stop the current process and reset the interface?")) return;
    fetch('/stop_processing', { method: 'POST' })
        .then(response => response.json())
        .then(() => window.location.reload())
        .catch(error => {
            console.error('Error:', error);
            window.location.reload();
        });
}

document.addEventListener("DOMContentLoaded", function() {
    const progressElement = document.getElementById("progress");
    const progressTextElement = document.getElementById("progressText");
    const messageDivElement = document.getElementById('confirmationMessage');

    function createElement(tag, attrs, children) {
        const el = document.createElement(tag);
        for (let key in attrs) {
            el[key] = attrs[key];
        }
        if (children) {
            children.forEach(child => el.appendChild(child));
        }
        return el;
    }

    function createAndAppendTableRows(dataJSON) {
        const tableBody = document.querySelector('#dataTable tbody');
        dataJSON.forEach(dataItem => {
            const row = createElement('tr', {}, []);
            ['id', 'anchor', 'linking_url', 'topic', 'live_url', 'Host_site'].forEach(column => {
                const cell = createElement('td', {textContent: dataItem[column]});
                row.appendChild(cell);
            });
            tableBody.appendChild(row);
        });
    }

    // Progress bar helpers
    function showProgressBar() {
        document.getElementById("progressBarWrapper").style.display = "block";
    }
    function updateProgressBar(current, total) {
        const pct = total > 0 ? Math.round((current / total) * 100) : 0;
        const bar = document.getElementById("progressBar");
        bar.style.width = pct + "%";
        bar.setAttribute("aria-valuenow", pct);
        document.getElementById("progressCurrent").innerText = current;
        document.getElementById("progressTotal").innerText = total;
        document.getElementById("progressPercent").innerText = pct + "%";
        document.getElementById("progressLabel").innerText =
            current < total ? "Posting links..." : "Complete";
        if (current >= total && total > 0) {
            bar.classList.remove("progress-bar-animated");
            bar.classList.add("bg-success");
        }
    }

    // Form submission handling
    const form = document.getElementById("uploadForm");
    form.addEventListener("submit", function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        showProgressBar();
        document.getElementById("progressLabel").innerText = "Uploading & analyzing file...";
        document.getElementById("progress").style.display = "flex";
        fetch('/start_emit', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                document.getElementById("progressText").innerText = data.message;
            }
        });
    });

    // Socket.io connection
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port, {
        'reconnection': true,
        'reconnectionDelay': 500,
        'reconnectionAttempts': 5
    });

    socket.on('progress_init', function(data) {
        const tbody = document.querySelector('#dataTable tbody');
        if (tbody) tbody.innerHTML = '';
        showProgressBar();
        updateProgressBar(0, data.total || 0);
        document.getElementById("progressLabel").innerText =
            (data.total > 0) ? "Preparing — " + data.total + " links queued" : "No rows to post";
    });

    socket.on('progress_tick', function(data) {
        updateProgressBar(data.current || 0, data.total || 0);
    });

    socket.on('progress_reset', function() {
        document.getElementById("progressBarWrapper").style.display = "none";
        const tbody = document.querySelector('#dataTable tbody');
        if (tbody) tbody.innerHTML = '';
    });

    // Restore progress bar after page refresh
    socket.on('progress_state', function(data) {
        if (!data || data.total === 0) return;
        if (data.active || data.status === 'complete' || data.status === 'stopped') {
            showProgressBar();
            updateProgressBar(data.current || 0, data.total || 0);
            if (data.status === 'stopped') {
                document.getElementById("progressLabel").innerText = "Stopped";
            } else if (data.status === 'error') {
                document.getElementById("progressLabel").innerText = "Error occurred";
            }
        }
    });

    socket.on('update', function(data) {
        if (data.data) {
            createAndAppendTableRows(JSON.parse(data.data));
        }
        if (data.message) {
//            messageDivElement.innerHTML = data.message;
//            messageDivElement.style.display = "block";
//
//            if (["Processing complete.", "Process stopped"].includes(data.message)) {
//                progressElement.style.display = "none";
//            }

            if (data.message === "Processing Ended") {
                alert("Job Processing is complete!");
            }
        }

        if (data.error) {
            alert('Error: ' + data.error);
        }
    });


    // Progress spinner and text setup
    const progressDiv = createElement('div', {id: 'progress', className: 'd-flex align-items-center gap-2', style: 'display: none'});
    const spinner = createElement('div', {className: 'spinner-border spinner-border-sm text-primary', role: 'status'});
    const span = createElement('span', {className: 'visually-hidden', innerText: 'Processing...'});
    const progressText = createElement('span', {id: 'progressText', className: 'fw-semibold text-primary', innerText: 'Processing...'});
    spinner.appendChild(span);
    progressDiv.appendChild(spinner);
    progressDiv.appendChild(progressText);
    document.getElementById("progressContainer").appendChild(progressDiv);

});
