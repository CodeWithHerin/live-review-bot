import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="wide")

# --- PROFESSIONAL UI STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 1. TARGET ONLY THE PRIMARY BUTTON (The Generate Button) */
    div.stButton > button[kind="primary"] {
        background-color: #2E7D32; /* Professional Dark Green */
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1B5E20; /* Darker on hover */
    }

    /* 2. STYLE SECONDARY BUTTONS (Shorten, Empathy, History) */
    /* Makes them look cleaner and less distracting */
    div.stButton > button[kind="secondary"] {
        border: 1px solid #555; /* Subtle border */
        color: #eee;
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT PRESETS ---
CLIENT_PRESETS = {
    "Manual Entry": {"name": "", "location": "", "services": "", "owner": ""},
    "Ocean Paradise Goa": {
        "name": "Ocean Paradise Resort", 
        "location": "Calangute Beach, Goa", 
        "services": "Infinity Pool, Beach Bar", 
        "owner": "Mr. Verma"
    },
    "Mountain View Manali": {
        "name": "Mountain View Cottage", 
        "location": "Old Manali", 
        "services": "Bonfire, Trekking Guide", 
        "owner": "Simran"
    }
}

# --- SESSION STATE ---
if "history" not in st.session_state: st.session_state["history"] = []
if "current_reply" not in st.session_state: st.session_state["current_reply"] = ""
if "analysis" not in st.session_state: st.session_state["analysis"] = None

# --- AUTOFILL LOGIC ---
def update_client_info():
    selected = st.session_state["selected_client_dropdown"]
    data = CLIENT_PRESETS[selected]
    st.session_state["h_name"] = data["name"]
    st.session_state["loc"] = data["location"]
    st.session_state["srv"] = data["services"]
    st.session_state["mgr"] = data["owner"]

# --- LOGIN SYSTEM ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.header("💎 Smart Agency Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Log In", type="primary"): # Made this primary too for better UX
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
    
    # 1. SETUP
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # 2. SIDEBAR
    with st.sidebar:
        st.success(f"👤 Agent: {st.session_state['user']}")
        st.divider()
        
        st.subheader("📂 Client Profile")
        selected_client = st.selectbox(
            "Select Client:", 
            list(CLIENT_PRESETS.keys()), 
            key="selected_client_dropdown",
            on_change=update_client_info
        )

        hotel_name = st.text_input("Business Name", key="h_name")
        location = st.text_input("Location", key="loc")
        services = st.text_input("Services", key="srv")
        manager_name = st.text_input("Sign-off Name", key="mgr")
        
        st.divider()
        st.subheader("🎨 Brand Voice")
        brand_voice = st.text_area("Describe Tone", value="Professional, Warm, and Helpful")
        
        if hotel_name: st.caption("✅ Profile Active")
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 3. MAIN INTERFACE
    st.title("💎 Smart Review Responder")
    st.markdown(f"Drafting for: **{hotel_name if hotel_name else 'Unknown'}**")

    user_review = st.text_area("Paste Customer Review:", height=150)

    # ACTION BUTTONS - ONLY GENERATE IS GREEN NOW
    col1, col2, col3 = st.columns(3)
    with col1:
        # type="primary" triggers the GREEN CSS
        generate_btn = st.button("✨ Generate Reply", type="primary", use_container_width=True)
    with col2:
        # Default type triggers the NEUTRAL CSS
        shorten_btn = st.button("✂️ Shorten Text", use_container_width=True)
    with col3:
        # Default type triggers the NEUTRAL CSS
        elaborate_btn = st.button("✍️ Add Empathy", use_container_width=True)

    # 4. LOGIC
    if generate_btn or shorten_btn or elaborate_btn:
        if not user_review:
            st.warning("Please paste a review first.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')

                base_instruction = f"""
                Role: You are {manager_name}, manager of {hotel_name} in {location}.
                Services: {services}.
                Brand Voice: {brand_voice}.
                Task: Reply to this review: "{user_review}"
                
                CRITICAL RULES:
                1. Detect the language of the review and REPLY IN THE SAME LANGUAGE.
                2. If negative, be apologetic. If positive, be thankful.
                """

                if shorten_btn:
                    base_instruction += "\nCONSTRAINT: Keep it under 40 words."
                if elaborate_btn:
                    base_instruction += "\nCONSTRAINT: Be highly empathetic and detailed."

                # Updated Loading Text
                with st.spinner("Consulting Brand Guidelines..."):
                    response = model.generate_content(base_instruction)
                    reply = response.text
                    st.session_state["current_reply"] = reply
                    
                    if generate_btn:
                        analysis_prompt = f"""
                        Analyze this review: "{user_review}"
                        Return ONLY a string: Sentiment | Category
                        """
                        analysis = model.generate_content(analysis_prompt).text
                        st.session_state["analysis"] = analysis

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 5. DISPLAY RESULT
    if st.session_state["current_reply"]:
        st.divider()
        
        if st.session_state["analysis"]:
            st.info(f"📊 Analysis: **{st.session_state['analysis']}**")

        st.subheader("Draft Reply:")
        st.code(st.session_state["current_reply"], language=None)
        
        # Save button is also Neutral (Professional)
        if st.button("💾 Save to History"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state["history"].append({
                "Date": timestamp,
                "Client": hotel_name,
                "Review": user_review[:50] + "...",
                "Analysis": st.session_state["analysis"],
                "Reply": st.session_state["current_reply"]
            })
            st.success("Saved!")

    # 6. HISTORY
    st.divider()
    with st.expander("📜 View Session History"):
        if len(st.session_state["history"]) > 0:
            df = pd.DataFrame(st.session_state["history"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Download CSV", data=csv, file_name='smart_report.csv', mime='text/csv')
        else:
            st.write("No history yet.")