import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="wide")

# --- HIDE BRANDING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
if "history" not in st.session_state:
    st.session_state["history"] = []
if "current_reply" not in st.session_state:
    st.session_state["current_reply"] = ""
if "analysis" not in st.session_state:
    st.session_state["analysis"] = None

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
            if st.button("Log In"):
                if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                    st.session_state["password_correct"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("⛔ Access Denied")
        return False
    return True

# --- HELPER FUNCTIONS ---
def generate_reply(model, prompt):
    with st.spinner("🤖 AI is working..."):
        response = model.generate_content(prompt)
        return response.text

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
        selected_client = st.selectbox("Select Client:", list(CLIENT_PRESETS.keys()))
        data = CLIENT_PRESETS[selected_client]

        hotel_name = st.text_input("Business Name", value=data["name"], key="h_name")
        location = st.text_input("Location", value=data["location"], key="loc")
        services = st.text_input("Services", value=data["services"], key="srv")
        manager_name = st.text_input("Sign-off Name", value=data["owner"], key="mgr")
        
        st.divider()
        st.subheader("🎨 Brand Voice")
        brand_voice = st.text_area("Describe Tone", value="Professional, Warm, and Helpful", help="E.g., 'We are funny and casual' or 'Strictly formal'")
        
        if hotel_name: st.success("✅ Profile Active")
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 3. MAIN INTERFACE
    st.title("💎 Smart Review Responder V4")
    st.markdown(f"Drafting for: **{hotel_name if hotel_name else 'Unknown'}**")

    user_review = st.text_area("Paste Customer Review:", height=150)

    # ACTION BUTTONS
    col1, col2, col3 = st.columns(3)
    
    with col1:
        generate_btn = st.button("✨ Generate Reply", type="primary", use_container_width=True)
    with col2:
        shorten_btn = st.button("✂️ Make Shorter", use_container_width=True)
    with col3:
        elaborate_btn = st.button("✍️ Add Empathy", use_container_width=True)

    # 4. LOGIC
    if generate_btn or shorten_btn or elaborate_btn:
        if not user_review:
            st.warning("Please paste a review first.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')

                # BASE INSTRUCTION
                base_instruction = f"""
                Role: You are {manager_name}, manager of {hotel_name} in {location}.
                Services: {services}.
                Brand Voice: {brand_voice}.
                Task: Reply to this review: "{user_review}"
                
                CRITICAL RULES:
                1. Detect the language of the review and REPLY IN THE SAME LANGUAGE.
                2. If the review is negative, be apologetic and solution-oriented.
                3. If positive, thank them and mention our services.
                """

                # MODIFIERS
                if shorten_btn:
                    base_instruction += "\nCONSTRAINT: Keep the reply under 50 words."
                if elaborate_btn:
                    base_instruction += "\nCONSTRAINT: Be extra empathetic and explain our commitment to quality."

                # GENERATE
                reply = generate_reply(model, base_instruction)
                st.session_state["current_reply"] = reply
                
                # ANALYZE (Only on fresh generation)
                if generate_btn:
                    analysis_prompt = f"""
                    Analyze this review: "{user_review}"
                    Return ONLY a string in this format: Sentiment | Category
                    Example: Negative | Hygiene Issue
                    """
                    analysis = generate_reply(model, analysis_prompt)
                    st.session_state["analysis"] = analysis

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 5. DISPLAY RESULT
    if st.session_state["current_reply"]:
        st.divider()
        
        # Analysis Tags
        if st.session_state["analysis"]:
            st.info(f"📊 Analysis: **{st.session_state['analysis']}**")

        st.subheader("Draft Reply:")
        st.code(st.session_state["current_reply"], language=None)
        
        # Save to History Logic
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