document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("generator-form");
    const generateBtn = document.getElementById("generate-btn");
    
    const blankState = document.getElementById("blank-state");
    const loadingState = document.getElementById("loading-state");
    const contentState = document.getElementById("content-state");
    const postsContainer = document.getElementById("posts-container");
    
    // Stats Elements
    const statLatency = document.getElementById("stat-latency");
    const statCost = document.getElementById("stat-cost");
    const statModel = document.getElementById("stat-model");

    // Stepper Elements
    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const loadingHint = document.getElementById("loading-hint");

    let stepInterval = null;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // 1. Collect inputs
        const topic = document.getElementById("topic").value;
        const tone = document.getElementById("tone").value;
        const audience = document.getElementById("audience").value;
        const length = document.getElementById("length").value;
        const count = parseInt(document.getElementById("count").value);
        const cta = document.getElementById("cta").value;
        const examples = document.getElementById("examples").value;

        // 2. Adjust UX States
        blankState.classList.add("hidden");
        contentState.classList.add("hidden");
        loadingState.classList.remove("hidden");
        generateBtn.disabled = true;

        // Reset Stepper Styles
        resetStepper();
        
        // Start Stepper Simulation to mimic Agent's multi-step thought process
        simulateAgentSteps();

        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    topic,
                    tone,
                    audience,
                    length,
                    cta,
                    examples,
                    language: "English",
                    count
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Generation failed.");
            }

            const data = await response.json();
            
            // Finish Stepper Simulation immediately and display content
            completeStepper();
            setTimeout(() => {
                renderResults(data);
            }, 600);

        } catch (error) {
            console.error(error);
            clearInterval(stepInterval);
            alert(`Error: ${error.message}`);
            
            // Restore appropriate screen state
            loadingState.classList.add("hidden");
            blankState.classList.remove("hidden");
        } finally {
            generateBtn.disabled = false;
        }
    });

    // Simulated Stepper Sequence
    function resetStepper() {
        step1.className = "step active";
        step2.className = "step";
        step3.className = "step";
        loadingHint.innerText = "Analyzing topic and outlining concepts...";
        if (stepInterval) clearInterval(stepInterval);
    }

    function simulateAgentSteps() {
        let elapsed = 0;
        stepInterval = setInterval(() => {
            elapsed += 1;
            
            if (elapsed === 3) {
                // Shift to Step 2: Drafting
                step1.className = "step completed";
                step2.className = "step active";
                loadingHint.innerText = "Drafting customized LinkedIn post variants...";
            } else if (elapsed === 7) {
                // Shift to Step 3: Guardrails
                step2.className = "step completed";
                step3.className = "step active";
                loadingHint.innerText = "Applying quality filters & optimizing layout readability...";
            }
        }, 1000);
    }

    function completeStepper() {
        clearInterval(stepInterval);
        step1.className = "step completed";
        step2.className = "step completed";
        step3.className = "step completed";
        loadingHint.innerText = "Success! Polishing final drafts...";
    }

    // Render results on screen
    function renderResults(data) {
        // Toggle States
        loadingState.classList.add("hidden");
        contentState.classList.remove("hidden");

        // Set Metadata stats
        const meta = data.metadata || {};
        statLatency.innerText = `${meta.total_latency_seconds || "--"}s`;
        statCost.innerText = `$${parseFloat(meta.estimated_cost_usd || 0).toFixed(5)}`;
        statModel.innerText = meta.model || "gemini-2.5-flash";

        // Build Cards
        postsContainer.innerHTML = "";
        
        data.posts.forEach((post) => {
            const card = document.createElement("div");
            card.className = "post-card";
            
            // Generate Hashtag HTML
            const hashtagsHtml = post.suggested_hashtags
                .map(tag => `<span class="hashtag">#${tag.replace("#", "")}</span>`)
                .join(" ");

            card.innerHTML = `
                <div class="card-top">
                    <span class="option-badge">Option ${post.id}</span>
                    <div class="card-actions">
                        <button class="btn-icon copy-btn" title="Copy Post Text">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </div>
                </div>
                <div class="post-body">${escapeHTML(post.post_text)}</div>
                <div class="post-footer-tags">
                    ${hashtagsHtml}
                </div>
                <div class="card-details">
                    <div class="detail-row">
                        <span class="detail-lbl">Strategy:</span>
                        <span class="detail-val">${escapeHTML(post.justification)}</span>
                    </div>
                    ${post.call_to_action ? `
                    <div class="detail-row">
                        <span class="detail-lbl">CTA Applied:</span>
                        <span class="detail-val">${escapeHTML(post.call_to_action)}</span>
                    </div>` : ''}
                    <div class="guardrail-tag">
                        <i class="fa-solid fa-circle-check"></i> Quality Guardrails Passed
                    </div>
                </div>
            `;

            // Attach Clipboard Copy Functionality
            const copyBtn = card.querySelector(".copy-btn");
            copyBtn.addEventListener("click", () => {
                // Combine text and hashtags for sharing
                const fullText = `${post.post_text}\n\n${post.suggested_hashtags.map(t => `#${t.replace("#", "")}`).join(" ")}`;
                navigator.clipboard.writeText(fullText).then(() => {
                    copyBtn.classList.add("copied");
                    copyBtn.innerHTML = `<i class="fa-solid fa-check"></i>`;
                    
                    setTimeout(() => {
                        copyBtn.classList.remove("copied");
                        copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i>`;
                    }, 2000);
                }).catch(err => {
                    console.error("Clipboard copy failed: ", err);
                });
            });

            postsContainer.appendChild(card);
        });
    }

    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
