#!/usr/bin/env python3
"""Update AI Literacy index.html with onboarding, search, persona filter, reading path."""

import re

with open('/Users/flare/Desktop/CLAUDE/claude main/tools/ai-literacy/index.html', 'r') as f:
    html = f.read()

# ============================================================
# 1. ADD CSS before </style>
# ============================================================
new_css = """
        /* Onboarding Overlay */
        .onboarding-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 1;
            transition: opacity 0.5s ease;
        }
        .onboarding-overlay.fade-out {
            opacity: 0;
            pointer-events: none;
        }
        .onboarding-card {
            background: var(--card);
            border: 1px solid #333;
            border-radius: 16px;
            padding: 36px 32px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            animation: onboardSlideUp 0.4s ease;
        }
        @keyframes onboardSlideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .onboarding-card h2 {
            font-size: 22px;
            margin-bottom: 8px;
        }
        .onboarding-card p {
            color: var(--text-dim);
            font-size: 14px;
            margin-bottom: 24px;
        }
        .persona-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }
        .persona-btn {
            background: var(--bg);
            border: 1px solid #333;
            border-radius: 12px;
            padding: 18px 12px;
            cursor: pointer;
            transition: all 0.25s;
            color: var(--text);
            font-size: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .persona-btn .persona-icon { font-size: 28px; }
        .persona-btn .persona-label { font-weight: 600; }
        .persona-btn .persona-desc { font-size: 11px; color: var(--text-dim); }
        .persona-btn:hover {
            border-color: var(--accent);
            box-shadow: 0 0 20px rgba(99,102,241,0.25);
            transform: translateY(-2px);
        }
        .persona-btn.selected {
            border-color: var(--accent);
            background: rgba(99,102,241,0.15);
        }
        .onboard-step { display: none; }
        .onboard-step.active { display: block; }
        .onboard-input {
            width: 100%;
            padding: 10px 14px;
            background: var(--bg);
            border: 1px solid #333;
            border-radius: 8px;
            color: var(--text);
            font-size: 14px;
            outline: none;
            margin-bottom: 10px;
        }
        .onboard-input:focus { border-color: var(--accent); }
        .onboard-input-label {
            font-size: 12px;
            color: var(--text-dim);
            text-align: left;
            display: block;
            margin-bottom: 4px;
        }
        .onboard-submit {
            width: 100%;
            padding: 14px;
            background: var(--accent);
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
            transition: all 0.2s;
        }
        .onboard-submit:hover { background: var(--accent-light); }
        .onboard-skip {
            display: inline-block;
            margin-top: 10px;
            font-size: 12px;
            color: var(--text-dim);
            cursor: pointer;
            border: none;
            background: none;
            text-decoration: underline;
        }
        .onboard-skip:hover { color: var(--text); }

        /* Search Bar */
        .search-wrap {
            margin-bottom: 16px;
        }
        .search-input {
            width: 100%;
            padding: 10px 16px;
            background: var(--card);
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            color: var(--text);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .search-input:focus { border-color: var(--accent); }
        .search-input::placeholder { color: #555; }
        .search-no-results {
            text-align: center;
            color: var(--text-dim);
            padding: 32px 0;
            font-size: 14px;
            display: none;
        }

        /* Persona Indicator */
        .persona-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            font-size: 13px;
            color: var(--text-dim);
        }
        .persona-indicator .pi-label {
            background: rgba(99,102,241,0.15);
            padding: 4px 12px;
            border-radius: 12px;
            color: var(--accent-light);
            font-weight: 500;
        }
        .persona-indicator .pi-change {
            background: none;
            border: 1px solid #333;
            padding: 3px 10px;
            border-radius: 10px;
            color: var(--text-dim);
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .persona-indicator .pi-change:hover {
            border-color: var(--accent);
            color: var(--text);
        }

        /* Persona section dividers */
        .persona-divider {
            font-size: 13px;
            color: var(--text-dim);
            padding: 12px 0 8px;
            display: none;
        }
        .persona-divider.visible { display: block; }

        /* Card persona dimming */
        .card.persona-dimmed {
            opacity: 0.3;
            order: 999;
        }
        .cards-wrapper {
            display: flex;
            flex-direction: column;
        }

        /* Reading Path */
        .reading-path {
            background: var(--card);
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .reading-path-header {
            padding: 14px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.2s;
        }
        .reading-path-header:hover { background: var(--card-hover); }
        .reading-path-body {
            display: none;
            padding: 0 20px 16px;
        }
        .reading-path.expanded .reading-path-body { display: block; }
        .reading-path-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #222;
            cursor: pointer;
            transition: color 0.2s;
            font-size: 13px;
            color: var(--text-dim);
        }
        .reading-path-item:last-child { border-bottom: none; }
        .reading-path-item:hover { color: var(--accent-light); }
        .reading-path-num {
            width: 24px;
            height: 24px;
            background: rgba(99,102,241,0.15);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            color: var(--accent-light);
            font-weight: 600;
            flex-shrink: 0;
        }

        @media (max-width: 600px) {
            .persona-grid { grid-template-columns: 1fr; }
            .onboarding-card { padding: 24px 18px; }
        }
"""
html = html.replace('    </style>', new_css + '    </style>')

# ============================================================
# 2. ADD Onboarding Overlay HTML after <body>
# ============================================================
onboarding_html = """
<!-- Onboarding Overlay -->
<div class="onboarding-overlay" id="onboardingOverlay" style="display:none;">
    <div class="onboarding-card">
        <div class="onboard-step active" id="onboardStep1">
            <h2>Chào bạn! 👋</h2>
            <p>Bạn thuộc nhóm nào?</p>
            <div class="persona-grid">
                <button class="persona-btn" data-persona="producer" onclick="selectOnboardPersona(this,'producer')">
                    <span class="persona-icon">🎬</span>
                    <span class="persona-label">Producer</span>
                    <span class="persona-desc">Người làm sản xuất</span>
                </button>
                <button class="persona-btn" data-persona="creative" onclick="selectOnboardPersona(this,'creative')">
                    <span class="persona-icon">🎨</span>
                    <span class="persona-label">Creative</span>
                    <span class="persona-desc">Sáng tạo / thiết kế</span>
                </button>
                <button class="persona-btn" data-persona="manager" onclick="selectOnboardPersona(this,'manager')">
                    <span class="persona-icon">📊</span>
                    <span class="persona-label">Manager</span>
                    <span class="persona-desc">Quản lý / điều hành</span>
                </button>
                <button class="persona-btn" data-persona="curious" onclick="selectOnboardPersona(this,'curious')">
                    <span class="persona-icon">🔍</span>
                    <span class="persona-label">Tò mò về AI</span>
                    <span class="persona-desc">Mới tìm hiểu</span>
                </button>
            </div>
        </div>
        <div class="onboard-step" id="onboardStep2">
            <h2>Gần xong rồi! 🎉</h2>
            <p>Để lại thông tin nếu muốn nhận update mới nhất từ AI Studio</p>
            <label class="onboard-input-label">Tên</label>
            <input class="onboard-input" type="text" id="onboardName" placeholder="VD: Minh">
            <label class="onboard-input-label">Email</label>
            <input class="onboard-input" type="email" id="onboardEmail" placeholder="email@company.com">
            <label class="onboard-input-label">Công ty <span style="color:#555">(không bắt buộc)</span></label>
            <input class="onboard-input" type="text" id="onboardCompany" placeholder="VD: Agency XYZ">
            <button class="onboard-submit" onclick="finishOnboarding()">Bắt đầu học →</button>
            <button class="onboard-skip" onclick="finishOnboarding()">Bỏ qua →</button>
        </div>
    </div>
</div>

"""
html = html.replace('<body>\n', '<body>\n' + onboarding_html)

# ============================================================
# 3. ADD Search Bar + Persona Indicator after </nav>
# ============================================================
search_persona_html = """
<!-- Persona Indicator -->
<div class="persona-indicator" id="personaIndicator" style="display:none;">
    <span>👤</span>
    <span class="pi-label" id="piLabel">Producer</span>
    <button class="pi-change" onclick="showOnboarding()">Đổi</button>
</div>

<!-- Search Bar -->
<div class="search-wrap">
    <input class="search-input" type="text" id="searchInput" placeholder="🔍 Tìm kiếm nội dung...">
</div>

"""
html = html.replace('</nav>\n', '</nav>\n' + search_persona_html)

# ============================================================
# 4. ADD Reading Path in Overview section (after section-desc)
# ============================================================
reading_path_html = """
    <!-- Suggested Reading Path -->
    <div class="reading-path" id="readingPath" style="display:none;">
        <div class="reading-path-header" onclick="this.parentElement.classList.toggle('expanded')">
            <span>📖 Lộ trình đề xuất</span>
            <span class="arrow">›</span>
        </div>
        <div class="reading-path-body" id="readingPathBody">
        </div>
    </div>

    <div class="persona-divider" id="personaMatchDivider">📌 Gợi ý cho bạn</div>

"""
# Insert after the overview section-desc paragraph
html = html.replace(
    '    <p class="section-desc">Bức tranh toàn cảnh: AI đang ở đâu, đang thay đổi thế giới ra sao, và ảnh hưởng trực tiếp đến ngành của bạn thế nào.</p>\n',
    '    <p class="section-desc">Bức tranh toàn cảnh: AI đang ở đâu, đang thay đổi thế giới ra sao, và ảnh hưởng trực tiếp đến ngành của bạn thế nào.</p>\n' + reading_path_html
)

# Add "other content" divider before closing each section (we'll handle via JS)

# ============================================================
# 5. ADD data-persona to EVERY card
# ============================================================
persona_map = {
    'ai-now': 'producer,creative,manager,curious',
    'ai-jobs': 'producer,creative,manager,curious',
    'ai-production': 'producer,creative,manager,curious',
    'ai-business': 'manager,producer',
    'ai-agents-overview': 'manager,curious',
    'ai-seegroup': 'producer,creative,manager,curious',
    'ai-vision': 'producer,creative,manager,curious',
    'llm': 'producer,creative,manager,curious',
    'diffusion': 'curious,producer,creative',
    'transformer': 'curious',
    'training': 'curious,producer',
    'multimodal': 'curious,producer,creative',
    'tokens': 'curious,producer',
    'api': 'curious,manager',
    'opensource': 'curious',
    'i2i': 'producer,creative',
    'interpolation': 'producer,creative',
    'consistency': 'producer,creative',
    'cfg': 'producer',
    'video-models': 'producer,creative',
    'prompt-eng': 'producer,creative',
    'brand-ai-policy': 'manager,producer',
    'agent-concept': 'producer,creative,manager,curious',
    'mcp': 'producer,curious',
    'coding-agents': 'curious,manager',
    'hermes': 'curious',
    'agentic-workflow': 'producer,manager',
    'rag': 'curious,manager',
    'local-vs-cloud': 'manager,curious',
    'gpu': 'curious',
    'docker': 'curious',
    'gateway': 'curious',
    'ollama': 'curious',
    'version-control': 'curious',
    'latent-space': 'curious,producer',
    'video-gen-deep': 'producer,creative',
    'lora-deep': 'curious,producer',
    'attention-deep': 'curious,producer,creative',
    'multimodal-deep': 'curious,producer',
    'orchestration': 'manager,producer',
    'benchmarks': 'manager,curious',
    'tokenizer': 'curious,manager',
    'thinking-modes': 'curious,manager',
    'context-deep': 'curious,producer',
    'breaking-changes': 'curious',
    'vision-resolution': 'producer,curious',
    'model-choosing': 'manager,producer',
}

for card_id, personas in persona_map.items():
    html = html.replace(
        f'data-id="{card_id}"',
        f'data-id="{card_id}" data-persona="{personas}"'
    )

# ============================================================
# 6. WRAP card containers in each section with cards-wrapper + add dividers
# ============================================================
# We'll handle persona dividers via JS instead of static HTML, simpler.

# ============================================================
# 7. ADD new JS before </script>
# ============================================================
new_js = """
    // ============================================================
    // ONBOARDING
    // ============================================================
    let currentPersona = null;
    const personaNames = {
        producer: '🎬 Producer',
        creative: '🎨 Creative',
        manager: '📊 Manager',
        curious: '🔍 Tò mò về AI'
    };
    const readingPaths = {
        producer: [
            { id: 'ai-production', title: 'AI trong Production — Cuộc cách mạng đang diễn ra' },
            { id: 'prompt-eng', title: 'Prompt Engineering — Nguyên tắc core' },
            { id: 'video-models', title: 'AI Video Models — Cách chúng hoạt động' },
            { id: 'consistency', title: 'Character Consistency & Identity' },
            { id: 'i2i', title: 'txt2img vs img2img vs img2vid' },
            { id: 'interpolation', title: 'Frame Interpolation & Motion' },
            { id: 'brand-ai-policy', title: 'Tại sao một số Brand chưa cho dùng AI?' }
        ],
        creative: [
            { id: 'ai-production', title: 'AI trong Production — Cuộc cách mạng đang diễn ra' },
            { id: 'consistency', title: 'Character Consistency & Identity' },
            { id: 'video-models', title: 'AI Video Models — Cách chúng hoạt động' },
            { id: 'prompt-eng', title: 'Prompt Engineering — Nguyên tắc core' },
            { id: 'diffusion', title: 'Diffusion Model' },
            { id: 'video-gen-deep', title: 'Video Generation — Tại sao khó hơn Image' },
            { id: 'attention-deep', title: 'Attention Mechanism — Tại sao prompt structure quan trọng' }
        ],
        manager: [
            { id: 'ai-business', title: 'AI trong Quản trị — CEO/EP cần biết gì' },
            { id: 'ai-jobs', title: 'AI thay đổi ngành nghề — Ai mất việc, ai lên giá' },
            { id: 'ai-agents-overview', title: 'AI Agents — Bản đồ thị trường 2026' },
            { id: 'brand-ai-policy', title: 'Tại sao một số Brand chưa cho dùng AI?' },
            { id: 'model-choosing', title: 'Cách chọn model — Ma trận quyết định' },
            { id: 'agentic-workflow', title: 'Agentic Workflow Patterns' },
            { id: 'orchestration', title: 'Agent Orchestration — Điều phối nhiều AI' }
        ],
        curious: [
            { id: 'ai-now', title: 'AI đang ở đâu — Bức tranh 2025-2026' },
            { id: 'llm', title: 'LLM — Large Language Model' },
            { id: 'diffusion', title: 'Diffusion Model' },
            { id: 'tokens', title: 'Tokens & Context Window' },
            { id: 'multimodal', title: 'Multimodal AI' },
            { id: 'training', title: 'Training vs Fine-tuning vs Inference' },
            { id: 'agent-concept', title: 'AI Agent — Khái niệm cơ bản' }
        ]
    };

    function initOnboarding() {
        const overlay = document.getElementById('onboardingOverlay');
        if (!localStorage.getItem('ai-literacy-onboarded')) {
            overlay.style.display = 'flex';
        } else {
            overlay.style.display = 'none';
            // Restore persona
            try {
                const profile = JSON.parse(localStorage.getItem('ai-literacy-profile') || '{}');
                if (profile.persona) {
                    currentPersona = profile.persona;
                    applyPersona(currentPersona);
                }
            } catch(e) {}
        }
    }

    function selectOnboardPersona(btn, persona) {
        document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        currentPersona = persona;
        // Go to step 2 after short delay
        setTimeout(() => {
            document.getElementById('onboardStep1').classList.remove('active');
            document.getElementById('onboardStep2').classList.add('active');
        }, 300);
    }

    function finishOnboarding() {
        const name = document.getElementById('onboardName').value.trim();
        const email = document.getElementById('onboardEmail').value.trim();
        const company = document.getElementById('onboardCompany').value.trim();

        const profileData = {
            persona: currentPersona,
            name: name || '',
            email: email || '',
            company: company || '',
            timestamp: new Date().toISOString()
        };

        // Save to localStorage
        localStorage.setItem('ai-literacy-onboarded', 'true');
        localStorage.setItem('ai-literacy-profile', JSON.stringify(profileData));

        // Send to GA
        if (typeof gtag !== 'undefined') {
            gtag('event', 'onboarding_complete', {
                persona: currentPersona,
                has_email: !!email,
                event_category: 'onboarding'
            });
        }

        // Send to Google Sheets webhook
        try {
            fetch('GOOGLE_SHEETS_WEBHOOK_URL', {
                method: 'POST',
                mode: 'no-cors',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            }).catch(() => {});
        } catch(e) {}

        // Fade out overlay
        const overlay = document.getElementById('onboardingOverlay');
        overlay.classList.add('fade-out');
        setTimeout(() => { overlay.style.display = 'none'; }, 500);

        applyPersona(currentPersona);
    }

    function showOnboarding() {
        const overlay = document.getElementById('onboardingOverlay');
        overlay.classList.remove('fade-out');
        overlay.style.display = 'flex';
        document.getElementById('onboardStep1').classList.add('active');
        document.getElementById('onboardStep2').classList.remove('active');
    }

    // ============================================================
    // PERSONA FILTER
    // ============================================================
    function applyPersona(persona) {
        if (!persona) return;
        currentPersona = persona;

        // Update indicator
        const indicator = document.getElementById('personaIndicator');
        indicator.style.display = 'flex';
        document.getElementById('piLabel').textContent = personaNames[persona] || persona;

        // Update reading path
        updateReadingPath(persona);

        // Apply persona filter to cards
        document.querySelectorAll('.card[data-persona]').forEach(card => {
            const cardPersonas = (card.getAttribute('data-persona') || '').split(',');
            if (cardPersonas.includes(persona)) {
                card.classList.remove('persona-dimmed');
                card.style.order = '';
            } else {
                card.classList.add('persona-dimmed');
                card.style.order = '999';
            }
        });

        // Show match/other dividers per section
        document.querySelectorAll('.section').forEach(section => {
            // Remove old dividers
            section.querySelectorAll('.persona-divider-dynamic').forEach(d => d.remove());

            const cards = section.querySelectorAll('.card[data-persona]');
            if (cards.length === 0) return;

            let hasMatch = false, hasDimmed = false;
            cards.forEach(c => {
                const cp = (c.getAttribute('data-persona') || '').split(',');
                if (cp.includes(persona)) hasMatch = true;
                else hasDimmed = true;
            });

            if (hasMatch && hasDimmed) {
                // Add "Gợi ý cho bạn" before first matching card
                const firstCard = section.querySelector('.card[data-persona]:not(.persona-dimmed)');
                if (firstCard) {
                    const matchDiv = document.createElement('div');
                    matchDiv.className = 'persona-divider-dynamic persona-divider visible';
                    matchDiv.textContent = '📌 Gợi ý cho bạn';
                    firstCard.parentNode.insertBefore(matchDiv, firstCard);
                }
                // Add "Nội dung khác" before first dimmed card
                const firstDimmed = section.querySelector('.card.persona-dimmed');
                if (firstDimmed) {
                    const otherDiv = document.createElement('div');
                    otherDiv.className = 'persona-divider-dynamic persona-divider visible';
                    otherDiv.style.order = '998';
                    otherDiv.textContent = '📚 Nội dung khác';
                    firstDimmed.parentNode.insertBefore(otherDiv, firstDimmed);
                }
            }
        });

        // Wrap card parents for flex ordering
        document.querySelectorAll('.section').forEach(section => {
            // If not already wrapped
            if (!section.querySelector('.cards-wrapper')) {
                const cards = Array.from(section.querySelectorAll('.card, .persona-divider-dynamic, .reading-path, #personaMatchDivider'));
                if (cards.length > 0) {
                    // We won't wrap - just ensure parent is flex
                    // Cards are direct children of section - set section to flex column
                }
            }
        });
    }

    // ============================================================
    // READING PATH
    // ============================================================
    function updateReadingPath(persona) {
        const pathContainer = document.getElementById('readingPath');
        const pathBody = document.getElementById('readingPathBody');
        const items = readingPaths[persona];

        if (!items || items.length === 0) {
            pathContainer.style.display = 'none';
            return;
        }

        pathContainer.style.display = 'block';
        pathBody.innerHTML = '';

        items.forEach((item, idx) => {
            const div = document.createElement('div');
            div.className = 'reading-path-item';
            div.innerHTML = '<span class="reading-path-num">' + (idx + 1) + '</span><span>' + item.title + '</span>';
            div.addEventListener('click', () => {
                navigateToCard(item.id);
            });
            pathBody.appendChild(div);
        });
    }

    function navigateToCard(cardId) {
        // Find the card
        const card = document.querySelector('.card[data-id="' + cardId + '"]');
        if (!card) return;

        // Find which section it's in
        const section = card.closest('.section');
        if (!section) return;

        // Activate that section's nav button
        const sectionId = section.id.replace('sec-', '');
        document.querySelectorAll('nav button').forEach(b => {
            b.classList.remove('active');
            if (b.dataset.section === sectionId) b.classList.add('active');
        });
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        section.classList.add('active');

        // Expand the card
        card.classList.add('expanded');

        // Scroll to it
        setTimeout(() => {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    // ============================================================
    // SEARCH
    // ============================================================
    let searchTimeout = null;
    const searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performSearch, 300);
    });

    function performSearch() {
        const query = searchInput.value.trim().toLowerCase();
        const activeSection = document.querySelector('.section.active');
        if (!activeSection) return;

        const cards = activeSection.querySelectorAll('.card');
        let noResults = activeSection.querySelector('.search-no-results');

        if (!noResults) {
            noResults = document.createElement('div');
            noResults.className = 'search-no-results';
            noResults.textContent = 'Không tìm thấy nội dung phù hợp';
            activeSection.appendChild(noResults);
        }

        if (!query) {
            cards.forEach(c => c.style.display = '');
            noResults.style.display = 'none';
            // Re-show dividers
            activeSection.querySelectorAll('.persona-divider-dynamic').forEach(d => d.style.display = '');
            return;
        }

        let found = 0;
        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            if (text.includes(query)) {
                card.style.display = '';
                found++;
            } else {
                card.style.display = 'none';
            }
        });

        // Hide dividers during search
        activeSection.querySelectorAll('.persona-divider-dynamic').forEach(d => d.style.display = 'none');

        noResults.style.display = found === 0 ? 'block' : 'none';
    }

    // Re-run search when switching tabs
    const origNavButtons = document.querySelectorAll('nav button');
    origNavButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setTimeout(() => {
                if (searchInput.value.trim()) performSearch();
            }, 50);
        });
    });

    // ============================================================
    // INIT
    // ============================================================
    initOnboarding();

    // Make sections flex for ordering
    document.querySelectorAll('.section').forEach(s => {
        s.style.display === 'block' || s.classList.contains('active') ? null : null;
        // Add flex container style for card ordering
        const style = document.createElement('style');
        style.textContent = '.section.active { display: flex; flex-direction: column; }';
        if (!document.getElementById('persona-flex-style')) {
            style.id = 'persona-flex-style';
            document.head.appendChild(style);
        }
    });
"""

html = html.replace('    // Init\n    restoreState();\n</script>', '    // Init\n    restoreState();\n' + new_js + '\n</script>')

# ============================================================
# 8. Fix the section active display CSS
# ============================================================
# The existing CSS has `.section.active { display: block; }` which conflicts with flex
# We need sections to be flex when active for ordering to work
# But we need to be careful - the original toggle just sets active class
# Let's update the section active CSS
html = html.replace(
    '.section.active { display: block; }',
    '.section.active { display: flex; flex-direction: column; }'
)

# Write the updated file
with open('/Users/flare/Desktop/CLAUDE/claude main/tools/ai-literacy/index.html', 'w') as f:
    f.write(html)

print("Done! File updated successfully.")
print(f"File size: {len(html)} bytes, {html.count(chr(10))} lines")
