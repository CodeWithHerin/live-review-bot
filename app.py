import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div.stButton > button[kind="primary"] {
        background-color: #2E7D32; color: white; border: none; border-radius: 6px; font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover { background-color: #1B5E20; }
    div.stButton > button[kind="secondary"] { border: 1px solid #555; color: #eee; border-radius: 6px; }
    textarea { font-size: 1rem !important; font-family: sans-serif !important; }
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
if "last_action" not in st.session_state: st.session_state["last_action"] = None

# --- HELPERS ---
def clear_text_box():
    if "final_output_box" in st.session_state: del st.session_state["final_output_box"]

def update_client_info():
    selected = st.session_state["selected_client_dropdown"]
    data = CLIENT_PRESETS[selected]
    st.session_state["h_name"] = data["name"]
    st.session_state["loc"] = data["location"]
    st.session_state["srv"] = data["services"]
    st.session_state["mgr"] = data["owner"]

# --- LOGIN ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.header("💎 Smart Agency Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Log In", type="primary"):
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
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    with st.sidebar:
        st.success(f"👤 Agent: {st.session_state['user']}")
        st.divider()
        st.subheader("📂 Client Profile")
        selected_client = st.selectbox("Select Client:", list(CLIENT_PRESETS.keys()), key="selected_client_dropdown", on_change=update_client_info)
        hotel_name = st.text_input("Business Name (Required)", key="h_name", placeholder="Enter Hotel Name")
        location = st.text_input("Location", key="loc")
        services = st.text_input("Services", key="srv")
        manager_name = st.text_input("Sign-off Name", key="mgr", placeholder="e.g. The Manager")
        st.divider()
        st.subheader("🎨 Brand Voice")
        brand_voice = st.text_area("Describe Tone", value="Professional but conversational. Warm, like a real person talking.")
        if hotel_name: st.caption("✅ Profile Active")
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.title("💎 Smart Review Responder")
    if not hotel_name: st.warning("⚠️ Please enter a Business Name in the sidebar to start.")
    else: st.markdown(f"Drafting for: **{hotel_name}**")

    user_review = st.text_area("Paste Customer Review:", height=150)

    col1, col2, col3 = st.columns(3)
    with col1:
        generate_btn = st.button("✨ Generate Reply", type="primary", use_container_width=True, on_click=clear_text_box)
    with col2:
        shorten_btn = st.button("✂️ Make Conciser", use_container_width=True, on_click=clear_text_box)
    with col3:
        elaborate_btn = st.button("✍️ Add Detail (Polite)", use_container_width=True, on_click=clear_text_box)

    if generate_btn or shorten_btn or elaborate_btn:
        if not user_review:
            st.warning("Please paste a review first.")
        elif not hotel_name:
            st.error("❌ Error: Business Name is missing.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # MAX TOKENS set to 1000 to give AI breathing room
                # SAFETY SETTINGS disabled to allow reading negative reviews
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                model = genai.GenerativeModel(
                    'gemini-2.5-flash', 
                    generation_config={"temperature": 0.7, "max_output_tokens": 1000},
                    safety_settings=safety_settings
                )
                
                safe_mgr = manager_name if manager_name else "The Management"
                
                base_context = f"You are {safe_mgr}, manager of {hotel_name} in {location}. Services: {services}. Voice: {brand_voice}. Review: '{user_review}'"
                
                if shorten_btn:
                    st.session_state["last_action"] = "short" 
                    prompt = f"""
                    {base_context}
                    TASK: Write a punchy reply (1-2 sentences).
                    RULES: No fluff. Address point. 1 Emoji. Match Language.
                    ALWAYS END WITH: "\n\n- {safe_mgr}"
                    """
                elif elaborate_btn:
                    st.session_state["last_action"] = "long"
                    prompt = f"""
                    {base_context}
                    TASK: Write a detailed, empathetic reply (4-5 sentences).
                    RULES: Validate feelings. Explain gently. 2 Emojis. Match Language.
                    ALWAYS END WITH: "\n\n- {safe_mgr}"
                    """
                else:
                    st.session_state["last_action"] = "std"
                    prompt = f"""
                    {base_context}
                    TASK: Write a balanced professional reply (3 sentences).
                    RULES: Natural tone. 'I' not 'We'. 1 Emoji. Match Language.
                    ALWAYS END WITH: "\n\n- {safe_mgr}"
                    """

                with st.spinner("Consulting Brand Guidelines..."):
                    response = model.generate_content(prompt)
                    
                    # --- V5.6 FIX: ROBUST TEXT EXTRACTION ---
                    # We manually dig for the text to avoid 'finish_reason' crashes
                    final_text = ""
                    if response.candidates:
                        candidate = response.candidates[0]
                        if candidate.content and candidate.content.parts:
                            final_text = candidate.content.parts[0].text
                        elif candidate.finish_reason == 2:
                            final_text = "⚠️ Error: The AI reply was cut off (Max Tokens). Please try 'Make Conciser'."
                        else:
                            final_text = "⚠️ Error: Safety Filter triggered. Please refine the review text."
                    
                    st.session_state["current_reply"] = final_text
                    
                    if generate_btn and final_text:
                        try:
                            analysis_prompt = f"Analyze review: '{user_review}'. Return string: Sentiment | Category"
                            analysis = model.generate_content(analysis_prompt).text
                            st.session_state["analysis"] = analysis
                        except:
                            st.session_state["analysis"] = "Analysis Unavailable"

            except Exception as e:
                st.error(f"System Error: {str(e)}")

    if st.session_state["current_reply"]:
        st.divider()
        if st.session_state["analysis"]:
            st.info(f"📊 Analysis: **{st.session_state['analysis']}**")

        st.subheader("Draft Reply:")
        
        unique_key = f"box_{st.session_state['last_action']}_{datetime.now().strftime('%H%M%S')}"
        
        st.text_area("Copy or Edit:", value=st.session_state["current_reply"], height=150, key=unique_key)
        
        if st.button("💾 Save to History"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state["history"].append({
                "Date": timestamp, "Client": hotel_name, "Review": user_review[:50] + "...", "Reply": st.session_state["current_reply"]
            })
            st.success("Saved!")

    st.divider()
    with st.expander("📜 View Session History"):
        if len(st.session_state["history"]) > 0:
            df = pd.DataFrame(st.session_state["history"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Download CSV", data=csv, file_name='smart_report.csv', mime='text/csv')
        else:
            st.write("No history yet.")