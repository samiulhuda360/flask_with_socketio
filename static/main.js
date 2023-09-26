// Stop Processing Button
function stopProcessing() {
    fetch('/stop_processing', { method: 'POST' })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error('Error:', error));
}

document.addEventListener("DOMContentLoaded", function() {
    // Helper functions
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
        tableBody.innerHTML = '';
        dataJSON.forEach(dataItem => {
            const row = createElement('tr', {}, []);
            ['id', 'anchor', 'linking_url', 'topic', 'live_url', 'Host_site'].forEach(column => {
                const cell = createElement('td', {textContent: dataItem[column]});
                row.appendChild(cell);
            });
            tableBody.appendChild(row);
        });
    }

    // Form submission handling
    const form = document.getElementById("uploadForm");
    form.addEventListener("submit", function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        document.getElementById("progress").style.display = "block";
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
    const socket = io.connect('http://' + document.domain + ':' + location.port, {
        'reconnection': true,
        'reconnectionDelay': 500,
        'reconnectionAttempts': 5
    });

    socket.on('update', function(data) {
        if (data.data) {
            createAndAppendTableRows(JSON.parse(data.data));
        }
        if (data.message) {
            const messageDiv = document.getElementById('confirmationMessage');
            messageDiv.innerHTML = data.message;
            messageDiv.style.display = "block";
       if (data.message === "Process stopped" || data.message === "Processing complete.") {
                document.getElementById("progress").style.display = "none";
            }
       // Handle errors from the 'start_emit' function here
         if (data.error) {
        alert('Error: ' + data.error);
    }
        }
    });

    // Progress spinner and text setup
    const progressDiv = createElement('div', {id: 'progress', style: 'display: none'});
    const spinner = createElement('div', {className: 'spinner-border text-primary', role: 'status'});
    const span = createElement('span', {className: 'sr-only', innerText: 'Processing...'});
    const progressText = createElement('p', {id: 'progressText', innerText: 'Processing...'});

    spinner.appendChild(span);
    progressDiv.appendChild(spinner);
    progressDiv.appendChild(progressText);
    document.getElementById("progressContainer").appendChild(progressDiv);

    // Fake scroll sync
    const table = document.getElementById('dataTable');
    const fakeScroll = document.getElementById('fakeScroll');
    const fakeContent = document.getElementById('fakeContent');

    fakeContent.style.width = table.offsetWidth + 'px';

    // Inside your DOMContentLoaded event
    console.log("DOM fully loaded and parsed");

    // Inside your fake scroll event listeners
    fakeScroll.addEventListener('scroll', function() {
        table.parentNode.scrollLeft = fakeScroll.scrollLeft;
    });

    table.parentNode.addEventListener('scroll', function() {
        fakeScroll.scrollLeft = table.parentNode.scrollLeft;
    });



});
