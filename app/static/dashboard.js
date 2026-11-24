const ticketRows = document.querySelector("#ticketRows");
const notice = document.querySelector("#notice");

const refreshButton = document.querySelector("#refreshButton");
const searchInput = document.querySelector("#searchInput");
const statusFilter = document.querySelector("#statusFilter");
const departmentFilter = document.querySelector("#departmentFilter");

let allTickets = [];

function showNotice(message, type = "success") {
  notice.textContent = message;
  notice.className = `notice ${type}`;
}

function clearNotice() {
  notice.textContent = "";
  notice.className = "notice";
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function makeCell(value, className = "") {
  const cell = document.createElement("td");
  cell.textContent = value ?? "—";

  if (className) {
    cell.className = className;
  }

  return cell;
}

function updateStatistics() {
  document.querySelector("#totalCount").textContent = allTickets.length;

  document.querySelector("#openCount").textContent = allTickets.filter(
    (ticket) => ticket.status === "open",
  ).length;

  document.querySelector("#progressCount").textContent = allTickets.filter(
    (ticket) => ticket.status === "in_progress",
  ).length;

  document.querySelector("#resolvedCount").textContent = allTickets.filter(
    (ticket) => ticket.status === "resolved",
  ).length;
}

function getFilteredTickets() {
  const search = searchInput.value.trim().toLowerCase();
  const status = statusFilter.value;
  const department = departmentFilter.value;

  return allTickets.filter((ticket) => {
    const matchesStatus = !status || ticket.status === status;

    const matchesDepartment = !department || ticket.department === department;

    const searchableText = [
      ticket.ticket_id,
      ticket.customer_message,
      ticket.department,
      ticket.reason,
      ticket.status,
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch = !search || searchableText.includes(search);

    return matchesStatus && matchesDepartment && matchesSearch;
  });
}

function createStatusSelect(currentStatus) {
  const select = document.createElement("select");
  select.className = "status-select";
  select.setAttribute("aria-label", "Choose ticket status");

  const options = [
    { value: "open", label: "Open" },
    { value: "in_progress", label: "In progress" },
    { value: "resolved", label: "Resolved" },
  ];

  for (const item of options) {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
    option.selected = item.value === currentStatus;

    select.appendChild(option);
  }

  return select;
}

function renderTickets() {
  const tickets = getFilteredTickets();

  document.querySelector("#visibleCount").textContent =
    `${tickets.length} ${tickets.length === 1 ? "ticket" : "tickets"}`;

  ticketRows.replaceChildren();

  if (tickets.length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = 6;
    cell.className = "empty-state";
    cell.textContent = allTickets.length
      ? "No tickets match your search or filters."
      : "No support tickets yet. Escalated conversations will appear here.";

    row.appendChild(cell);
    ticketRows.appendChild(row);
    return;
  }

  for (const ticket of tickets) {
    const row = document.createElement("tr");

    const idCell = document.createElement("td");
    const id = document.createElement("span");

    id.className = "ticket-id";
    id.textContent = ticket.ticket_id;

    idCell.appendChild(id);
    row.appendChild(idCell);

    row.appendChild(makeCell(ticket.customer_message, "ticket-message"));

    const departmentCell = document.createElement("td");
    const department = document.createElement("span");

    department.className = "department-label";
    department.textContent = ticket.department;

    departmentCell.appendChild(department);
    row.appendChild(departmentCell);

    row.appendChild(makeCell(ticket.reason, "reason-cell"));

    row.appendChild(makeCell(formatDate(ticket.created_at)));

    const actionCell = document.createElement("td");
    const statusSelect = createStatusSelect(ticket.status);

    const updateButton = document.createElement("button");
    updateButton.type = "button";
    updateButton.className = "update-button";
    updateButton.textContent = "Save status";

    updateButton.addEventListener("click", async () => {
      await updateTicketStatus(
        ticket.ticket_id,
        statusSelect.value,
        updateButton,
      );
    });

    actionCell.appendChild(statusSelect);
    actionCell.appendChild(updateButton);
    row.appendChild(actionCell);

    ticketRows.appendChild(row);
  }
}

async function loadTickets({ silent = false } = {}) {
  refreshButton.disabled = true;
  refreshButton.textContent = "Loading...";

  if (!silent) {
    clearNotice();
  }

  try {
    const response = await fetch("/api/tickets", {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Could not load tickets. HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!Array.isArray(data.tickets)) {
      throw new Error("Unexpected response from the tickets API.");
    }

    allTickets = data.tickets;

    updateStatistics();
    renderTickets();

    document.querySelector("#lastUpdated").textContent =
      `Last updated: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    showNotice(error.message, "error");
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "↻ Refresh tickets";
  }
}

async function updateTicketStatus(ticketId, status, button) {
  clearNotice();

  button.disabled = true;
  button.textContent = "Saving...";

  try {
    const response = await fetch(
      `/api/tickets/${encodeURIComponent(ticketId)}/status`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ status }),
      },
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Ticket status update failed.");
    }

    await loadTickets({ silent: true });

    showNotice(
      `Ticket ${ticketId} updated to "${status.replace("_", " ")}".`,
      "success",
    );
  } catch (error) {
    showNotice(error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Save status";
  }
}

searchInput.addEventListener("input", renderTickets);
statusFilter.addEventListener("change", renderTickets);
departmentFilter.addEventListener("change", renderTickets);

refreshButton.addEventListener("click", () => {
  loadTickets();
});

loadTickets();
