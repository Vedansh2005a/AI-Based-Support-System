const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const messages = document.querySelector("#messages");
const errorNotice = document.querySelector("#errorNotice");

function appendMessage(role, text, ticket = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  if (ticket && ticket.handoff) {
    const details = document.createElement("span");
    details.className = "ticket-details";
    details.textContent =
      `Ticket: ${ticket.ticket_id || "Created"}\n` +
      `Department: ${ticket.department || "Customer Support"}\n` +
      `Status: ${ticket.ticket_status || "open"}`;

    bubble.appendChild(details);
  }

  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);

  messages.scrollTop = messages.scrollHeight;

  return wrapper;
}

function showError(message) {
  errorNotice.textContent = message;
  errorNotice.classList.add("visible");
}

function clearError() {
  errorNotice.textContent = "";
  errorNotice.classList.remove("visible");
}

async function sendMessage(message) {
  clearError();

  appendMessage("user", message);

  const typingMessage = appendMessage(
    "assistant typing",
    "Thinking... Finding the best support answer.",
  );

  sendButton.disabled = true;
  messageInput.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    typingMessage.remove();

    if (!response.ok) {
      throw new Error(data.detail || `Request failed (${response.status}).`);
    }

    appendMessage(
      "assistant",
      data.response || "Sorry, no response was returned.",
      data.handoff ? data : null,
    );
  } catch (error) {
    typingMessage.remove();

    appendMessage(
      "assistant",
      "Sorry, I couldn't process your request right now. " +
        "Please try again.",
    );

    showError(error.message || "Unable to connect to the support API.");
  } finally {
    sendButton.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();

  if (!message || sendButton.disabled) {
    return;
  }

  messageInput.value = "";

  await sendMessage(message);
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
