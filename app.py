import streamlit as st
import google.generativeai as genai
import pandas as pd # Used for Excel/CSV handling
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="wide")

# --- HIDE BRANDING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE SETUP (The Brain) ---
# We use this to remember data while the app runs
if "history" not in st.session_state:
    st.session_state["history"] = [] # List to store past replies

if "total_usage" not in st.session_state:
    st.session_state["total_usage"] = 0

# --- LOGIN SYSTEM ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        # Centered Login Box
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.header("💎 Private Access")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Log In"):
                if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                    st.session_state["password_correct"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("⛔ Access Denied")
        return False
    return True

# --- MAIN APP ---
if check_password():
    
    # 1. API KEY SETUP
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # 2. SIDEBAR (Brand Voice & Admin)
    with st.sidebar:
        st.write(f"👤 User: **{st.session_state['user']}**")
        
        st.divider()
        st.subheader("🏨 Brand Settings")
        hotel_name = st.text_input("Hotel Name", placeholder="e.g., Ocean View Resort")
        manager_name = st.text_input("Sign-off Name", placeholder="e.g., Rahul, Manager")
        
        st.divider()
        # ADMIN PANEL (Only visible if you log in as 'admin')
        if st.session_state["user"] == "admin":
            st.error("🕵️ ADMIN PANEL")
            st.write(f"Total Replies Generated: {st.session_state['total_usage']}")
            
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 3. MAIN INTERFACE
    st.title("💎 AI Review Responder Pro")
    st.markdown("Generate professional replies in seconds. **History is saved below.**")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_review = st.text_area("Paste Customer Review:", height=150)
    
    with col2:
        tone = st.selectbox("Reply Tone:", ["Professional", "Warm & Friendly", "Apologetic", "Short"])
        lang = st.selectbox("Language:", ["English", "Hindi", "Gujarati", "Hinglish"])

    if st.button("✨ Generate Magic Reply"):
        if not user_review:
            st.warning("Please paste a review first.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # ADVANCED PROMPT with Brand Memory
                prompt = f"""
                You are the manager of {hotel_name if hotel_name else 'a hotel'}.
                Your name is {manager_name if manager_name else 'The Management'}.
                
                Write a reply to this review: "{user_review}"
                
                Tone: {tone}
                Language: {lang}
                Structure:
                1. Thank them.
                2. Address specific points in the review.
                3. Sign off with {hotel_name} and {manager_name}.
                """
                
                with st.spinner("Thinking..."):
                    response = model.generate_content(prompt)
                    reply_text = response.text
                    
                    # Show Result
                    st.success("Draft Ready:")
                    st.code(reply_text, language=None)
                    
                    # SAVE TO HISTORY
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state["history"].append({
                        "Date": timestamp,
                        "User": st.session_state["user"],
                        "Review": user_review[:50] + "...", # First 50 chars
                        "Reply": reply_text,
                        "Tone": tone
                    })
                    st.session_state["total_usage"] += 1

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 4. HISTORY & EXPORT SECTION
    st.divider()
    st.subheader("📜 Recent Activity History")
    
    if len(st.session_state["history"]) > 0:
        # Convert list to a Pandas Dataframe (Table)
        df = pd.DataFrame(st.session_state["history"])
        
        # Show the table
        st.dataframe(df, use_container_width=True)
        
        # Create CSV for download
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download History (CSV)",
            data=csv,
            file_name='review_history.csv',
            mime='text/csv',
        )
    else:
        st.info("No replies generated in this session yet.")