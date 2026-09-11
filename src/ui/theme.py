"""Corporate theme, CSS styling, and visual components for TCS ATS."""
from __future__ import annotations

import base64
import os
from typing import Optional
import streamlit as st

TCS_COLORS = {
    "deep_navy": "#0A192F",
    "navy_surface": "#001E3C",
    "vibrant_blue": "#0076CE",
    "cyan_accent": "#00B4D8",
    "magenta_accent": "#E91E63",
    "bg_neutral": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "border": "#E2E8F0",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    # Traffic light semaphores
    "green": "#2ECC71",
    "yellow": "#F1C40F",
    "red": "#E74C3C",
    "purple_boomerang": "#9B59B6",
}


def get_logo_base64() -> Optional[str]:
    """Load assets/tcs_logo.png as base64 string for direct HTML embedding."""
    logo_path = os.path.join(os.getcwd(), "assets", "tcs_logo.png")
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None
    return None


def apply_theme() -> None:
    """Inject corporate CSS stylesheet into Streamlit."""
    custom_css = f"""
    <style>
        /* Main page background */
        .stApp {{
            background-color: {TCS_COLORS["bg_neutral"]};
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            color: {TCS_COLORS["text_primary"]};
        }}

        /* Header Bar */
        .tcs-header-container {{
            background: linear-gradient(135deg, {TCS_COLORS["deep_navy"]} 0%, {TCS_COLORS["navy_surface"]} 100%);
            padding: 1rem 1.75rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #FFFFFF;
            box-shadow: 0 4px 14px rgba(10, 25, 47, 0.15);
        }}

        .tcs-header-title {{
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .tcs-header-subtitle {{
            font-size: 0.85rem;
            color: {TCS_COLORS["cyan_accent"]};
            margin-top: 4px;
            font-weight: 500;
        }}

        /* Cards and Containers */
        .tcs-card {{
            background-color: {TCS_COLORS["card_bg"]};
            border: 1px solid {TCS_COLORS["border"]};
            border-radius: 10px;
            padding: 1.25rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            margin-bottom: 1rem;
        }}

        /* Buttons */
        .stButton>button {{
            background-color: {TCS_COLORS["vibrant_blue"]};
            color: #FFFFFF;
            border-radius: 6px;
            font-weight: 600;
            border: none;
            padding: 0.5rem 1.25rem;
            transition: all 0.2s ease-in-out;
        }}
        .stButton>button:hover {{
            background-color: #005FA3;
            box-shadow: 0 4px 12px rgba(0, 118, 206, 0.25);
            color: #FFFFFF;
        }}

        /* Secondary & Danger buttons */
        .stButton>button:disabled {{
            background-color: #CBD5E1 !important;
            color: #94A3B8 !important;
            cursor: not-allowed;
        }}

        /* Metric cards */
        div[data-testid="stMetricValue"] {{
            color: {TCS_COLORS["deep_navy"]};
            font-weight: 700;
        }}

        /* Badges */
        .tcs-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .tcs-badge-purple {{
            background-color: #F3E8FF;
            color: #7E22CE;
            border: 1px solid #D8B4FE;
        }}
        .tcs-badge-green {{
            background-color: #DCFCE7;
            color: #15803D;
            border: 1px solid #86EFAC;
        }}
        .tcs-badge-yellow {{
            background-color: #FEF9C3;
            color: #A16207;
            border: 1px solid #FDE047;
        }}
        .tcs-badge-red {{
            background-color: #FEE2E2;
            color: #B91C1C;
            border: 1px solid #FCA5A5;
        }}
        .tcs-badge-blue {{
            background-color: #E0F2FE;
            color: #0369A1;
            border: 1px solid #7DD3FC;
        }}
        .tcs-badge-gray {{
            background-color: #F1F5F9;
            color: #475569;
            border: 1px solid #CBD5E1;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_badge(label: str, badge_type: str = "blue") -> str:
    """Return HTML string for corporate status badge."""
    valid_types = ["blue", "green", "yellow", "red", "purple", "gray"]
    t = badge_type if badge_type in valid_types else "blue"
    return f'<span class="tcs-badge tcs-badge-{t}">{label}</span>'


def render_header(
    current_user: Optional[dict] = None,
    on_logout_callback=None,
) -> None:
    """Render top branding bar with logo, user info and logout button."""
    logo_b64 = get_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 38px; margin-right: 12px; vertical-align: middle; filter: brightness(0) invert(1);" />'

    user_info_html = ""
    role_badge = ""
    if current_user:
        rol = current_user.get("rol", "Compliance_Officer")
        rol_display = rol.replace("_", " ")
        badge_style = "purple" if "Head" in rol else ("blue" if "Recruiter" in rol else ("yellow" if "Coordinator" in rol else "gray"))
        role_badge = render_badge(rol_display, badge_style)
        user_info_html = f"""
        <div style="text-align: right;">
            <div style="font-weight: 600; font-size: 0.9rem; color: #FFFFFF;">{current_user.get('nombres_completos', '')}</div>
            <div style="font-size: 0.75rem; color: #94A3B8;">{current_user.get('email', '')} &nbsp;|&nbsp; {role_badge}</div>
        </div>
        """

    header_html = f"""
    <div class="tcs-header-container">
        <div style="display: flex; align-items: center;">
            {logo_html}
            <div>
                <h1 class="tcs-header-title">ATS TCS Perú <span style="font-size: 0.75rem; background: rgba(0,180,216,0.2); border: 1px solid #00B4D8; color: #00B4D8; padding: 2px 8px; border-radius: 4px; font-weight: 600;">CORE MVP</span></h1>
                <div class="tcs-header-subtitle">Talent Acquisition Engine &amp; Candidate Lifecycle Management</div>
            </div>
        </div>
        <div>
            {user_info_html}
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
