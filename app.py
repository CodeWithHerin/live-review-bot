import streamlit as st
import google.generativeai as genai

# --- PART 1: CONFIGURATION ---
# This sets up the page title and icon
st.set_page_config(page_title="AI Review Responder", page_icon="🤖")

# --- PART 2: SIDEBAR (API KEY) ---
# We ask for the API key here so we don't hard-code it (security best practice)
with st.sidebar:
    st.header("Settings")
    # This input box hides the key like a password
    api_key = st.text_input("Enter Gemini API Key", type="password")

# --- PART 3: THE MAIN APP UI ---
st.title("🤖 Auto-Review Responder")
st.write("Paste a customer review below, and I will write a professional reply.")

# Input Box for the user to paste the review
user_review = st.text_area("Customer Review:", height=150, placeholder="Paste review here...")

# Dropdown to choose the 'vibe' of the reply
tone = st.selectbox("Choose Tone:", ["Professional", "Friendly", "Apologetic"])

# --- PART 4: THE MAGIC (GEMINI) ---
if st.button("Generate Reply"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar first!")
    elif not user_review:
        st.error("Please paste a review first!")
    else:
        try:
            # Connect to Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # The Prompt (Instructions to AI)
            prompt = f"""
            You are a customer service expert. 
            Write a reply to this customer review: "{user_review}"
            The tone should be: {tone}.
            Keep it concise and polite.
            Output ONLY the reply text.
            """

            # Get response
            with st.spinner("Thinking..."):
                response = model.generate_content(prompt)
                st.success("Here is your draft:")
                st.write(response.text)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")