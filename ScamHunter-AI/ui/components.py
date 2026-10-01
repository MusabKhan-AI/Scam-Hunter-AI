from __future__ import annotations

import html

import streamlit as st


def hero(compact: bool = False):
    cls = "hero hero-compact" if compact else "hero"
    st.markdown(
        f"""
        <div class="{cls}">
            <div class="hero-logo">🛡️</div>

            <div class="hero-title">
                ScamHunter <span>AI</span>
            </div>

            <div class="hero-description">
                Investigate suspicious messages, offers, links and online
                claims with AI-powered evidence analysis.
            </div>

            <div class="hero-badge">
                <span class="hero-badge-dot">●</span>
                Evidence-first AI investigation
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def source_card(item):
    """
    Render a safe, theme-aware evidence citation card.

    Supports:
    - Knowledge Base evidence
    - Web evidence
    - Flat evidence dictionaries
    - Nested source dictionaries
    """

    if not isinstance(item, dict):
        item = {"text": str(item)}

    source = item.get("source")

    if isinstance(source, dict):
        merged = dict(source)

        for key, value in item.items():
            if key != "source" and value not in (None, ""):
                merged[key] = value

        item = merged

    source_type = (
        item.get("source_type")
        or item.get("type")
        or ""
    ).lower()

    # ---------------------------------------------------------
    # KNOWLEDGE BASE SOURCE
    # ---------------------------------------------------------

    if source_type == "knowledge_base":
        filename = (
            item.get("filename")
            or item.get("title")
            or "Knowledge Base Document"
        )

        page = item.get("page")
        section = item.get("section") or "General"
        chunk_id = item.get("chunk_id")

        details = []

        if page is not None:
            details.append(f"Page {page}")

        if section:
            details.append(section)

        if chunk_id:
            details.append(chunk_id)

        detail_text = " · ".join(details)

        excerpt = (
            item.get("excerpt")
            or item.get("text")
            or item.get("content")
            or ""
        )

        filename = html.escape(str(filename))
        detail_text = html.escape(str(detail_text))
        excerpt = html.escape(str(excerpt)).replace("\n", "<br>")

        st.markdown(
            f"""
            <div class="source-card source-card-kb">

                <div class="source-header">
                    <div class="source-icon">📄</div>

                    <div class="source-heading">
                        <div class="source-title">
                            {filename}
                        </div>

                        <div class="source-meta">
                            {detail_text}
                        </div>
                    </div>
                </div>

                <div class="source-excerpt">
                    {excerpt}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    # ---------------------------------------------------------
    # WEB SOURCE
    # ---------------------------------------------------------

    title = (
        item.get("title")
        or item.get("url")
        or "Web source"
    )

    url = item.get("url", "")

    excerpt = (
        item.get("snippet")
        or item.get("excerpt")
        or item.get("text")
        or item.get("content")
        or ""
    )

    title = html.escape(str(title))
    url = html.escape(str(url))
    excerpt = html.escape(str(excerpt)).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class="source-card source-card-web">

            <div class="source-header">
                <div class="source-icon">🌐</div>

                <div class="source-heading">
                    <div class="source-title">
                        {title}
                    </div>

                    <div class="source-meta">
                        {url}
                    </div>
                </div>
            </div>

            <div class="source-excerpt">
                {excerpt}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str):
    """Render a small uppercase section label."""

    safe_text = html.escape(str(text))

    st.markdown(
        f'<div class="section-label">{safe_text}</div>',
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str, icon: str = "ℹ️"):
    """Render a generic theme-aware information card."""

    safe_title = html.escape(str(title))
    safe_body = html.escape(str(body)).replace("\n", "<br>")
    safe_icon = html.escape(str(icon))

    st.markdown(
        f"""
        <div class="info-card">

            <div class="info-card-title">
                <span class="info-card-icon">{safe_icon}</span>
                <span>{safe_title}</span>
            </div>

            <div class="info-card-body">
                {safe_body}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Dashboard strip, instant scan, example prompts, setup banner
# ---------------------------------------------------------------------------

LEVEL_COLORS = {
    "high": "#EF4444",
    "medium": "#F59E0B",
    "low": "#64748B",
    "none": "#64748B",
}

LEVEL_TITLES = {
    "high": "Strong warning signals",
    "medium": "Several warning signals",
    "low": "A few warning signals",
    "none": "No automatic warning signals",
}

EXAMPLES = [
    (
        "Bank alert",
        "Dear customer, your HBL account will be suspended within 24 hours. "
        "Verify now at http://hbl-secure-login.xyz/verify and send the OTP you receive.",
    ),
    (
        "Job offer",
        "Earn Rs 5,000 daily working from home. No experience needed. Pay a Rs 1,500 "
        "registration fee and join our WhatsApp group to start today.",
    ),
    (
        "Parcel and romance",
        "I am a doctor working abroad and I want to send you a gift parcel. "
        "You only need to pay the customs fee with gift cards. Please keep this between us.",
    ),
    (
        "Crypto investment",
        "Our trading group guarantees 3% daily profit with zero risk. "
        "Deposit USDT to the wallet we send you and withdraw anytime.",
    ),
]


def stat_strip(items):
    """Quiet row of status cards. items = [(label, value), ...]"""
    cards = "".join(
        '<div class="stat-card">'
        f'<div class="stat-value">{html.escape(str(value))}</div>'
        f'<div class="stat-label">{html.escape(str(label))}</div>'
        "</div>"
        for label, value in items
    )
    st.markdown(f'<div class="stat-grid">{cards}</div>', unsafe_allow_html=True)


def setup_banner(has_groq: bool, has_gemini: bool):
    """Show a clear message when no AI key is configured."""
    if has_groq or has_gemini:
        return
    st.markdown(
        '<div class="banner-warn">'
        "<strong>No AI key found.</strong> The instant scan still works, but full "
        "investigations need a key. Add <code>GROQ_API_KEY</code> or "
        "<code>GEMINI_API_KEY</code> under <em>Manage app → Settings → Secrets</em> "
        "(Streamlit Cloud) or in <code>.streamlit/secrets.toml</code> (local)."
        "</div>",
        unsafe_allow_html=True,
    )


def example_prompts():
    """Render example buttons. Returns the example text if one was clicked."""
    from ui.compat import stretch

    st.markdown(
        '<div class="example-title">Try an example</div>',
        unsafe_allow_html=True,
    )
    columns = st.columns(len(EXAMPLES), gap="small")
    for column, (label, text) in zip(columns, EXAMPLES):
        with column:
            if st.button(label, key=f"example_{label}", **stretch(st.button)):
                return text
    return None


def risk_meter(scan: dict):
    """Instant scan summary: severity bar plus the evidence it is based on."""
    level = scan.get("level", "none")
    color = LEVEL_COLORS.get(level, LEVEL_COLORS["none"])
    score = int(scan.get("score", 0))
    title = LEVEL_TITLES.get(level, "")
    headline = html.escape(scan.get("headline") or title)

    chips = []
    for flag in scan.get("flags", [])[:8]:
        weight = flag.get("weight", 0)
        sev = "high" if weight >= 18 else "med" if weight >= 12 else "low"
        chips.append(
            f'<span class="chip chip-{sev}">{html.escape(flag["label"])}</span>'
        )
    for url in scan.get("urls", []):
        if url.get("risk", 0) > 0:
            sev = "high" if url["risk"] >= 28 else "med"
            chips.append(
                f'<span class="chip chip-{sev}">Risky link: {html.escape(url.get("host", ""))}</span>'
            )

    st.markdown(
        '<div class="risk-meter" style="--meter-color:' + color + ';">'
        '<div class="risk-meter-head">'
        '<div class="risk-meter-title">Instant scan</div>'
        f'<div class="risk-meter-score">{score}<span>/100</span></div>'
        "</div>"
        f'<div class="risk-meter-bar"><div class="risk-meter-fill" style="width:{max(score, 3)}%"></div></div>'
        f'<div class="risk-meter-sub">{headline}. Pattern matching only, not proof.</div>'
        f'<div class="chip-row">{"".join(chips)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def scan_details(scan: dict):
    """Expandable details: quoted evidence, link checks and extracted items."""
    with st.expander("Instant scan details", expanded=False):
        flags = scan.get("flags", [])
        if flags:
            rows = "".join(
                '<div class="scan-row">'
                f'<div class="scan-label">{html.escape(f["label"])}</div>'
                f'<div class="scan-quote">“{html.escape(f["evidence"])}”</div>'
                f'<div class="scan-advice">{html.escape(f["advice"])}</div>'
                "</div>"
                for f in flags
            )
            st.markdown(rows, unsafe_allow_html=True)

        urls = scan.get("urls", [])
        if urls:
            rows = "".join(
                '<div class="scan-row">'
                f'<div class="scan-label">{html.escape(u["url"])}</div>'
                + (
                    "".join(
                        f'<div class="scan-advice">• {html.escape(x)}</div>'
                        for x in u["flags"]
                    )
                    or '<div class="scan-advice">No automatic flags. Still check it before opening.</div>'
                )
                + "</div>"
                for u in urls
            )
            st.markdown(rows, unsafe_allow_html=True)

        extracted = []
        if scan.get("phones"):
            extracted.append("Phone numbers: " + ", ".join(scan["phones"]))
        if scan.get("emails"):
            extracted.append("E-mail addresses: " + ", ".join(scan["emails"]))
        if scan.get("wallets"):
            extracted.append(
                "Crypto wallets: "
                + ", ".join(f'{w["chain"]} {w["address"]}' for w in scan["wallets"])
            )
        if scan.get("amounts"):
            extracted.append("Amounts mentioned: " + ", ".join(scan["amounts"]))
        if extracted:
            st.caption("  \n".join(extracted))
