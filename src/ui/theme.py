"""Corporate theme, CSS styling, and visual components for TCS ATS."""
from __future__ import annotations

import base64
import os
from typing import Optional
import streamlit as st

TCS_COLORS = {
    "deep_navy": "#0A192F",
    "navy_surface": "#1C2541",
    "vibrant_blue": "#0076CE",
    "cyan_accent": "#00B4D8",
    "card_bg": "#1C2541",
    "border": "#334155",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    # Traffic light semaphores
    "green": "#2ECC71",
    "yellow": "#F1C40F",
    "red": "#E74C3C",
    "purple_boomerang": "#9B59B6",
}


def get_logo_base64() -> str:
    """Return base64-encoded string of TCS logo for embedding."""
    logo_path = os.path.join(os.getcwd(), "assets", "tcs_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def apply_theme() -> None:
    """Inject corporate CSS stylesheet into Streamlit."""
    custom_css = """
    <style>
        /* Typography & Smooth Rendering */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Card & Metric container styling */
        div[data-testid="stMetric"] {
            background-color: #1C2541 !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            padding: 14px 18px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.2px;
        }
        div[data-testid="stMetricValue"] {
            color: #38BDF8 !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
        }

        /* Buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #0076CE 0%, #00B4D8 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.25rem !important;
            box-shadow: 0 2px 6px rgba(0, 180, 216, 0.2) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #005FA3 0%, #0096B4 100%) !important;
            box-shadow: 0 4px 14px rgba(0, 180, 216, 0.4) !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }
        div.stButton > button:active {
            transform: translateY(0);
        }
        div.stButton > button:disabled {
            background: #334155 !important;
            color: #64748B !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }

        /* Form Inputs & Selects */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            background-color: #162032 !important;
            color: #F8FAFC !important;
            border: 1px solid #334155 !important;
            border-radius: 6px !important;
            font-size: 0.92rem !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: #00B4D8 !important;
            box-shadow: 0 0 0 2px rgba(0, 180, 216, 0.25) !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
            padding: 8px 16px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #00B4D8 !important;
            border-bottom-color: #00B4D8 !important;
            font-weight: 700 !important;
        }

        /* Dataframe / Tables */
        div[data-testid="stDataFrame"] {
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        /* Callouts / Alerts */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
            background-color: #162032 !important;
            color: #F8FAFC !important;
        }

        /* Corporate Badges */
        .tcs-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .tcs-badge-purple { background-color: rgba(168, 85, 247, 0.25); color: #C084FC; border: 1px solid #A855F7; }
        .tcs-badge-green  { background-color: rgba(34, 197, 94, 0.25);  color: #4ADE80; border: 1px solid #22C55E; }
        .tcs-badge-yellow { background-color: rgba(234, 179, 8, 0.25);  color: #FACC15; border: 1px solid #EAB308; }
        .tcs-badge-red    { background-color: rgba(239, 68, 68, 0.25);   color: #F87171; border: 1px solid #EF4444; }
        .tcs-badge-blue   { background-color: rgba(56, 189, 248, 0.25);  color: #38BDF8; border: 1px solid #38BDF8; }
        .tcs-badge-gray   { background-color: rgba(148, 163, 184, 0.25); color: #CBD5E1; border: 1px solid #64748B; }

        /* Custom Modern Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0B132B;
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00B4D8;
        }
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
    """Render top branding bar with official TCS logo, application title and active user info."""
    logo_path = os.path.join(os.getcwd(), "assets", "tcs_logo.png")

    c_logo, c_title, c_user = st.columns([1.5, 4.5, 3.5])

    with c_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=160)

    with c_title:
        st.markdown(
            "<h2 style='margin: 0; padding: 0; color: #F8FAFC; font-weight: 700;'>ATS TCS Perú "
            "<span style='font-size: 0.75rem; background: #00B4D8; color: #0B132B; padding: 2px 8px; "
            "border-radius: 4px; font-weight: 700; vertical-align: middle;'>CORE MVP</span></h2>"
            "<p style='margin: 2px 0 0 0; font-size: 0.82rem; color: #94A3B8; font-weight: 500;'>"
            "Talent Acquisition Engine • Candidate Lifecycle Management</p>",
            unsafe_allow_html=True,
        )

    with c_user:
        if current_user:
            rol = current_user.get("rol", "Compliance_Officer").replace("_", " ")
            email = current_user.get("email", "")
            nombre = current_user.get("nombres_completos", "")
            st.markdown(
                f"<div style='text-align: right; padding-top: 4px;'>"
                f"<div style='font-weight: 600; color: #F8FAFC; font-size: 0.92rem;'>👤 {nombre}</div>"
                f"<div style='font-size: 0.78rem; color: #00B4D8; margin-top: 2px;'>"
                f"<b>{rol}</b> &nbsp;|&nbsp; <span style='color: #94A3B8;'>{email}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 8px 0 16px 0; border: none; border-top: 1px solid #334155;'/>", unsafe_allow_html=True)


def render_pipeline_stepper(
    current_step: int,
    candidate_name: Optional[str] = None,
    role_or_rgs: Optional[str] = None,
) -> None:
    """Render a visual 5-step recruitment progress stepper banner."""
    steps = [
        (1, "Demanda RGS", "📝"),
        (2, "Ficha & CV", "📋"),
        (3, "Screening HITL", "📞"),
        (4, "Simulación CTC", "💰"),
        (5, "Terna / One-Pager", "📄"),
    ]

    items_html = []
    for step_num, step_label, icon in steps:
        if step_num < current_step:
            badge_style = "background: #065F46; color: #34D399; border: 1px solid #059669;"
            icon_disp = "✔"
            status_text = "Completado"
        elif step_num == current_step:
            badge_style = "background: #0369A1; color: #E0F2FE; border: 2px solid #38BDF8; font-weight: 700; box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);"
            icon_disp = icon
            status_text = "En curso"
        else:
            badge_style = "background: #1E293B; color: #64748B; border: 1px solid #334155;"
            icon_disp = icon
            status_text = "Pendiente"

        items_html.append(
            f'<div style="flex: 1; margin: 0 4px; padding: 6px 10px; border-radius: 8px; {badge_style} text-align: center; font-size: 12px;">'
            f'<div style="font-size: 13px; margin-bottom: 2px;">{icon_disp} <b>{step_label}</b></div>'
            f'<div style="font-size: 10px; text-transform: uppercase; opacity: 0.9;">{status_text}</div>'
            f'</div>'
        )

    cand_banner = ""
    if candidate_name or role_or_rgs:
        cand_str = f"👤 <b>{candidate_name}</b>" if candidate_name else ""
        role_str = f"📌 Rol: <b>{role_or_rgs}</b>" if role_or_rgs else ""
        sep = " &nbsp;|&nbsp; " if cand_str and role_str else ""
        cand_banner = (
            f'<div style="font-size: 12px; color: #94A3B8; margin-bottom: 6px; padding: 4px 10px; background: rgba(15, 23, 42, 0.6); border-radius: 6px;">'
            f'{cand_str}{sep}{role_str}'
            f'</div>'
        )

    stepper_html = (
        f'<div style="background: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; margin-bottom: 16px;">'
        f'{cand_banner}'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        + "".join(items_html)
        + '</div></div>'
    )
    st.markdown(stepper_html, unsafe_allow_html=True)

