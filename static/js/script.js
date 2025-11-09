/*
  runPipeline()
  - Triggered by the "Run Analysis & Reduce" button in the UI.
  - Calls server endpoint `/run` which runs: scan -> analysis -> map -> reduce.
  - Disables the button while the pipeline runs, shows status messages, and reloads
    the view when complete.
  Note: `/run` returns JSON { status: 'complete', newly_analyzed: <number> }.
*/
function runPipeline() {
    const btn = document.getElementById('runBtn');
    const status = document.getElementById('status');

    // Prevent double-submits while the pipeline is running
    btn.disabled = true;
    status.textContent = "Running Pipeline... (Scanning -> Gemini -> Map -> Reduce)";

    fetch('/run')
        .then(res => res.json())
        .then(data => {
            // Show concise completion feedback and refresh the displayed data
            status.textContent = `Complete! Newly analyzed: ${data.newly_analyzed} files.`;
            loadView();
            btn.disabled = false;
        })
        .catch(err => {
            // Network or server error — surface to the status line and re-enable
            status.textContent = "Error: " + err;
            btn.disabled = false;
        });
}


/*
    loadView()
    - Fetches grouped data from `/data` and passes it to `render()`.
    - `/data` returns an object shaped like:
            {
                "TAG_NAME": [ { name: "file1.pdf", all_keys: ["TAG_NAME","OTHER"] }, ... ],
                ...
            }
    - `render()` expects the exact structure above when building DOM nodes.
*/
function loadView() {
        fetch('/data')
                .then(res => res.json())
                .then(data => render(data));
}


/*
  render(data)
  - Build the visible DOM for the grouped tags and their files.
  - The function intentionally builds HTML strings for simplicity; for larger
    projects consider using a light templating or virtual DOM approach.
  - Important: `file.all_keys` must be present for each file entry; it is used
    to render pills and determine the `.active` pill (the pill that matches the
    current group header).
*/
function render(data) {
    const container = document.getElementById('results');
    container.innerHTML = '';

    // data is { "key1": [ {name: "doc1", all_keys: ["key1", "key2"]}, ... ] }
    for (const [genreKey, files] of Object.entries(data)) {
        let html = `
            <div class="genre-group">
                <div class="genre-header">${genreKey}</div>
                <div class="file-list">
        `;

        files.forEach(file => {
            // Render all tags, highlighting the one that matches the current header
            // The UI expects `file.name` and `file.all_keys` to exist for each file.
            const tagsHtml = file.all_keys.map(key => 
                `<span class="key-pill ${key === genreKey ? 'active' : ''}">${key}</span>`
            ).join('');

            html += `
                <div class="file-item">
                    <div class="file-name">${file.name}</div>
                    <div class="file-keys">${tagsHtml}</div>
                </div>
            `;
        });

        html += `</div></div>`;
        container.innerHTML += html;
    }
}


// Load existing data on page load
// Load existing data on page load so the UI is populated immediately.
loadView();
