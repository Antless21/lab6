"use strict";

const joinForm = document.getElementById("join-form");
const messageForm = document.getElementById("message-form");
const nameInput = document.getElementById("chat-name");
const messageInput = document.getElementById("message");
const connectButton = document.getElementById("connect");
const disconnectButton = document.getElementById("disconnect");
const sendButton = document.getElementById("send");
const statusLabel = document.getElementById("status");
const messages = document.getElementById("messages");
let socket = null;

function setConnected(connected) {
  nameInput.disabled = connected;
  connectButton.disabled = connected;
  disconnectButton.disabled = !connected;
  messageInput.disabled = !connected;
  sendButton.disabled = !connected;
}

joinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = nameInput.value.trim();
  if (!name || (socket && socket.readyState < WebSocket.CLOSING)) return;
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(`${protocol}//${location.host}/ws/chat?name=${encodeURIComponent(name)}`);
  connectButton.disabled = true;
  statusLabel.textContent = "Подключение…";
  socket.addEventListener("open", () => {
    setConnected(true);
    statusLabel.textContent = `В чате: ${name}`;
    messageInput.focus();
  });
  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    const item = document.createElement("li");
    // textContent выводит пользовательский текст без выполнения HTML/JavaScript.
    item.textContent = data.type === "message"
      ? `${new Date(data.time).toLocaleTimeString()} · ${data.name}: ${data.text}`
      : data.text;
    if (data.type === "error") item.className = "error";
    messages.appendChild(item);
    if (messages.children.length > 200) messages.firstElementChild.remove();
    messages.scrollTop = messages.scrollHeight;
  });
  socket.addEventListener("close", () => {
    setConnected(false);
    statusLabel.textContent = "Соединение закрыто. Можно войти снова.";
  });
  socket.addEventListener("error", () => {
    statusLabel.textContent = "Не удалось подключиться к серверу.";
  });
});

disconnectButton.addEventListener("click", () => socket?.close(1000));
messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (text && socket?.readyState === WebSocket.OPEN) {
    socket.send(text);
    messageInput.value = "";
  }
});
