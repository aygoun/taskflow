const API_BASE = "/api";

let searchTimeout = null;

document.getElementById("taskTitle").addEventListener("keypress", (e) => {
    if (e.key === "Enter") addTask();
});

function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadTasks, 300);
}

async function loadTasks() {
    const listEl = document.getElementById("taskList");
    const search = document.getElementById("searchInput").value.trim();
    const priority = document.getElementById("filterPriority").value;
    const status = document.getElementById("filterStatus").value;

    listEl.innerHTML = '<p class="loading">Loading...</p>';

    try {
        let tasks;
        if (search) {
            const resp = await fetch(`${API_BASE}/tasks/search?q=${encodeURIComponent(search)}`);
            tasks = await resp.json();
        } else {
            let url = `${API_BASE}/tasks?limit=100`;
            if (priority) url += `&priority=${priority}`;
            if (status) url += `&completed=${status}`;
            const resp = await fetch(url);
            tasks = await resp.json();
        }

        // Apply status filter client-side if searching
        if (search && status) {
            tasks = tasks.filter(t => String(t.completed) === status);
        }

        renderTasks(tasks);
    } catch (err) {
        listEl.innerHTML = `<p class="error">Failed to load tasks: ${err.message}</p>`;
    }
}

function renderTasks(tasks) {
    const listEl = document.getElementById("taskList");

    if (tasks.length === 0) {
        listEl.innerHTML = '<p class="empty">No tasks found. Add one above!</p>';
        return;
    }

    listEl.innerHTML = tasks.map(task => `
        <div class="task-card ${task.completed ? 'completed' : ''} priority-${task.priority}">
            <div class="task-checkbox" onclick="toggleTask(${task.id}, ${!task.completed})">
                ${task.completed ? "&#10003;" : ""}
            </div>
            <div class="task-content">
                <div class="task-title">${escapeHtml(task.title)}</div>
                ${task.description ? `<div class="task-desc">${escapeHtml(task.description)}</div>` : ""}
                <div class="task-meta">
                    <span class="badge priority-${task.priority}">${task.priority}</span>
                    ${task.due_date ? `<span class="badge due">Due: ${task.due_date}</span>` : ""}
                    <span class="badge date">${formatDate(task.created_at)}</span>
                </div>
            </div>
            <button class="task-delete" onclick="deleteTask(${task.id})" title="Delete">&times;</button>
        </div>
    `).join("");
}

async function addTask() {
    const titleEl = document.getElementById("taskTitle");
    const title = titleEl.value.trim();
    if (!title) return;

    const priority = document.getElementById("taskPriority").value;
    const dueDate = document.getElementById("taskDueDate").value || null;

    try {
        const resp = await fetch(`${API_BASE}/tasks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, priority, due_date: dueDate }),
        });
        if (resp.ok) {
            titleEl.value = "";
            document.getElementById("taskDueDate").value = "";
            loadTasks();
        }
    } catch (err) {
        alert("Failed to add task: " + err.message);
    }
}

async function toggleTask(id, completed) {
    try {
        await fetch(`${API_BASE}/tasks/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ completed }),
        });
        loadTasks();
    } catch (err) {
        alert("Failed to update task: " + err.message);
    }
}

async function deleteTask(id) {
    if (!confirm("Delete this task?")) return;
    try {
        await fetch(`${API_BASE}/tasks/${id}`, { method: "DELETE" });
        loadTasks();
    } catch (err) {
        alert("Failed to delete task: " + err.message);
    }
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

// Initial load
loadTasks();
