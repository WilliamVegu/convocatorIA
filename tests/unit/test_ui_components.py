"""Unit tests for UI session management, RBAC enforcement, and theme components."""
import time
import pytest
import streamlit as st

from src.ui.session import (
    init_session,
    login_user,
    logout,
    can_write,
    is_head_of_ta,
    has_role,
    get_current_user,
    check_session_timeout,
)
from src.ui.theme import render_badge, TCS_COLORS, get_logo_base64


def test_session_initialization_defaults():
    # Clear session state for test
    st.session_state.clear()
    init_session()

    assert st.session_state["is_authenticated"] is False
    assert st.session_state["user_id"] is None
    assert st.session_state["rol"] is None
    assert can_write() is False
    assert is_head_of_ta() is False


def test_session_login_and_rbac_roles():
    st.session_state.clear()
    login_user(
        user_id="usr-rec-001",
        email="recruiter@tcs.com",
        nombres_completos="Recruiter Demo",
        rol="Senior_Technical_Recruiter",
    )

    user = get_current_user()
    assert user is not None
    assert user["email"] == "recruiter@tcs.com"
    assert can_write() is True
    assert is_head_of_ta() is False
    assert has_role(["Senior_Technical_Recruiter", "Head_of_Talent_Acquisition"]) is True
    assert has_role(["Compliance_Officer"]) is False


def test_compliance_officer_is_read_only():
    st.session_state.clear()
    login_user(
        user_id="usr-comp-001",
        email="compliance@tcs.com",
        nombres_completos="Compliance Demo",
        rol="Compliance_Officer",
    )

    assert can_write() is False
    assert is_head_of_ta() is False


def test_head_of_ta_permissions():
    st.session_state.clear()
    login_user(
        user_id="usr-admin-001",
        email="admin.ta@tcs.com",
        nombres_completos="Head TA Demo",
        rol="Head_of_Talent_Acquisition",
    )

    assert can_write() is True
    assert is_head_of_ta() is True


def test_session_logout():
    st.session_state.clear()
    login_user(
        user_id="usr-001",
        email="user@tcs.com",
        nombres_completos="Test User",
        rol="Senior_Technical_Recruiter",
    )
    assert get_current_user() is not None

    logout(reason="Prueba unitaria de logout")
    assert get_current_user() is None
    assert st.session_state["is_authenticated"] is False


def test_session_timeout_detection():
    st.session_state.clear()
    login_user(
        user_id="usr-001",
        email="user@tcs.com",
        nombres_completos="Test User",
        rol="Senior_Technical_Recruiter",
    )
    # Simulate past activity > 30 min (1801 seconds ago)
    st.session_state["last_activity_time"] = time.time() - 1900

    is_active = check_session_timeout()
    assert is_active is False
    assert st.session_state["is_authenticated"] is False


def test_theme_badge_rendering():
    badge_html = render_badge("Activo", "green")
    assert 'class="tcs-badge tcs-badge-green"' in badge_html
    assert "Activo" in badge_html

    badge_purple = render_badge("Boomerang", "purple")
    assert 'class="tcs-badge tcs-badge-purple"' in badge_purple
    assert "Boomerang" in badge_purple


def test_theme_colors_integrity():
    assert TCS_COLORS["deep_navy"] == "#0A192F"
    assert TCS_COLORS["green"] == "#2ECC71"
    assert TCS_COLORS["red"] == "#E74C3C"
    assert TCS_COLORS["purple_boomerang"] == "#9B59B6"
