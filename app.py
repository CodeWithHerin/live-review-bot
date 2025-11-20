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

    # Initialize session state for login if it doesn't exist
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If not logged in, show the login form
    if not st.session_state["password_correct"]:
        st.header("🔒 Private Access")
        st.write("Please log in to use the AI Tool.")
        
        # Inputs
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # THE LOGIN BUTTON
        if st.button("Log In"):
            # Check against Secrets
            if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                st.session_state["password_correct"] = True
                st.session_state["user"] = username
                st.success("Login successful! Loading...")
                time.sleep(1)
                st.rerun()  # Force reload to show the app
            else:
                st.error("😕 User not found or password incorrect")
        return False
    
    # If logged in, return True
    else:
        return True

# --- MAIN APP FLOW ---
if check_password():
    # --- API KEY LOGIC (Only runs if logged in) ---
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # --- THE TOOL UI ---
    # Logout Button in Sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state['user']}**")
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.title("✨ AI Review Responder")
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