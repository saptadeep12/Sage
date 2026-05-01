const chatWindow = document.getElementById("chat-window");
const input      = document.getElementById("user-input");
const sendBtn    = document.getElementById("send-btn");
const welcome    = document.getElementById("welcome");

// Auto-resize textarea
input.addEventListener("input", () => {
  input.style.height = "24px";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
});

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function sendMessage() {
  const query = input.value.trim();
  if (!query) return;

  input.value = "";
  input.style.height = "24px";
  sendBtn.disabled = true;

  addMessage(query, "user");
  addTyping();

  try {
      const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: query })
      });

      // Remove typing indicator and create empty sage bubble
      removeTyping();
      const bubble = addMessage("", "sage");

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer    = "";

      while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop(); // keep incomplete line in buffer

          for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const data = line.slice(6);
              if (data === "[DONE]") break;

              try {
                  const parsed = JSON.parse(data);
                  if (parsed.token) {
                      bubble._raw = (bubble._raw || "") + parsed.token;
                      bubble.innerHTML = marked.parse(bubble._raw);
                      chatWindow.scrollTop = chatWindow.scrollHeight;   // append word by word
                  }
              } catch {}
          }
      }
  } catch (err) {
      removeTyping();
      addMessage("I'm having trouble connecting. Is the server running?", "sage");
  }

  sendBtn.disabled = false;
  input.focus();
}

function usePrompt(el) {
  input.value = el.textContent;
  input.focus();
  sendMessage();
}

function addMessage(text, role) {
  if (welcome) welcome.style.display = "none";

  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role}`;
  avatar.textContent = role === "sage" ? "🌿" : "you";

  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;

  // Render markdown for sage, plain text for user
  if (role === "sage" && text) {
      bubble.innerHTML = marked.parse(text);
  } else {
      bubble.textContent = text;
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

function addTyping() {
  if (welcome) welcome.style.display = "none";

  const row    = document.createElement("div");
  row.className = "message-row";
  row.id = "typing-row";

  const avatar = document.createElement("div");
  avatar.className = "avatar sage";
  avatar.textContent = "🌿";

  const bubble = document.createElement("div");
  bubble.className = "bubble sage typing";
  bubble.innerHTML = "<span></span><span></span><span></span>";

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById("typing-row");
  if (t) t.remove();
}
