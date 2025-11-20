import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="Review Reply Pro", page_icon="✨")

# --- HIDE STREAMLIT BRANDING (CSS HACK) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- API KEY LOGIC ---
# Try to get key from Cloud Secrets first
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # If running locally without secrets, ask for it
    api_key = st.text_input("Enter API Key", type="password")

# --- MAIN APP ---
st.title("✨ Instant Review Reply")
st.write("Paste the customer review below.")

user_review = st.text_area("Customer Review:", height=150, placeholder="Example: The room was dirty but the staff was nice...")
tone = st.selectbox("Choose Tone:", ["Professional", "Friendly", "Apologetic", "Short & Sweet"])

if st.button("Generate Reply"):
    if not api_key:
        st.error("System Error: API Key missing.")
    elif not user_review:
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
            
            with st.spinner("Drafting the perfect response..."):
                response = model.generate_content(prompt)
                st.success("Copy this reply:")
                st.code(response.text, language=None) # Makes it easy to copy
        
        except Exception as e:
            st.error(f"Error: {str(e)}")