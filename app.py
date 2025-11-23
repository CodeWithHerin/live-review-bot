import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import pandas as pd
from datetime import datetime
import pytz
import time

# --- PAGE CONFIG (CENTERED = BETTER LAYOUT) ---
st.set_page_config(page_title="Review Reply Pro", page_icon="💎", layout="centered")

# --- CSS CLEANUP & STYLING ---
st.markdown("""
    <style>
    /* 1. Hide Streamlit Chrome */
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    /* 2. Background */
    .stApp {background-color: #0E1117;}
    
    /* 3. GREEN BUTTONS (Targeting Form Submit specifically too) */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background-color: #2E7D32 !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 6px !important; 
        font-weight: 600 !important; 
        width: 100%;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button[kind="primary"]:hover { 
        background-color: #1B5E20 !important; 
    }
    
    /* 4. SECONDARY BUTTONS */
    div.stButton > button[kind="secondary"] {
        border: 1px solid #555; color: #eee; border-radius: 6px; width: 100%;
    }
    
    /* 5. INPUT FIELDS */
    input, textarea { border-radius: 6px !important; }
    
    /* 6. WARNING BOX */
    .warning-box {
        padding: 1rem; background-color: #FFF3CD; color: #856404;
        border-radius: 5px; border: 1px solid #FFEEBA; margin-bottom: 10px;
    }
    </style>
    
    <script>
    // Aggressive JS to remove 'Manage App' & Toolbar
    setInterval(function() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes("Manage app") || btn.innerText.includes("Deploy") || btn.innerText.includes("Share")) {
                btn.style.display = 'none';
            }
        });
        const toolbar = window.parent.document.querySelector('[data-testid="stToolbar"]');
        if (toolbar) toolbar.remove();
    }, 500);
    </script>
    """, unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "user_settings" not in st.session_state: st.session_state["user_settings"] = {}
if "history" not in st.session_state: st.session_state["history"] = []
if "current_reply" not in st.session_state: st.session_state["current_reply"] = ""
if "analysis" not in st.session_state: st.session_state["analysis"] = None
if "last_action" not in st.session_state: st.session_state["last_action"] = None

# --- CACHED MODEL ---
@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    return genai.GenerativeModel(
        'gemini-2.5-flash', 
        generation_config={"temperature": 0.9, "max_output_tokens": 8192},
        safety_settings=safety_settings
    )

# --- SCREENS ---

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 1]) # Centered column
    with c2:
        st.title("💎 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In", type="primary"):
            if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("⛔ Access Denied")

def setup_screen():
    # Centered Layout for Setup (No columns needed due to page config)
    st.title("🛠️ Business Setup")
    st.info("Configure your business details to start.")
    
    defaults = st.session_state["user_settings"]
    
    with st.form("setup_form"):
        h_name = st.text_input("Business Name (Required)", value=defaults.get("hotel_name", ""))
        h_loc = st.text_input("Location", value=defaults.get("location", ""))
        h_srv = st.text_input("Services", value=defaults.get("services", ""))
        h_mgr = st.text_input("Manager Name", value=defaults.get("manager_name", ""))
        h_voice = st.text_area("Brand Voice", value=defaults.get("brand_voice", "Professional, Warm, and Concise"))
        
        # This button will now be GREEN due to the CSS fix
        submitted = st.form_submit_button("Save & Continue", type="primary")
        
        if submitted:
            if not h_name:
                st.error("Business Name is required.")
            else:
                st.session_state["user_settings"] = {
                    "hotel_name": h_name, "location": h_loc, 
                    "services": h_srv, "manager_name": h_mgr, 
                    "brand_voice": h_voice
                }
                st.rerun()

def dashboard_screen():
    settings = st.session_state["user_settings"]
    
    # Get API Key
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter API Key", type="password")

    # Header Area
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader(f"Drafting for: {settings['hotel_name']}")
    with c2:
        if st.button("⚙️ Edit Profile"):
            st.session_state["user_settings"]["hotel_name"] = "" 
            st.rerun()

    user_review = st.text_area("Paste Customer Review:", height=150)

    # Buttons are now close together because layout="centered"
    c1, c2, c3 = st.columns(3)
    with c1: gen_btn = st.button("✨ Generate", type="primary")
    with c2: short_btn = st.button("✂️ Shorten")
    with c3: detail_btn = st.button("✍️ Expand")

    if gen_btn or short_btn or detail_btn:
        if not user_review:
            st.warning("Please paste a review.")
        elif not api_key:
            st.error("API Key missing.")
        else:
            try:
                model = get_model(api_key)
                mgr = settings['manager_name'] if settings['manager_name'] else "The Management"
                base = f"You are {mgr}, manager of {settings['hotel_name']} in {settings['location']}. Services: {settings['services']}. Voice: {settings['brand_voice']}. Review: '{user_review}'"
                
                if short_btn:
                    st.session_state["last_action"] = "short"
                    prompt = f"{base}\nTASK: Write VERY short reply (1-2 sentences). RULES: Direct. 1 Emoji. Match Language. END WITH: '\n\n- {mgr}'"
                elif detail_btn:
                    st.session_state["last_action"] = "long"
                    prompt = f"{base}\nTASK: Write warm, detailed reply (4-5 sentences). RULES: Empathetic. 2 Emojis. Match Language. END WITH: '\n\n- {mgr}'"
                else:
                    st.session_state["last_action"] = "std"
                    prompt = f"{base}\nTASK: Write balanced reply (3 sentences). RULES: Natural. 1 Emoji. Match Language. END WITH: '\n\n- {mgr}'"

                with st.spinner("Drafting..."):
                    response = model.generate_content(prompt)
                    
                    final_text = ""
                    if response.parts: final_text = response.text
                    elif response.candidates and response.candidates[0].content.parts:
                        final_text = response.candidates[0].content.parts[0].text
                    elif response.prompt_feedback and response.prompt_feedback.block_reason:
                        final_text = "🛡️ Brand Protection: Review contains unsafe content."
                    else:
                        final_text = "⚠️ System Error. Try again."
                    
                    st.session_state["current_reply"] = final_text
                    
                    if gen_btn and "⚠️" not in final_text and "🛡️" not in final_text:
                        try:
                            an_prompt = f"Analyze: '{user_review}'. Return: Sentiment | Category"
                            st.session_state["analysis"] = model.generate_content(an_prompt).text
                        except: st.session_state["analysis"] = None

            except Exception as e:
                st.error(f"Error: {e}")

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
                ist = pytz.timezone('Asia/Kolkata')
                ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M")
                st.session_state["history"].append({
                    "Date": ts, "Client": settings['hotel_name'], "Review": user_review[:50]+"...", "Reply": st.session_state["current_reply"]
                })
                st.success("Saved!")

    st.divider()
    if st.button("📜 View History"):
        if len(st.session_state["history"]) > 0:
            df = pd.DataFrame(st.session_state["history"])
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Download CSV", data=csv, file_name='report.csv', mime='text/csv')
        else:
            st.write("No history yet.")

# --- MAIN CONTROLLER ---
if not st.session_state["logged_in"]:
    login_screen()
else:
    if "hotel_name" not in st.session_state["user_settings"] or not st.session_state["user_settings"]["hotel_name"]:
        setup_screen()
    else:
        dashboard_screen()