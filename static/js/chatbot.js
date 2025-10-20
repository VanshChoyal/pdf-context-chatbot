document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("send-btn");
    const chatInput = document.getElementById("chat-input");
    const messages = document.getElementById("messages");
    const fileList = document.getElementById("file-list");
    
    const md = window.markdownit({
        highlight: function (str, lang) {
            if (lang && Prism.languages[lang]) {
                try {
                    return '<pre class="language-' + lang + '"><code>' +
                           Prism.highlight(str, Prism.languages[lang], lang) +
                           '</code></pre>';
                } catch (__) {}
            }
            return '<pre class="language-none"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
        }
    });

    function createSpinner() {
        const container = document.createElement("div");
        container.className = "spinner-container";
        const spinner = document.createElement("div");
        spinner.className = "spinner";
        container.appendChild(spinner);
        return container;
    }

    function showSpinnerInFiles() {
        fileList.innerHTML = '';
        fileList.appendChild(createSpinner());
    }

    function showSpinnerInChat() {
        const spinnerMsg = document.createElement("div");
        spinnerMsg.classList.add("message", "bot");
        spinnerMsg.appendChild(createSpinner());
        messages.appendChild(spinnerMsg);
        messages.scrollTop = messages.scrollHeight;
        return spinnerMsg;
    }

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    showSpinnerInFiles();
    fetch("/api/get/file_names")
    .then(response => response.json())
    .then(data => {
        fileList.innerHTML = '';
        data.forEach(fileName => {
            add_files_item(fileName);
        });
    })
    .catch(err => {
        console.error("Error fetching file names:", err);
        fileList.innerHTML = '<div style="padding: 10px; color: red;">Error loading files</div>';
    });

function add_files_item(fileName) {
    const li = document.createElement("li");
    const fileNameSpan = document.createElement("span");
    fileNameSpan.className = "file-name";
    fileNameSpan.textContent = fileName;
    li.appendChild(fileNameSpan);

    const deleteIcon = document.createElement("i");
    deleteIcon.className = "fas fa-trash-alt delete-icon";
    deleteIcon.setAttribute('title', 'Delete file');
    
    deleteIcon.addEventListener("click", async (e) => {
        e.stopPropagation();
        
        if (confirm(`Are you sure you want to delete ${fileName}? This will remove the file from the chat context.`)) {
            try {
                const response = await fetch("/api/delete/file", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ file_name: fileName })
                });

                if (response.ok) {
                    li.remove();
                } else {
                    alert("Failed to delete the file");
                }
            } catch (err) {
                console.error("Error deleting file:", err);
                alert("Error deleting file");
            }
        }
    });

    li.appendChild(deleteIcon);
    fileList.appendChild(li);
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.classList.add("message", "user");
    userMsg.textContent = text;
    messages.appendChild(userMsg);
    chatInput.value = "";
    messages.scrollTop = messages.scrollHeight;

    const spinnerMsg = showSpinnerInChat();

    fetch("/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question: text })
    })
    .then(response => response.json())
    .then(data => {
        spinnerMsg.remove();
        const botMsg = document.createElement("div");
        botMsg.classList.add("message", "bot");

        if (data.success) {
            botMsg.innerHTML = md.render(data.response);
            botMsg.querySelectorAll('pre code').forEach((block) => {
                Prism.highlightElement(block);
            });
        } else {
            botMsg.textContent = "Error: " + (data.error || "Something went wrong");
        }

        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
    })
    .catch(err => {
        spinnerMsg.remove();
        const botMsg = document.createElement("div");
        botMsg.classList.add("message", "bot");
        botMsg.textContent = "Error: " + err;
        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
    });
}

    const pdfInput = document.createElement("input");
    pdfInput.type = "file";
    pdfInput.accept = ".pdf";
    pdfInput.style.display = "none";
    document.body.appendChild(pdfInput);

    document.querySelector(".add-file-btn").addEventListener("click", () => {
        pdfInput.click();
    });

    pdfInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("pdf", file);

        try {
            const res = await fetch("/api/upload/pdf", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                add_files_item(file.name);
            } else {
                alert("Upload failed!");
            }
        } catch (err) {
            console.error(err);
            alert("Upload error!");
        }

        e.target.value = "";
    });
});
