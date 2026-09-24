"""
auth.py - Authentication Module for Schema-Agnostic Natural Language Data Analyst
Gates access behind an email/password login screen with email validation.
Designed for Streamlit Community Cloud deployment.
"""

import re
import streamlit as st

# Hardcoded demo credentials dictionary for access gating
CREDENTIALS_DB = {
    "analyst@demo.com": "analyst123",
    "demo@gmail.com": "demo123",
    "judge@hackathon.com": "hth2024",
    "admin@company.com": "admin123",
    "user@gmail.com": "password123",
}

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def is_valid_email(email: str) -> bool:
    """Validates that input string conforms to standard email format."""
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))


def verify_credentials(email: str, password: str) -> tuple[bool, str]:
    """
    Validates email format and verifies against hardcoded credential dictionary.
    Returns (is_success, error_or_success_message).
    """
    cleaned_email = email.strip().lower()
    if not cleaned_email or not password:
        return False, "Please enter both email and password."

    if not is_valid_email(cleaned_email):
        return False, "Invalid email format. Please enter a valid email (e.g. name@gmail.com)."

    if cleaned_email not in CREDENTIALS_DB:
        return False, "Account not found. Please check your email or use a demo account."

    if CREDENTIALS_DB[cleaned_email] != password:
        return False, "Incorrect password. Please try again."

    return True, "Login successful."


def login_panel() -> bool:
    """
    Renders a Gmail-style email/password authentication screen.
    Returns True if user is authenticated, False otherwise.
    """
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    if st.session_state.authenticated:
        return True

    # Styling for the login card
    st.markdown("""
    <style>
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 16px;
            padding: 2.2rem 2rem 1.8rem 2rem;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
        }
        .login-title {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.3rem;
            text-align: center;
        }
        .login-subtitle {
            font-size: 0.95rem;
            color: #888888;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .login-badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            background-color: rgba(59, 130, 246, 0.15);
            color: #3b82f6;
            border: 1px solid rgba(59, 130, 246, 0.3);
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <div class="login-badge">🛡️ SECURE ACCESS GATE</div>
            <div class="login-title">📊 Schema-Agnostic Analyst</div>
            <div class="login-subtitle">Sign in to query spreadsheets in plain English without hallucinated numbers.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("##### 👤 Sign In")
            email_input = st.text_input(
                "Email address",
                placeholder="analyst@demo.com or name@gmail.com",
                help="Enter your registered email address"
            )
            password_input = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Enter your password"
            )

            submit = st.form_submit_button("Sign In →", use_container_width=True)

            if submit:
                success, msg = verify_credentials(email_input, password_input)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email_input.strip().lower()
                    st.success("✅ Authentication successful! Loading workspace...")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        # Demo Credentials Helper for judges and testing
        with st.expander("🔑 Quick Demo Credentials (For Evaluation & Review)"):
            st.markdown("""
            Use any of the following pre-configured credentials to sign in:
            - **Analyst:** `analyst@demo.com` • Password: `analyst123`
            - **Gmail:** `demo@gmail.com` • Password: `demo123`
            - **Judge:** `judge@hackathon.com` • Password: `hth2024`
            - **Admin:** `admin@company.com` • Password: `admin123`
            """)

        st.caption("🔒 **Streamlit Cloud Gate**: Validates email format against local credential store. In enterprise production, this gates via Google Cloud OAuth / SSO.")

    return False


def logout_button():
    """
    Renders user profile badge and Sign Out button in the sidebar.
    """
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            user_email = st.session_state.get("user_email", "analyst@demo.com")
            st.markdown(
                f"""
                <div style="padding: 0.6rem 0.8rem; background: rgba(59, 130, 246, 0.08); border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2); margin-bottom: 0.8rem;">
                    <div style="font-size: 0.72rem; color: #888888; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Signed In As</div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #3b82f6; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">👤 {user_email}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("🚪 Sign Out", key="auth_logout_btn", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.rerun()
            st.markdown("---")
