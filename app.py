import streamlit as st
import google.generativeai as genai
import pandas as pd
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

# --- AGENCY MEMORY (The "Database") ---
# EDIT THIS: Add your paying clients here to save time!
CLIENT_PRESETS = {
    "Manual Entry": {
        "name": "", 
        "location": "", 
        "services": "", 
        "owner": ""
    },
    "Ocean Paradise Goa": {
        "name": "Ocean Paradise Resort", 
        "location": "Calangute Beach, Goa", 
        "services": "Infinity Pool, Beach Bar, Free Breakfast", 
        "owner": "Mr. Verma"
    },
    "Mountain View Manali": {
        "name": "Mountain View Cottage", 
        "location": "Old Manali", 
        "services": "Bonfire, Trekking Guide, Home-cooked Food", 
        "owner": "Simran"
    }
}

# --- SESSION STATE SETUP ---
if "history" not in st.session_state:
    st.session_state["history"] = []

if "total_usage" not in st.session_state:
    st.session_state["total_usage"] = 0

# --- LOGIN SYSTEM ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.header("💎 Agency Login")
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
    
    # 1. API KEY
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # 2. SIDEBAR (Agency Mode)
    with st.sidebar:
        st.success(f"👤 Agent: {st.session_state['user']}")
        st.divider()
        
        st.subheader("📂 Load Client Profile")
        # Dropdown to pick a client
        selected_client = st.selectbox("Select Client:", list(CLIENT_PRESETS.keys()))
        
        # Get data for that client
        client_data = CLIENT_PRESETS[selected_client]

        st.subheader("🏨 Business Details")
        # We use key= to allowing manual editing even after loading a preset
        hotel_name = st.text_input("Business Name", value=client_data["name"])
        location = st.text_input("Location", value=client_data["location"])
        services = st.text_input("Key Services/Amenities", value=client_data["services"])
        manager_name = st.text_input("Sign-off Name", value=client_data["owner"])
        
        st.divider()
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 3. MAIN INTERFACE
    st.title("💎 Agency Review Responder")
    st.markdown(f"Drafting replies for: **{hotel_name if hotel_name else 'Unknown Business'}**")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_review = st.text_area("Paste Customer Review:", height=200)
    
    with col2:
        tone = st.selectbox("Tone:", ["Professional", "Warm & Personal", "Apologetic", "Short"])
        lang = st.selectbox("Language:", ["English", "Hindi", "Gujarati", "Hinglish"])

    if st.button("✨ Generate Magic Reply"):
        if not user_review:
            st.warning("Please paste a review first.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # HYPER-PERSONALIZED PROMPT
                prompt = f"""
                You are the owner/manager of {hotel_name}.
                Your name is {manager_name}.
                Your business is located in {location}.
                You offer these services: {services}.

                Write a reply to this review: "{user_review}"
                
                Tone: {tone}
                Language: {lang}
                
                Rules:
                1. If the review is positive, mention our location ({location}) and invite them to try our services ({services}).
                2. If negative, be polite and address the issue.
                3. Sign off with {hotel_name} and {manager_name}.
                4. Output ONLY the reply text.
                """
                
                with st.spinner("Consulting the AI..."):
                    response = model.generate_content(prompt)
                    reply_text = response.text
                    
                    st.success("Draft Ready (Click top-right of box to Copy):")
                    st.code(reply_text, language=None)
                    
                    # HISTORY LOGGING
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state["history"].append({
                        "Client": hotel_name,
                        "Date": timestamp,
                        "Review": user_review[:50] + "...",
                        "Reply": reply_text,
                        "Agent": st.session_state["user"]
                    })

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 4. HISTORY & EXPORT
    st.divider()
    st.subheader("📜 Session History")
    if len(st.session_state["history"]) > 0:
        df = pd.DataFrame(st.session_state["history"])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Report (CSV)", data=csv, file_name='agency_report.csv', mime='text/csv')