import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import pandas as pd
from datetime import datetime
import pytz # New library for Timezone fix
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="centered")

# --- NUCLEAR STYLING ---
st.markdown("""
    <style>
    /* Hide ALL Standard Elements */
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* Clean Background */
    .stApp {background-color: #0E1117;}
    
    /* Green Buttons */
    div.stButton > button[kind="primary"] {
        background-color: #2E7D32; color: white; border: none; border-radius: 6px; font-weight: 600;
        width: 100%;
        padding: 0.5rem 1rem;
    }
    div.stButton > button[kind="primary"]:hover { background-color: #1B5E20; }
    
    /* Secondary Buttons */
    div.stButton > button[kind="secondary"] {
        border: 1px solid #555; color: #eee; border-radius: 6px; width: 100%;
    }

    /* Input Fields */
    input, textarea {border-radius: 6px !important;}
    
    /* Warning Box */
    .warning-box {
        padding: 15px;
        background-color: #FFF3CD;
        color: #856404;
        border-radius: 5px;
        border: 1px solid #FFEEBA;
        margin-bottom: 10px;
    }
    </style>
    
    <script>
    // Force hide the manage button
    const observer = new MutationObserver(() => {
        const buttons = document.querySelectorAll("button");
        buttons.forEach(btn => {
            if (btn.innerText.includes("Manage app") || btn.innerText.includes("Deploy")) {
                btn.style.display = "none";
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "history" not in st.session_state: st.session_state["history"] = []
if "current_reply" not in st.session_state: st.session_state["current_reply"] = ""
if "analysis" not in st.session_state: st.session_state["analysis"] = None
if "last_action" not in st.session_state: st.session_state["last_action"] = None
if "user_settings" not in st.session_state: st.session_state["user_settings"] = {}

# --- CACHED MODEL LOADER ---
@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    model = genai.GenerativeModel(
        'gemini-2.5-flash', 
        generation_config={"temperature": 0.9, "max_output_tokens": 8192},
        safety_settings=safety_settings
    )
    return model

# --- LOGIN ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("💎 Login")
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

# --- MAIN APP LOGIC ---
if check_password():
    # 1. Load API Key
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    try:
        if api_key: model = get_model(api_key)
    except Exception as e:
        st.error(f"Connection Error: {e}")

    # --- STEP 2: THE SETUP WIZARD ---
    # Check if settings exist. If NOT, show the form.
    if "hotel_name" not in st.session_state["user_settings"] or not st.session_state["user_settings"]["hotel_name"]:
        st.title("🛠️ Business Setup")
        st.info("Please enter your business details to configure the AI.")
        
        # Pre-fill form if data exists (Edit Mode), otherwise empty
        defaults = st.session_state["user_settings"]
        
        with st.form("setup_form"):
            h_name = st.text_input("Business Name (Required)", value=defaults.get("hotel_name", ""))
            h_loc = st.text_input("Location", value=defaults.get("location", ""))
            h_srv = st.text_input("Services (e.g. Pool, Spa)", value=defaults.get("services", ""))
            h_mgr = st.text_input("Manager Name", value=defaults.get("manager_name", ""))
            h_voice = st.text_area("Brand Voice", value=defaults.get("brand_voice", "Professional, Warm, and Concise"))
            
            submitted = st.form_submit_button("Save & Continue", type="primary")
            
            if submitted:
                if not h_name:
                    st.error("Business Name is required.")
                else:
                    st.session_state["user_settings"] = {
                        "hotel_name": h_name,
                        "location": h_loc,
                        "services": h_srv,
                        "manager_name": h_mgr,
                        "brand_voice": h_voice
                    }
                    st.rerun()
    
    # --- STEP 3: THE DASHBOARD ---
    else:
        settings = st.session_state["user_settings"]
        
        # Top Bar: Title + Edit Button
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(f"Drafting for: {settings['hotel_name']}")
        with c2:
            if st.button("⚙️ Edit Profile"):
                # We keep the data in 'user_settings' but trigger a rerun so the 'if' block above catches it
                # The form will re-render, pre-filled with the current data
                # To force the form to show, we temporarily clear the 'hotel_name' check or add an 'edit_mode' flag
                # Simplest way: Clear hotel_name, but keep a backup to pre-fill? 
                # Actually, better way: Add an 'edit_mode' flag to session state.
                st.session_state["edit_mode"] = True
                st.rerun()

        # Logic to handle Edit Mode trigger
        if st.session_state.get("edit_mode", False):
             # If edit mode is ON, we clear the hotel name trigger to show the form
             # But we KEEP the data in user_settings so it pre-fills
             # We just need to unset the specific key that hides the form
             # A cleaner way is to change the logic at Step 2:
             # Instead of checking hotel_name, check a flag "profile_completed"
             pass # Refactoring logic below for next version to be cleaner

        user_review = st.text_area("Paste Customer Review:", height=150)

        col1, col2, col3 = st.columns(3)
        with col1:
            generate_btn = st.button("✨ Generate", type="primary")
        with col2:
            shorten_btn = st.button("✂️ Shorten", use_container_width=True)
        with col3:
            elaborate_btn = st.button("✍️ Expand", use_container_width=True)

        if generate_btn or shorten_btn or elaborate_btn:
            if not user_review:
                st.warning("Please paste a review first.")
            else:
                try:
                    safe_mgr = settings['manager_name'] if settings['manager_name'] else "The Management"
                    base_context = f"You are {safe_mgr}, manager of {settings['hotel_name']} in {settings['location']}. Services: {settings['services']}. Voice: {settings['brand_voice']}. Review: '{user_review}'"
                    
                    if shorten_btn:
                        st.session_state["last_action"] = "short"
                        prompt = f"{base_context}\nTASK: Write a VERY short reply (1-2 sentences MAX). RULES: Direct. No fluff. 1 Emoji. Match Language. ALWAYS END WITH: '\n\n- {safe_mgr}'"
                    elif elaborate_btn:
                        st.session_state["last_action"] = "long"
                        prompt = f"{base_context}\nTASK: Write a detailed, warm reply (4-5 sentences). RULES: Empathetic. Explain gently. 2 Emojis. Match Language. ALWAYS END WITH: '\n\n- {safe_mgr}'"
                    else:
                        st.session_state["last_action"] = "std"
                        prompt = f"{base_context}\nTASK: Write a balanced professional reply (3 sentences). RULES: Acknowledge -> Solve -> Close. Natural tone. 1 Emoji. Match Language. ALWAYS END WITH: '\n\n- {safe_mgr}'"

                    with st.spinner("Drafting..."):
                        full_response = ""
                        response_stream = model.generate_content(prompt, stream=True)
                        for chunk in response_stream:
                            if chunk.text: full_response += chunk.text
                        
                        st.session_state["current_reply"] = full_response
                        
                        if generate_btn:
                            try:
                                analysis = model.generate_content(f"Analyze: '{user_review}'. Return: Sentiment | Category").text
                                st.session_state["analysis"] = analysis
                            except:
                                st.session_state["analysis"] = None

                except Exception as e:
                    if "safety" in str(e).lower():
                        st.session_state["current_reply"] = "🛡️ Brand Protection: Review contains unsafe content."
                    else:
                        st.error(f"System Error: {str(e)}")

        if st.session_state["current_reply"]:
            st.divider()
            if st.session_state["analysis"] and "🛡️" not in st.session_state["current_reply"]:
                st.info(f"📊 {st.session_state['analysis']}")

            st.subheader("Draft Reply:")
            if "🛡️" in st.session_state["current_reply"]:
                 st.markdown(f"<div class='warning-box'>{st.session_state['current_reply']}</div>", unsafe_allow_html=True)
            else:
                unique_key = f"box_{st.session_state['last_action']}_{time.time()}"
                st.text_area("Copy or Edit:", value=st.session_state["current_reply"], height=150, key=unique_key)
                
                if st.button("💾 Save to History"):
                    # TIMEZONE FIX: Convert UTC to IST
                    ist_zone = pytz.timezone('Asia/Kolkata')
                    ist_time = datetime.now(ist_zone).strftime("%Y-%m-%d %H:%M")
                    
                    st.session_state["history"].append({
                        "Date": ist_time, "Client": settings['hotel_name'], "Review": user_review[:50] + "...", "Reply": st.session_state["current_reply"]
                    })
                    st.success("Saved!")

        st.divider()
        if st.button("📜 View History"):
            if len(st.session_state["history"]) > 0:
                df = pd.DataFrame(st.session_state["history"])
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Download CSV", data=csv, file_name='smart_report.csv', mime='text/csv')
            else:
                st.write("No history yet.")