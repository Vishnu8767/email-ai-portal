import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.utils
import requests
import json
import re 
import time
import html  
import io
import streamlit as st
from PIL import Image as PILImage

try:
    import pytesseract
except ImportError:
    pytesseract = None

# ==================== WEB PORTAL LAYOUT CONFIGURATION ====================
st.set_page_config(
    page_title="Global Email Intelligence Portal",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #1E293B; margin-bottom: 0.2rem; }
    .subtitle { font-size: 1.1rem; color: #64748B; margin-bottom: 2rem; }
    .metric-card { background-color: #F8FAFC; padding: 1.5rem; border-radius: 0.75rem; border-left: 6px solid #2563EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .status-text { font-family: 'Courier New', Courier, monospace; font-size: 0.9rem; color: #0F172A; }
    </style>
""", unsafe_allow_html=True)

if "email_store" not in st.session_state:
    st.session_state.email_store = []
if "email_subjects" not in st.session_state:
    st.session_state.email_subjects = []

# ==================== SIDEBAR CONFIGURATION ====================
st.sidebar.image("https://img.icons8.com/fluent/100/000000/artificial-intelligence.png", width=55)
st.sidebar.markdown("### Secure Server Settings")

EMAIL_USER = st.sidebar.text_input("Gmail Address", value="sreenivasareddy267538@gmail.com")
EMAIL_PASS = st.sidebar.text_input("Gmail App Password", value="vzjt tjrq qmif szac", type="password")

st.sidebar.markdown("---")
st.sidebar.markdown("### AI Engine Settings")
MODEL_NAME = "meta/llama-3.3-70b-instruct"
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

default_key = ""
try:
    from google.colab import userdata
    default_key = userdata.get('NVAPI_KEY')
except:
    pass

NVAPI_KEY = st.sidebar.text_input("NVIDIA API Key", value=default_key, type="password")

# ==================== CORE COGNITIVE COMPONENT FUNCTIONS ====================

def send_nvidia_request_with_retry(payload, status_placeholder, max_retries=4):
    if not NVAPI_KEY:
        st.sidebar.error("❌ Missing NVIDIA API Key! Configure it in the sidebar or advanced settings.")
        return None
        
    headers = {
        "Authorization": f"Bearer {NVAPI_KEY.strip()}",
        "Content-Type": "application/json"
    }
    
    delay = 2  
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 429:
                status_placeholder.warning(f"⚠️ Rate limit hit (429). Pacing engine pausing for {delay}s before retry...")
                time.sleep(delay)
                delay *= 2  
                continue
                
            response_data = response.json()
            if "choices" in response_data:
                return response_data["choices"][0]["message"]["content"].strip()
            else:
                st.error(f"NVIDIA API Error: {response_data}")
                return None
                
        except Exception as network_error:
            status_placeholder.warning(f"Connection hiccup, retrying: {network_error}")
            time.sleep(1)
            
    st.error("❌ Pipeline Break: Max retries reached. Server overloaded.")
    return None

def clean_html(html_text):
    unescaped = html.unescape(html_text)
    clean = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', unescaped, flags=re.IGNORECASE)
    clean = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'[\u200b-\u200d\u2060\ufeff\xad]', '', clean)
    return re.sub(r'\s+', ' ', clean).strip()

def extract_text_from_images_ocr(image_bytes_list):
    if not pytesseract:
        return ""
    ocr_text_pool = []
    for idx, img_bytes in enumerate(image_bytes_list):
        try:
            image_object = PILImage.open(io.BytesIO(img_bytes))
            extracted_string = pytesseract.image_to_string(image_object)
            if extracted_string.strip():
                ocr_text_pool.append(f"\n--- [Text Extracted From Attached Image #{idx+1}] ---\n{extracted_string.strip()}")
        except:
            pass
    return "\n".join(ocr_text_pool)

# ==================== MAIN DASHBOARD UI WORKSPACE ====================
st.markdown('<div class="main-title">📥 Global Email Intelligence Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Secure Multi-Stage Email Analysis, Optical Character Recognition, and Fallback Persona Engine</div>', unsafe_allow_html=True)

col_ctrl_1, col_ctrl_2 = st.columns([1, 2])

with col_ctrl_1:
    folder_choice = st.radio("Select Mail Folder Target", ["Inbox (Clean)", "Spam Folder"], horizontal=True)
    target_folder = "[Gmail]/Spam" if folder_choice == "Spam Folder" else "inbox"

with col_ctrl_2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Sync & Retrieve Latest Mail Threads", use_container_width=True):
        if not EMAIL_USER or not EMAIL_PASS:
            st.error("Please enter your Gmail configurations in the sidebar.")
        else:
            with st.spinner("Establishing secure IMAP handshake link..."):
                try:
                    mail = imaplib.IMAP4_SSL("imap.gmail.com")
                    mail.login(EMAIL_USER, EMAIL_PASS)
                    mail.select(target_folder)
                    
                    status, messages = mail.search(None, "ALL")
                    email_ids = messages[0].split()
                    latest_emails = email_ids[-10:]
                    latest_emails.reverse()
                    
                    st.session_state.email_store = []
                    st.session_state.email_subjects = []
                    
                    for idx, e_id in enumerate(latest_emails):
                        res, msg_data = mail.fetch(e_id, "(RFC822)")
                        for response in msg_data:
                            if isinstance(response, tuple):
                                msg = email.message_from_bytes(response[1])
                                subject, encoding = decode_header(msg["Subject"])[0]
                                if isinstance(subject, bytes):
                                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                                st.session_state.email_subjects.append(f"[{idx}] {subject}")
                                st.session_state.email_store.append(msg)
                    mail.logout()
                    st.success(f"Successfully synced top {len(st.session_state.email_subjects)} email headers!")
                except Exception as err:
                    st.error(f"Failed to fetch mail data: {err}")

st.markdown("---")

if st.session_state.email_subjects:
    selected_subject = st.selectbox("Select an incoming message thread to process:", st.session_state.email_subjects)
    selection_index = st.session_state.email_subjects.index(selected_subject)
    selected_msg = st.session_state.email_store[selection_index]
    
    if st.button("🚀 Run Deep Cognitive Evaluation Pipeline", type="primary", use_container_width=True):
        status_box = st.empty()
        body = ""
        html_body = ""
        extracted_images = []
        
        if selected_msg.is_multipart():
            for part in selected_msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type.startswith("image/"):
                    img_bytes = part.get_payload(decode=True)
                    if img_bytes: extracted_images.append(img_bytes)
                    continue
                if "attachment" in content_disposition: continue
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode(errors="ignore")
            if html_body.strip(): body = clean_html(html_body)
            elif body.strip(): body = clean_html(body)
        else:
            content_type = selected_msg.get_content_type()
            payload = selected_msg.get_payload(decode=True)
            if content_type.startswith("image/"):
                if payload: extracted_images.append(payload)
            elif content_type == "text/html":
                body = clean_html(payload.decode(errors="ignore"))
            else:
                body = clean_html(payload.decode(errors="ignore"))
                
        image_ocr_payload = ""
        if extracted_images:
            image_ocr_payload = extract_text_from_images_ocr(extracted_images)
            
        total_email_text = f"{body.strip()}\n{image_ocr_payload}".strip()
        
        if total_email_text or extracted_images:
            tab_doc, tab_ai = st.columns([1, 1])
            
            with tab_doc:
                st.markdown("### 📄 Email Document Payload")
                if body.strip():
                    st.text_area("Cleaned Email Text Body", value=body.strip(), height=250, disabled=True)
                if image_ocr_payload.strip():
                    st.text_area("Extracted OCR Text Layer", value=image_ocr_payload.strip(), height=150, disabled=True)
                if extracted_images:
                    st.markdown("#### 📸 Extracted Image Assets")
                    for img_bytes in extracted_images:
                        st.image(img_bytes, use_column_width=True)
                        
            with tab_ai:
                st.markdown("### 🧠 AI Analytics & Automation")
                
                if total_email_text:
                    status_box.info("🕵️ Stage 1/5: Mapping linguistic matrix fingerprints...")
                    lang_payload = {
                        "model": MODEL_NAME,
                        "messages": [{"role": "system", "content": "You are an advanced language identification system. Identify underlying languages spoken phonetically. Ignore nouns/currency markers. STRICT ACCURACY RULE: Do not guess based on acronyms like 'CA 1' or 'marks'. If pure English shorthand, return ONLY 'English'. Reply with clean, comma-separated language names."},
                                     {"role": "user", "content": f"Identify languages:\n\n{total_email_text[:20000]}"}],
                        "temperature": 0.0, "max_tokens": 100
                    }
                    detected_languages = send_nvidia_request_with_retry(lang_payload, status_box)
                    
                    if detected_languages:
                        status_box.info("🔀 Stage 2/5: Synchronizing English translation layers...")
                        trans_payload = {
                            "model": MODEL_NAME,
                            "messages": [{"role": "system", "content": "You are an elite translator. Convert regular or phonetic transliterated regional layouts into fluent English. Preserve all metrics and exact values. Output ONLY translation text."},
                                         {"role": "user", "content": f"Translate into English:\n\n{total_email_text[:15000]}"}],
                            "temperature": 0.0, "max_tokens": 2000
                        }
                        translation_output = send_nvidia_request_with_retry(trans_payload, status_box) if "english" not in detected_languages.lower() else total_email_text
                        
                        status_box.info("🎭 Stage 3/5: Running deep word-by-word tone profiler...")
                        tone_payload = {
                            "model": MODEL_NAME,
                            "messages": [{"role": "system", "content": "You are an expert communication analyst. Classify tone as 'Friendly' or 'Formal'. Read every single word. If it starts formal but shifts to personal questions ('ela unav', 'tinnava'), it is 'Friendly'. Reply with ONLY the single classification word."},
                                         {"role": "user", "content": f"Determine tone:\n\n{total_email_text[:5000]}"}],
                            "temperature": 0.0, "max_tokens": 10
                        }
                        detected_tone = send_nvidia_request_with_retry(tone_payload, status_box)
                        
                        status_box.info("🤖 Stage 4/5: Compiling human persona fallback response...")
                        draft_payload = {
                            "model": MODEL_NAME,
                            "messages": [{"role": "system", "content": f"You are a real human writing a direct personal reply as Vishnu (Boddu Vishnu Vardhan Reddy), a Computer Science student at Amity University studying NLP, Python, and GATE. Hobbies: IPL cricket, Telugu movies, Free Fire MAX. Food: Idli/Dosa/Poha with coffee in the morning, rice/dal/roti for lunch/dinner. CRITICAL AUTONOMOUS FALLBACK: If asked details not in profile, invent a natural realistic human reply fitting Vishnu's background. NEVER say 'I am an AI'. Match tone style parameter: **{detected_tone}**. Output ONLY response text payload."},
                                         {"role": "user", "content": f"Draft human response to:\n\n{translation_output[:5000]}"}],
                            "temperature": 0.5, "max_tokens": 1000
                        }
                        english_reply = send_nvidia_request_with_retry(draft_payload, status_box)
                        
                        status_box.info(f"🔄 Stage 5/5: Translating response back to destination tracking system ({detected_languages})...")
                        rev_payload = {
                            "model": MODEL_NAME,
                            "messages": [{"role": "system", "content": f"You are an elite linguistic expert. Translate the English message into {detected_languages}. Every phrase must be complete. Explicitly add verbs for implied actions. Avoid robotic phrases (do not use 'అడగ్గా ధన్యవాదాలు', use 'అడిగినందుకు ధన్యవాదాలు'). Maintain {detected_tone} tone register. Output ONLY final clean text translation."},
                                         {"role": "user", "content": f"Translate this human draft:\n\n{english_reply}"}],
                            "temperature": 0.0, "max_tokens": 1500
                        }
                        final_native_reply = send_nvidia_request_with_retry(rev_payload, status_box) if "english" not in detected_languages.lower() else english_reply
                        
                        if final_native_reply:
                            status_box.empty()
                            st.markdown(f"""
                                <div class="metric-card">
                                    <strong>🌍 Languages Spoken:</strong> {detected_languages}<br>
                                    <strong>🎭 Style Profile Tone:</strong> {detected_tone}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("<br>📊 **English Processing Step:**", unsafe_allow_html=True)
                            st.caption(translation_output)
                            
                            st.markdown("<br>🚀 **Automated Response Generated (Native Language Copy):**", unsafe_allow_html=True)
                            st.success(final_native_reply)
                            
                            raw_from = selected_msg.get("From")
                            sender_name, sender_email = email.utils.parseaddr(raw_from)
                            raw_subject, encoding = decode_header(selected_msg.get("Subject", ""))[0]
                            if isinstance(raw_subject, bytes):
                                raw_subject = raw_subject.decode(encoding or "utf-8", errors="ignore")
                            reply_subject = raw_subject if raw_subject.lower().startswith("re:") else f"Re: {raw_subject}"
                            
                            with st.spinner(f"📤 Auto-dispatching email via SMTP back to {sender_email}..."):
                                try:
                                    msg = MIMEMultipart()
                                    msg['From'] = EMAIL_USER
                                    msg['To'] = sender_email
                                    msg['Subject'] = reply_subject
                                    msg.attach(MIMEText(final_native_reply, 'plain', 'utf-8'))
                                    
                                    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                                    server.login(EMAIL_USER, EMAIL_PASS)
                                    server.sendmail(EMAIL_USER, sender_email, msg.as_string())
                                    server.close()
                                    st.toast(f"Outbound reply delivered smoothly to {sender_email}!", icon="✅")
                                except Exception as smtp_err:
                                    st.error(f"SMTP Outbound Transmission Error: {smtp_err}")
                else:
                    status_box.error("Processing halted: The email body contains zero text metrics.")
        else:
            st.warning("Selected email contains no evaluation fields.")
