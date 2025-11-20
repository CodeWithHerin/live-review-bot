import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="✨")

# --- HIDE STREAMLIT BRANDING ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- LOGIN LOGIC ---
def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not found or password incorrect")
        return False
    else:
        # Password correct
        return True

# --- MAIN APP FLOW ---
if check_password():
    # --- API KEY LOGIC (Only runs if logged in) ---
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # --- THE TOOL UI ---
    st.title("✨ AI Review Responder")
    st.success(f"✅ Logged in as: {st.session_state['username']}")
    st.write("Paste the customer review below.")

    user_review = st.text_area("Customer Review:", height=150, placeholder="Paste the review here...")
    tone = st.selectbox("Choose Tone:", ["Professional", "Friendly", "Apologetic", "Short & Sweet"])

    if st.button("Generate Reply"):
        if not user_review:
            st.warning("Please paste a review first.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                You are a helpful hotel manager.
                Write a reply to this review: "{user_review}"
                Tone: {tone}.
                Result should be ready to copy-paste. No quotes.
                """
                
                with st.spinner("Drafting response..."):
                    response = model.generate_content(prompt)
                    st.markdown("### Copy this reply:")
                    st.code(response.text, language=None)
            
            except Exception as e:
                st.error(f"Error: {str(e)}")