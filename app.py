import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="wide")

# --- STYLING (Green Button + Professional Look) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Primary Green Button */
    div.stButton > button[kind="primary"] {
        background-color: #2E7D32; color: white; border: none; border-radius: 6px; font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover { background-color: #1B5E20; }
    
    /* Secondary Gray Buttons */
    div.stButton > button[kind="secondary"] { border: 1px solid #555; color: #eee; border-radius: 6px; }
    
    /* Better Text Area Reading */
    textarea { font-size: 1rem !important; font-family: sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CLIENT PRESETS (Your Database) ---
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

# --- SESSION STATE INITIALIZATION ---
if "history" not in st.session_state: st.session_state["history"] = []
if "current_reply" not in st.session_state: st.session_state["current_reply"] = ""
if "analysis" not in st.session_state: st.session_state["analysis"] = None
if "last_action" not in st.session_state: st.session_state["last_action"] = None

# --- HELPER FUNCTIONS ---
def clear_text_box():
    """Forces the text box to reset so new text appears instantly"""
    if "final_output_box" in st.session_state: 
        del st.session_state["final_output_box"]

def update_client_info():
    """Updates the sidebar inputs when dropdown changes"""
    selected = st.session_state["selected_client_dropdown"]
    data = CLIENT_PRESETS[selected]
    st.session_state["h_name"] = data["name"]
    st.session_state["loc"] = data["location"]
    st.session_state["srv"] = data["services"]
    st.session_state["mgr"] = data["owner"]

# --- LOGIN SYSTEM ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.header("💎 Smart Agency Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Log In", type="primary"):
                # CHECK SECRETS FOR PASSWORD
                if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                    st.session_state["password_correct"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("⛔ Access Denied")
        return False
    return True

# --- MAIN APPLICATION ---
if check_password():
    # 1. Get API Key Securely
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # 2. Sidebar Configuration
    with st.sidebar:
        st.success(f"👤 Agent: {st.session_state['user']}")
        st.divider()
        st.subheader("📂 Client Profile")
        
        # Dropdown with Autofill Callback
        selected_client = st.selectbox(
            "Select Client:", list(CLIENT_PRESETS.keys()), 
            key="selected_client_dropdown", on_change=update_client_info
        )
        
        # Input Fields
        hotel_name = st.text_input("Business Name (Required)", key="h_name", placeholder="Enter Hotel Name")
        location = st.text_input("Location", key="loc")
        services = st.text_input("Services", key="srv")
        manager_name = st.text_input("Sign-off Name", key="mgr", placeholder="e.g. The Manager")
        
        st.divider()
        st.subheader("🎨 Brand Voice")
        brand_voice = st.text_area("Describe Tone", value="Professional, Warm, and Concise")
        
        if hotel_name: st.caption("✅ Profile Active")
        if st.button("Log Out"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 3. Main Interface
    st.title("💎 Smart Review Responder")
    
    # Safety Warning
    if not hotel_name:
        st.warning("⚠️ Please enter a Business Name in the sidebar to start.")
    else:
        st.markdown(f"Drafting for: **{hotel_name}**")

    user_review = st.text_area("Paste Customer Review:", height=150)

    # Buttons with 'on_click' to clear old text
    col1, col2, col3 = st.columns(3)
    with col1:
        generate_btn = st.button("✨ Generate Reply", type="primary", use_container_width=True, on_click=clear_text_box)
    with col2:
        shorten_btn = st.button("✂️ Make Conciser", use_container_width=True, on_click=clear_text_box)
    with col3:
        elaborate_btn = st.button("✍️ Add Detail (Polite)", use_container_width=True, on_click=clear_text_box)

    # 4. Logic Core
    if generate_btn or shorten_btn or elaborate_btn:
        if not user_review:
            st.warning("Please paste a review first.")
        elif not hotel_name:
            st.error("❌ Error: Business Name is missing. Please fill it in the Sidebar.")
        else:
            try:
                genai.configure(api_key=api_key)
                # Quality Settings: Temp 0.7 (Creative but stable), Tokens 250 (No cut-off)
                model = genai.GenerativeModel('gemini-2.5-flash', 
                    generation_config={"temperature": 0.7, "max_output_tokens": 250})
                
                safe_mgr = manager_name if manager_name else "The Management"
                
                # BASE CONTEXT (The Humanizer)
                context = f"""
                You are {safe_mgr}, manager of {hotel_name} in {location}. 
                Services: {services}. Tone: {brand_voice}.
                The customer wrote: "{user_review}"
                """
                
                # DISTINCT PROMPTS FOR EACH BUTTON
                if shorten_btn:
                    st.session_state["last_action"] = "short" 
                    prompt = f"""
                    {context}
                    TASK: Write a direct, punchy reply (max 2 sentences).
                    RULES: No fluff. Address the main point immediately. Use 1 relevant emoji.
                    Match language of review.
                    SIGN-OFF: "- {safe_mgr}"
                    """
                elif elaborate_btn:
                    st.session_state["last_action"] = "long"
                    prompt = f"""
                    {context}
                    TASK: Write a warm, empathetic reply (4-5 sentences).
                    RULES: Validate their feelings. Explain our side gently. Invite them back. Use 2 emojis.
                    Match language of review.
                    SIGN-OFF: "- {safe_mgr}"
                    """
                else:
                    st.session_state["last_action"] = "std"
                    prompt = f"""
                    {context}
                    TASK: Write a balanced professional reply (3 sentences).
                    RULES: Acknowledge -> Address -> Close. Sound natural (use 'I' not 'We'). Use 1 emoji.
                    Match language of review.
                    SIGN-OFF: "- {safe_mgr}"
                    """

                with st.spinner("Consulting Brand Guidelines..."):
                    response = model.generate_content(prompt)
                    st.session_state["current_reply"] = response.text
                    
                    # Analyze only on fresh generation to save time
                    if generate_btn:
                        analysis_prompt = f"Analyze review: '{user_review}'. Return string: Sentiment | Category"
                        analysis = model.generate_content(analysis_prompt).text
                        st.session_state["analysis"] = analysis

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 5. Display Result
    if st.session_state["current_reply"]:
        st.divider()
        if st.session_state["analysis"]:
            st.info(f"📊 Analysis: **{st.session_state['analysis']}**")

        st.subheader("Draft Reply:")
        
        # DYNAMIC KEY FIX: Ensures box refreshes every time a new button is clicked
        unique_key = f"box_{st.session_state['last_action']}_{datetime.now().strftime('%H%M%S')}"
        
        st.text_area(
            "Copy or Edit:", 
            value=st.session_state["current_reply"], 
            height=150, 
            key=unique_key
        )
        
        if st.button("💾 Save to History"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state["history"].append({
                "Date": timestamp, "Client": hotel_name, "Review": user_review[:50] + "...", "Reply": st.session_state["current_reply"]
            })
            st.success("Saved!")

    # 6. History Table
    st.divider()
    with st.expander("📜 View Session History"):
        if len(st.session_state["history"]) > 0:
            df = pd.DataFrame(st.session_state["history"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Download CSV", data=csv, file_name='smart_report.csv', mime='text/csv')
        else:
            st.write("No history yet.")