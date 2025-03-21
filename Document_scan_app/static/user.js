document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const uploadBtn = document.getElementById("uploadBtn");
    const fileInput = document.getElementById("fileInput");
    const loadingIndicator = document.getElementById("loading");
    const remainingUploadsElement = document.getElementById("remainingUploads");
    const similarityResult = document.getElementById("similarityResult");

    uploadForm.addEventListener("submit", function (event) {
        if (fileInput.files.length === 0) {
            event.preventDefault(); // Stop form submission if no file is selected
            alert("Please select a file before uploading!");
            return;
        }

        uploadBtn.disabled = true; // Disable button to prevent multiple uploads
        loadingIndicator.style.display = "block"; // Show loading message
    });

    // Auto-hide flash messages after 5 seconds
    setTimeout(function () {
        let messages = document.getElementById("messages");
        if (messages) {
            messages.style.display = "none";
        }
    }, 5000);

    // Fetch similarity results after upload
    function fetchResults() {
        fetch("/get_results") // Assuming this endpoint returns JSON with comparison data
            .then(response => response.json())
            .then(data => {
                similarityResult.innerHTML = "";
                if (data.user_comparisons.length > 0 || data.all_users_comparisons.length > 0) {
                    let html = "";
                    
                    // User's Own Files Comparison
                    if (data.user_comparisons.length > 0) {
                        html += "<h2>Your Files</h2><table><thead><tr><th>Uploaded File</th><th>Compared File</th><th>Similarity (%)</th></tr></thead><tbody>";
                        data.user_comparisons.forEach(result => {
                            html += `<tr><td>${result.uploaded_file}</td><td>${result.compared_file}</td><td>${result.similarity}%</td></tr>`;
                        });
                        html += "</tbody></table>";
                    }
                    
                    // All Users' Files Comparison
                    if (data.all_users_comparisons.length > 0) {
                        html += "<h2>All Users</h2><table><thead><tr><th>Uploaded File</th><th>Compared File</th><th>Similarity (%)</th></tr></thead><tbody>";
                        data.all_users_comparisons.forEach(result => {
                            html += `<tr><td>${result.uploaded_file}</td><td>${result.compared_file}</td><td>${result.similarity}%</td></tr>`;
                        });
                        html += "</tbody></table>";
                    }
                    
                    similarityResult.innerHTML = html;
                }
            })
            .catch(error => console.error("Error fetching results:", error));
    }

    // Fetch results on page load
    fetchResults();
});
