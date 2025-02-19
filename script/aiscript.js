/// Constants
const API_KEY = "AIzaSyBNjHRBNj7NW382WgKA7n3KVh56-MVfNTo";
const API_URL = `https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${API_KEY}`;
const SYSTEM_INSTRUCTION = {
    role: "user", // Add the role property
    parts: [{
    text: "You are a legal advisor chatbot specialized in corporate law in India. " +
              "Your role is to answer questions related to the Companies Act 2013, corporate governance, compliance, and related legal matters. " +
              "You can also handle scenario-based questions related to corporate issues, such as conflicts with colleagues, lost company property, or workplace disputes. " +
              "If a user greets you, respond with a friendly greeting and encourage them to ask about corporate law. " +
              "If a user asks a question unrelated to corporate law, politely inform them that you can only answer questions related to corporate law. " +
              "For example, you can say: 'I am a legal advisor chatbot specialized in corporate law in India. Please ask questions related to corporate law.'"
    }]
};
   

// DOM Elements
const elements = {
    messageForm: document.querySelector(".prompt__form"),
    chatContainer: document.querySelector(".chats"),
    suggestionItems: document.querySelectorAll(".suggests__item"),
    themeToggler: document.getElementById("themeToggler"),
    deleteButton: document.getElementById("deleteButton"),
    sidebarToggle: document.getElementById("sidebarToggle"),
    sidebar: document.getElementById("sidebar"),
    mainContent: document.querySelector(".main-content"),
    chatList: document.getElementById("chatList"),
    textInput: document.querySelector(".prompt__form-input"),
    newChatButton: document.getElementById("newChatButton")
};

// State
let currentChatId = null;
let chats = [];
let isGeneratingResponse = false;

// Chat Management
class ChatManager {
    static createMessageElement(content, type) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message message--${type}`;
        messageDiv.innerHTML = content;
        return messageDiv;
    }

    static async addUserMessage(message) {
        const messageHTML = `
            <div class="message__content">
                <p class="message__text">${message}</p>
            </div>
        `;
        elements.chatContainer.appendChild(this.createMessageElement(messageHTML, "outgoing"));
        this.autoScroll();
    }

    static addLoadingMessage() {
        const loadingHTML = `
            <div class="message__content">
                <p class="message__text"></p>
                <div class="message__loading-indicator">
                    <div class="message__loading-bar"></div>
                    <div class="message__loading-bar"></div>
                    <div class="message__loading-bar"></div>
                </div>
            </div>
        `;
        const loadingElement = this.createMessageElement(loadingHTML, "incoming message--loading");
        elements.chatContainer.appendChild(loadingElement);
        this.autoScroll();
        return loadingElement;
    }

    static updateLoadingMessage(loadingElement, content) {
        const messageText = loadingElement.querySelector(".message__text");
        messageText.innerHTML = marked.parse(content);
        loadingElement.classList.remove("message--loading");
        this.addCopyButton(loadingElement);
        hljs.highlightAll();
        this.autoScroll();
    }

    static addCopyButton(messageElement) {
        const copyButton = document.createElement("button");
        copyButton.className = "message__copy-btn";
        copyButton.innerHTML = '<i class="bx bx-copy"></i>';
        copyButton.onclick = () => this.copyToClipboard(messageElement);
        messageElement.appendChild(copyButton);
    }

    static async copyToClipboard(messageElement) {
        const text = messageElement.querySelector(".message__text").textContent;
        try {
            await navigator.clipboard.writeText(text);
            const copyBtn = messageElement.querySelector(".message__copy-btn i");
            copyBtn.className = "bx bx-check";
            setTimeout(() => copyBtn.className = "bx bx-copy", 2000);
        } catch (err) {
            console.error("Failed to copy text:", err);
        }
    }

    static autoScroll() {
        elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
    }
}

// API Interaction
class APIService {
    static async getResponse(message) {
        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    contents: [
                        SYSTEM_INSTRUCTION,
                        { role: "user", parts: [{ text: message }] }
                    ]
                })
            });

            console.log("API Request:", {
                url: API_URL,
                method: "POST",
                body: JSON.stringify({
                    contents: [
                        SYSTEM_INSTRUCTION,
                        { role: "user", parts: [{ text: message }] }
                    ]
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("API Error:", errorData);
                throw new Error(errorData.error?.message || "API request failed");
            }

            const data = await response.json();
            console.log("API Response:", data);

            const responseText = data?.candidates?.[0]?.content?.parts?.[0]?.text;
            if (!responseText) throw new Error("Invalid API response.");

            return responseText;
        } catch (error) {
            console.error("API Request Failed:", error);
            throw error;
        }
    }
}

// Storage Management
class StorageManager {
    static saveChat(chat) {
        chats.push(chat);
        localStorage.setItem("saved-chats", JSON.stringify(chats));
    }

    static getChats() {
        return JSON.parse(localStorage.getItem("saved-chats")) || [];
    }

    static clearChats() {
        localStorage.removeItem("saved-chats");
        chats = [];
        elements.chatContainer.innerHTML = "";
    }

    static loadChats() {
        chats = this.getChats();
    }
}

// Event Handlers
function startNewChat() {
    currentChatId = Date.now();
    elements.chatContainer.innerHTML = "";
}

// Initialization
function initialize() {
    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.body.classList.add("light_mode");
    }

    // Load saved chats
    StorageManager.loadChats();

    // Initialize event listeners
    initializeEventListeners();
}

// Event Handlers
async function handleSubmit(e) {
    e.preventDefault();
    if (isGeneratingResponse) return;

    const message = elements.textInput.value.trim();
    if (!message) return;

    isGeneratingResponse = true;
    elements.textInput.value = "";

    // Add user message
    ChatManager.addUserMessage(message);

    // Add loading message
    const loadingElement = ChatManager.addLoadingMessage();

    try {
        const response = await APIService.getResponse(message);
        ChatManager.updateLoadingMessage(loadingElement, response);

        // Save chat
        const chat = { id: currentChatId || Date.now(), messages: [{ message, response }] };
        StorageManager.saveChat(chat);
    } catch (error) {
        console.error("Error:", error);
        loadingElement.querySelector(".message__text").textContent = "Sorry, I couldn't process your request. Please try again later.";
        loadingElement.classList.add("message--error");
    } finally {
        isGeneratingResponse = false;
    }
}
function handleSuggestionClick(e) {
    const suggestion = e.currentTarget.querySelector(".suggests__item-text").textContent;
    elements.textInput.value = suggestion;
    handleSubmit(new Event("submit"));
}

function toggleSidebar() {
    elements.sidebar.classList.toggle("active");
    elements.mainContent.classList.toggle("sidebar-active");
}

function toggleTheme() {
    document.body.classList.toggle("light_mode");
    localStorage.setItem("theme", document.body.classList.contains("light_mode") ? "light" : "dark");
}

function startNewChat() {
    currentChatId = Date.now();
    elements.chatContainer.innerHTML = "";
}

function loadChat(index) {
    const chat = chats[index];
    if (!chat) return;

    currentChatId = chat.id;
    elements.chatContainer.innerHTML = "";

    chat.messages.forEach(({ message, response }) => {
        ChatManager.addUserMessage(message);
        const loadingElement = ChatManager.addLoadingMessage();
        ChatManager.updateLoadingMessage(loadingElement, response);
    });
}

// Event Listeners
function initializeEventListeners() {
    elements.messageForm.addEventListener("submit", handleSubmit);
    elements.suggestionItems.forEach(item => item.addEventListener("click", handleSuggestionClick));
    elements.sidebarToggle.addEventListener("click", toggleSidebar);
    elements.themeToggler.addEventListener("click", toggleTheme);
    elements.deleteButton.addEventListener("click", () => {
        if (confirm("Are you sure you want to clear all chats?")) {
            StorageManager.clearChats();
        }
    });
    elements.newChatButton.addEventListener("click", startNewChat);

    // Auto-resize textarea
    elements.textInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
        ChatManager.autoScroll(); // Auto-scroll while typing
    });

    // Handle Enter key
    elements.textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    });
}

// Initialization
function initialize() {
    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.body.classList.add("light_mode");
    }

    // Load saved chats
    StorageManager.loadChats();

    // Initialize event listeners
    initializeEventListeners();
}

// Start the application
initialize();