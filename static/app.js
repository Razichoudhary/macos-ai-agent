/**
 * macOS AI Agent — Frontend Application Controller
 * Handles WebSockets, Dual Voice Engine with 2s Silence Detection,
 * Real-Time Telemetry Polling, and Instant macOS Automation.
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- Elements ---
    const chatStream = document.getElementById("chatStream");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const inlineMicBtn = document.getElementById("inlineMicBtn");
    const bigMicBtn = document.getElementById("bigMicBtn");
    const voiceStage = document.getElementById("voiceStage");
    const voiceHeading = document.getElementById("voiceHeading");
    const voiceSubtext = document.getElementById("voiceSubtext");
    const voiceToggleNavBtn = document.getElementById("voiceToggleNavBtn");
    const clearMemoryBtn = document.getElementById("clearMemoryBtn");
    const pauseMeterWrap = document.getElementById("pauseMeterWrap");
    const pauseBarFill = document.getElementById("pauseBarFill");

    // Telemetry & Hardware elements
    const connectionPill = document.getElementById("connectionPill");
    const batteryText = document.getElementById("batteryText");
    const hudBatteryValue = document.getElementById("hudBatteryValue");
    const batteryProgressFill = document.getElementById("batteryProgressFill");
    const volumeSlider = document.getElementById("volumeSlider");
    const hudVolumeValue = document.getElementById("hudVolumeValue");
    const volDownBtn = document.getElementById("volDownBtn");
    const volUpBtn = document.getElementById("volUpBtn");
    const muteToggleBtn = document.getElementById("muteToggleBtn");
    const specCpu = document.getElementById("specCpu");

    // Media elements
    const trackTitle = document.getElementById("trackTitle");
    const trackArtist = document.getElementById("trackArtist");
    const vinylRecord = document.getElementById("vinylRecord");
    const mediaPlayPauseBtn = document.getElementById("mediaPlayPauseBtn");
    const mediaPrevBtn = document.getElementById("mediaPrevBtn");
    const mediaNextBtn = document.getElementById("mediaNextBtn");
    const mediaRandomBtn = document.getElementById("mediaRandomBtn");
    const songSearchInput = document.getElementById("songSearchInput");
    const songPlaySubmitBtn = document.getElementById("songPlaySubmitBtn");

    // Activity Stream
    const activityStream = document.getElementById("activityStream");

    // --- State Variables ---
    let isVoiceActive = false;
    let speechRecognition = null;
    let pauseTimer = null;
    let pauseCountdownInterval = null;
    let accumulatedTranscript = "";
    let websocket = null;
    let isPlayingMedia = false;

    // ==============================================================================
    // 1. WebSocket Live Stream
    // ==============================================================================
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/live`;
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            connectionPill.className = "status-pill status-connected";
            connectionPill.querySelector(".status-label").textContent = "Online";
            logActivity("Connected", "WebSocket live stream active.");
        };

        websocket.onmessage = (event) => {
            try {
                const data = jsonParseSafe(event.data);
                handleWebSocketEvent(data);
            } catch (err) {
                console.warn("WebSocket parse error:", err);
            }
        };

        websocket.onclose = () => {
            connectionPill.className = "status-pill";
            connectionPill.querySelector(".status-label").textContent = "Offline";
            setTimeout(initWebSocket, 3000);
        };

        websocket.onerror = () => {
            websocket.close();
        };
    }

    function handleWebSocketEvent(data) {
        if (!data) return;
        if (data.type === "tool_start") {
            logActivity(`⚙️ ${data.tool}`, `Invoking: ${data.input || ""}`);
        } else if (data.type === "tool_end") {
            logActivity("✅ Tool Completed", data.output || "Action succeeded.");
        } else if (data.type === "tool_error") {
            logActivity("❌ Tool Error", data.error || "An error occurred.");
        } else if (data.type === "init" && data.status) {
            updateTelemetryUI(data.status);
        }
    }

    function logActivity(title, desc) {
        const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        const item = document.createElement("div");
        item.className = "activity-item";
        item.innerHTML = `
            <span class="activity-time">${timeStr}</span>
            <div class="activity-content">
                <strong>${escapeHtml(title)}</strong>
                <p>${escapeHtml(desc)}</p>
            </div>
        `;
        activityStream.prepend(item);
        // Cap activity items to 20
        while (activityStream.children.length > 20) {
            activityStream.removeChild(activityStream.lastChild);
        }
    }

    // ==============================================================================
    // 2. Real-Time Telemetry Polling (Battery, Volume, Specs)
    // ==============================================================================
    async function fetchSystemStatus() {
        try {
            const res = await fetch("/api/status");
            if (!res.ok) return;
            const data = await res.json();
            updateTelemetryUI(data);
        } catch (e) {
            // Server offline or starting
        }
    }

    function updateTelemetryUI(data) {
        if (!data) return;

        // Battery
        if (data.battery) {
            const pct = data.battery.percent || 0;
            const isCharging = data.battery.charging;
            batteryText.textContent = `${pct}% ${isCharging ? "⚡" : ""}`;
            hudBatteryValue.textContent = `${pct}% ${isCharging ? "(Charging)" : ""}`;
            batteryProgressFill.style.width = `${pct}%`;
            if (pct <= 20) {
                batteryProgressFill.style.background = "linear-gradient(90deg, #ef4444, #f59e0b)";
            } else {
                batteryProgressFill.style.background = "linear-gradient(90deg, #10b981, #00f0ff)";
            }
        }

        // Volume
        if (data.volume) {
            const vol = data.volume.level;
            const muted = data.volume.muted;
            volumeSlider.value = vol;
            hudVolumeValue.textContent = muted ? "Muted (0%)" : `${vol}%`;
            muteToggleBtn.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
        }

        // Specs
        if (data.specs && specCpu) {
            specCpu.textContent = data.specs;
        }
    }

    // Poll status every 5 seconds
    setInterval(fetchSystemStatus, 5000);
    fetchSystemStatus();

    // ==============================================================================
    // 3. Hands-Free Voice Engine (Web Speech API + 2s Silence Detection)
    // ==============================================================================
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            voiceHeading.textContent = "Web Speech Not Supported";
            voiceSubtext.textContent = "Please use Google Chrome, Safari, or Brave for browser microphone input.";
            return null;
        }

        const recognizer = new SpeechRecognition();
        recognizer.continuous = true;
        recognizer.interimResults = true;
        recognizer.lang = "en-US";

        recognizer.onstart = () => {
            isVoiceActive = true;
            voiceStage.classList.add("listening");
            inlineMicBtn.classList.add("active-listening");
            voiceToggleNavBtn.querySelector(".voice-mode-label").textContent = "Voice ON";
            voiceHeading.textContent = "🎙️ Listening Continuously...";
            voiceSubtext.textContent = "Speak commands anytime. When you stop, it pauses for 2 seconds and auto-executes!";
            pauseMeterWrap.style.display = "block";
            resetPauseMeter();
        };

        recognizer.onresult = (event) => {
            let interim = "";
            let finalTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const chunk = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += chunk + " ";
                } else {
                    interim += chunk;
                }
            }

            const currentText = (finalTranscript || interim).trim();
            if (currentText) {
                accumulatedTranscript = currentText;
                chatInput.value = accumulatedTranscript;
                voiceHeading.textContent = `🗣️ Hearing: "${accumulatedTranscript}"`;
                triggerTwoSecondPauseCountdown();
            }
        };

        recognizer.onerror = (event) => {
            if (event.error !== "no-speech") {
                console.warn("Speech recognition error:", event.error);
            }
        };

        recognizer.onend = () => {
            // If user wanted voice mode to stay on, auto-restart continuous listening
            if (isVoiceActive) {
                try {
                    recognizer.start();
                } catch (e) {
                    // Ignore restart race condition
                }
            } else {
                setVoiceInactiveUI();
            }
        };

        return recognizer;
    }

    function triggerTwoSecondPauseCountdown() {
        // Clear previous timers
        clearTimeout(pauseTimer);
        clearInterval(pauseCountdownInterval);

        let progress = 0;
        pauseBarFill.style.width = "0%";

        const startTime = Date.now();
        const duration = 2000; // Exact 2.0s pause threshold as requested!

        pauseCountdownInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            progress = Math.min(100, (elapsed / duration) * 100);
            pauseBarFill.style.width = `${progress}%`;
            if (progress >= 100) {
                clearInterval(pauseCountdownInterval);
            }
        }, 50);

        pauseTimer = setTimeout(() => {
            clearInterval(pauseCountdownInterval);
            pauseBarFill.style.width = "100%";
            if (accumulatedTranscript.trim()) {
                const queryToSend = accumulatedTranscript.trim();
                accumulatedTranscript = "";
                chatInput.value = "";
                voiceHeading.textContent = "⚡ Executing Command...";
                executeChatCommand(queryToSend);
                setTimeout(resetPauseMeter, 800);
            }
        }, duration);
    }

    function resetPauseMeter() {
        pauseBarFill.style.width = "0%";
    }

    function toggleVoiceMode() {
        if (!speechRecognition) {
            speechRecognition = initSpeechRecognition();
        }
        if (!speechRecognition) return;

        if (isVoiceActive) {
            isVoiceActive = false;
            speechRecognition.stop();
            setVoiceInactiveUI();
        } else {
            isVoiceActive = true;
            try {
                speechRecognition.start();
            } catch (e) {
                // If already started
            }
        }
    }

    function setVoiceInactiveUI() {
        voiceStage.classList.remove("listening");
        inlineMicBtn.classList.remove("active-listening");
        voiceToggleNavBtn.querySelector(".voice-mode-label").textContent = "Voice Off";
        voiceHeading.textContent = "Hands-Free Voice Engine";
        voiceSubtext.textContent = "Click the microphone or speak commands. Pauses for 2 seconds after speech and auto-executes!";
        pauseMeterWrap.style.display = "none";
        clearTimeout(pauseTimer);
        clearInterval(pauseCountdownInterval);
    }

    bigMicBtn.addEventListener("click", toggleVoiceMode);
    inlineMicBtn.addEventListener("click", toggleVoiceMode);
    voiceToggleNavBtn.addEventListener("click", toggleVoiceMode);

    // Keyboard Shortcut: Press 'M' to toggle voice mode
    document.addEventListener("keydown", (e) => {
        if (e.key === "m" || e.key === "M") {
            if (document.activeElement !== chatInput && document.activeElement !== songSearchInput) {
                e.preventDefault();
                toggleVoiceMode();
            }
        }
    });

    // ==============================================================================
    // 4. Chat & Agent Execution Loop
    // ==============================================================================
    async function executeChatCommand(query) {
        if (!query || !query.trim()) return;
        const cleanQuery = query.trim();

        // 1. Render User Message
        appendMessage("user", cleanQuery);

        // 2. Render Agent Thinking Placeholder
        const thinkingBubble = appendThinkingPlaceholder();
        chatInput.value = "";

        try {
            const startTime = performance.now();
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: cleanQuery })
            });

            const elapsed = Math.round(performance.now() - startTime);

            if (!res.ok) {
                const errData = await res.json().catch(() => ({ detail: "Server execution error" }));
                thinkingBubble.remove();
                appendErrorMessage(errData.detail || "Error communicating with AI Agent.");
                return;
            }

            const data = await res.json();
            thinkingBubble.remove();
            appendAgentMessage(data, elapsed);

            // Refresh system telemetry after action
            fetchSystemStatus();

        } catch (err) {
            thinkingBubble.remove();
            appendErrorMessage(`Connection failed: ${err.message}`);
        }
    }

    function appendMessage(sender, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-message ${sender}-message`;
        msgDiv.innerHTML = `
            <div class="message-avatar">${sender === "user" ? "👤" : ""}</div>
            <div class="message-body">
                <div class="message-meta">
                    <span class="sender-name">${sender === "user" ? "You" : "macOS AI Agent"}</span>
                </div>
                <div class="message-content">
                    <p>${escapeHtml(text)}</p>
                </div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendThinkingPlaceholder() {
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-message agent-message thinking-bubble";
        msgDiv.innerHTML = `
            <div class="message-avatar"></div>
            <div class="message-body">
                <div class="message-meta">
                    <span class="sender-name">macOS AI Agent</span>
                    <span class="badge badge-instant">Processing...</span>
                </div>
                <div class="message-content">
                    <span class="thinking-dots">🧠 Coordinating system tools & reasoning...</span>
                </div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv;
    }

    function appendAgentMessage(data, elapsedMs) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-message agent-message";

        const isDirect = data.is_direct;
        const badgeClass = isDirect ? "badge-instant" : "badge-gemini";
        const badgeText = isDirect ? `⚡ Instant Router (${elapsedMs}ms)` : `🧠 Gemini Flash (${elapsedMs}ms)`;

        // Parse markdown content
        let htmlBody = "";
        try {
            if (window.marked) {
                htmlBody = marked.parse(data.summary || "");
            } else {
                htmlBody = `<p>${escapeHtml(data.summary || "")}</p>`;
            }
        } catch (e) {
            htmlBody = `<p>${escapeHtml(data.summary || "")}</p>`;
        }

        // Build sources & tools chips
        let chipsHtml = "";
        if (data.tools_used && data.tools_used.length > 0) {
            chipsHtml += `<span class="meta-chip">⚙️ ${data.tools_used.join(", ")}</span>`;
        }
        if (data.sources && data.sources.length > 0) {
            chipsHtml += `<span class="meta-chip">🔗 ${data.sources.join(", ")}</span>`;
        }

        msgDiv.innerHTML = `
            <div class="message-avatar"></div>
            <div class="message-body">
                <div class="message-meta">
                    <span class="sender-name">macOS AI Agent</span>
                    <span class="badge ${badgeClass}">${badgeText}</span>
                </div>
                <div class="message-content">
                    ${htmlBody}
                    ${chipsHtml ? `<div class="message-footer-meta">${chipsHtml}</div>` : ""}
                </div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendErrorMessage(errText) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "chat-message agent-message";
        msgDiv.innerHTML = `
            <div class="message-avatar">⚠️</div>
            <div class="message-body">
                <div class="message-meta">
                    <span class="sender-name">System Notice</span>
                </div>
                <div class="message-content" style="border-color: rgba(239, 68, 68, 0.4); color: #fca5a5;">
                    <p>${escapeHtml(errText)}</p>
                </div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    // Input handlers
    sendBtn.addEventListener("click", () => {
        const q = chatInput.value.trim();
        if (q) executeChatCommand(q);
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const q = chatInput.value.trim();
            if (q) executeChatCommand(q);
        }
    });

    // Clear Conversation Memory
    clearMemoryBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/clear", { method: "POST" });
            chatStream.innerHTML = "";
            logActivity("Memory Cleared", "Multi-turn conversation context reset.");
            appendMessage("agent", "Conversation memory has been cleared. How can I assist you next?");
        } catch (e) {
            console.error(e);
        }
    });

    // Prompt Chips in Welcome Message
    document.addEventListener("click", (e) => {
        const chip = e.target.closest(".prompt-chip");
        if (chip) {
            const query = chip.getAttribute("data-query");
            if (query) executeChatCommand(query);
        }
    });

    // ==============================================================================
    // 5. Volume Slider & Quick Actions
    // ==============================================================================
    volumeSlider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10);
        hudVolumeValue.textContent = `${val}%`;
    });

    volumeSlider.addEventListener("change", async (e) => {
        const val = parseInt(e.target.value, 10);
        try {
            await fetch("/api/action/volume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ level: val })
            });
            logActivity("Volume Adjusted", `Speaker level set to ${val}%.`);
        } catch (err) {
            console.error(err);
        }
    });

    volUpBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/action/volume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ direction: "up" })
            });
            const data = await res.json();
            if (data.level) {
                volumeSlider.value = data.level;
                hudVolumeValue.textContent = `${data.level}%`;
                logActivity("Volume +15%", `Output level increased to ${data.level}%.`);
            }
        } catch (e) {}
    });

    volDownBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/action/volume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ direction: "down" })
            });
            const data = await res.json();
            if (data.level) {
                volumeSlider.value = data.level;
                hudVolumeValue.textContent = `${data.level}%`;
                logActivity("Volume -15%", `Output level decreased to ${data.level}%.`);
            }
        } catch (e) {}
    });

    muteToggleBtn.addEventListener("click", async () => {
        const isMuted = muteToggleBtn.textContent.includes("Unmute");
        const action = isMuted ? "unmute" : "mute";
        try {
            await fetch("/api/action/quick", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
            muteToggleBtn.textContent = isMuted ? "🔇 Mute" : "🔊 Unmute";
            fetchSystemStatus();
            logActivity(isMuted ? "Audio Unmuted" : "Audio Muted", "macOS sound output updated.");
        } catch (e) {}
    });

    // Quick System Tiles
    document.getElementById("tileScreenshot").addEventListener("click", () => triggerQuickAction("screenshot", "Screenshot captured to Desktop."));
    document.getElementById("tileDarkMode").addEventListener("click", () => triggerQuickAction("dark_mode", "Toggled macOS Appearance."));
    document.getElementById("tileLock").addEventListener("click", () => triggerQuickAction("lock_screen", "macOS display locked."));
    document.getElementById("tileSpecs").addEventListener("click", () => executeChatCommand("specs"));

    async function triggerQuickAction(actionName, logMsg) {
        try {
            const res = await fetch("/api/action/quick", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: actionName })
            });
            const data = await res.json();
            logActivity(logMsg, data.message || "Completed.");
        } catch (e) {
            console.error(e);
        }
    }

    // ==============================================================================
    // 6. Smart Music Player Controls
    // ==============================================================================
    mediaRandomBtn.addEventListener("click", async () => {
        trackTitle.textContent = "Selecting Random Hit...";
        trackArtist.textContent = "Querying YouTube Top Result";
        vinylRecord.classList.add("spinning");
        try {
            const res = await fetch("/api/action/media", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "random" })
            });
            const data = await res.json();
            trackTitle.textContent = "Now Playing Top Hit";
            trackArtist.textContent = data.message || "YouTube Music";
            logActivity("🎵 Random Hit Playing", data.message);
        } catch (e) {
            vinylRecord.classList.remove("spinning");
        }
    });

    mediaPlayPauseBtn.addEventListener("click", async () => {
        isPlayingMedia = !isPlayingMedia;
        mediaPlayPauseBtn.textContent = isPlayingMedia ? "⏸" : "▶";
        if (isPlayingMedia) {
            vinylRecord.classList.add("spinning");
        } else {
            vinylRecord.classList.remove("spinning");
        }
        await sendMediaAction(isPlayingMedia ? "play" : "pause");
    });

    mediaNextBtn.addEventListener("click", () => sendMediaAction("next"));
    mediaPrevBtn.addEventListener("click", () => sendMediaAction("previous"));

    async function sendMediaAction(action) {
        try {
            const res = await fetch("/api/action/media", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
            const data = await res.json();
            logActivity(`Media: ${action}`, data.message);
        } catch (e) {}
    }

    // Song Search Input
    songPlaySubmitBtn.addEventListener("click", playCustomSong);
    songSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") playCustomSong();
    });

    async function playCustomSong() {
        const song = songSearchInput.value.trim();
        if (!song) return;
        trackTitle.textContent = song;
        trackArtist.textContent = "Searching #1 YouTube result...";
        vinylRecord.classList.add("spinning");
        try {
            const res = await fetch("/api/action/media", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "song", song: song })
            });
            const data = await res.json();
            trackTitle.textContent = song;
            trackArtist.textContent = "Playing on YouTube";
            songSearchInput.value = "";
            logActivity(`Song Playing: ${song}`, data.message);
        } catch (e) {
            vinylRecord.classList.remove("spinning");
        }
    }

    // ==============================================================================
    // 7. App Launcher Pills
    // ==============================================================================
    document.querySelectorAll(".app-pill").forEach((pill) => {
        pill.addEventListener("click", async () => {
            const app = pill.getAttribute("data-app");
            if (!app) return;
            try {
                const res = await fetch("/api/action/app", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ action: "open", app_name: app })
                });
                const data = await res.json();
                logActivity(`Launched ${app}`, data.message);
            } catch (e) {}
        });
    });

    // Helper Utilities
    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function jsonParseSafe(str) {
        try { return JSON.parse(str); } catch (e) { return null; }
    }

    // Start WebSocket
    initWebSocket();
});
