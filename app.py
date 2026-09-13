import streamlit as st
import streamlit.components.v1 as components
import os
import json
import re
import urllib.parse
import base64
from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import database and services
from database.database import (
    init_db,
    save_consultation,
    get_recent_consultations,
    clear_history
)
from services.safety_service import (
    check_query_safety,
    get_safety_disclaimer,
    format_missing_info_check
)
from services.ai_service import (
    get_api_key,
    get_ai_agricultural_advice
)

# Page Configuration
st.set_page_config(
    page_title="KhetIQ AI - Your AI Farming Companion",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Database
init_db()

# Base64 Helper for fixed non-clickable images
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# HTML Indentation Cleaner (Prevents Streamlit Markdown from parsing indented HTML lines as code blocks)
def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.splitlines() if line.strip()])

# Full Advisory Solution Report Generator
def generate_full_advisory_report(crop, lang, village, district, state, adv):
    t_sec = LANG_DATA.get(lang, LANG_DATA["Hindi"])["sections"]
    
    loc_parts = [x for x in [village, district, state] if x and x.strip()]
    loc_str = ", ".join(loc_parts) if loc_parts else ("Not Specified" if lang == "English" else "निर्दिष्ट नहीं")
    
    report_lines = []
    report_lines.append("="*65)
    report_lines.append(f"          🌾 KHETIQ AI - FULL CROP ADVISORY & SOLUTION REPORT 🌾")
    report_lines.append("="*65)
    report_lines.append(f"Crop / फ़सल: {crop}")
    report_lines.append(f"Language / भाषा: {lang}")
    report_lines.append(f"Location / स्थान: {loc_str}")
    report_lines.append("-" * 65)
    report_lines.append("")
    
    # 1. Problem Understanding
    report_lines.append(f"💡 1. {t_sec['problem'].upper()}:")
    report_lines.append(f"{adv.get('problem_understanding', 'N/A')}")
    report_lines.append("")
    
    # 2. Recommended Actions & Solutions
    report_lines.append(f"✅ 2. {t_sec['actions'].upper()} (SOLUTION STEPS):")
    actions = adv.get('recommended_actions', [])
    if isinstance(actions, list):
        for idx, act in enumerate(actions, 1):
            report_lines.append(f"   [{idx}] {act}")
    else:
        report_lines.append(f"   - {actions}")
    report_lines.append("")
    
    # 3. Possible Causes
    report_lines.append(f"🔍 3. {t_sec['causes'].upper()}:")
    causes = adv.get('possible_causes', [])
    if isinstance(causes, list):
        for idx, c in enumerate(causes, 1):
            report_lines.append(f"   [{idx}] {c}")
    else:
        report_lines.append(f"   - {causes}")
    report_lines.append("")
    
    # 4. Prevention Tips
    report_lines.append(f"🛡️ 4. {t_sec['prevention'].upper()}:")
    prevs = adv.get('prevention_tips', [])
    if isinstance(prevs, list):
        for idx, p in enumerate(prevs, 1):
            report_lines.append(f"   [{idx}] {p}")
    else:
        report_lines.append(f"   - {prevs}")
    report_lines.append("")
    
    # 5. Missing Info Needed
    missing = adv.get('missing_information', [])
    if missing:
        report_lines.append(f"❓ 5. {t_sec['missing'].upper()}:")
        for idx, m in enumerate(missing, 1):
            report_lines.append(f"   [{idx}] {m}")
        report_lines.append("")
    
    # 6. Contact Expert Guidance
    report_lines.append(f"👨‍🌾 6. {t_sec['expert'].upper()}:")
    exp = adv.get('when_to_contact_expert', [])
    if isinstance(exp, list):
        for idx, e in enumerate(exp, 1):
            report_lines.append(f"   [{idx}] {e}")
    else:
        report_lines.append(f"   - {exp}")
    report_lines.append("")
    
    report_lines.append("="*65)
    report_lines.append("Emergency Expert Hotline (Kisan Call Center): 1800-180-1551 (Toll-Free)")
    report_lines.append("KhetIQ AI - Smart Answers. Better Harvests.")
    report_lines.append("="*65)
    
    return "\n".join(report_lines)

# Speech Text Sanitizer for Errorless Continuous Pronunciation
def sanitize_text_for_speech(text, lang="Hindi"):
    if not text:
        return ""
    
    # 1. Remove Markdown formatting & HTML
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'<.*?>', '', text)
    
    # 2. Common abbreviations and dot cleanups to prevent letter-by-letter spelling
    text = re.sub(r'\be\.g\.\b', 'for example', text, flags=re.IGNORECASE)
    text = re.sub(r'\bi\.e\.\b', 'that is', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDr\.\b', 'Doctor', text, flags=re.IGNORECASE)

    if lang == "Hindi":
        text = text.replace("₹", " रुपये ").replace("%", " प्रतिशत ")
        text = text.replace("KVK", "कृषि विज्ञान केंद्र").replace("DAP", "डीएपी").replace("NPK", "एनपीके")
        text = text.replace("PM-KISAN", "पीएम किसान").replace("PMFBY", "पीएम फसल बीमा")
        text = text.replace("kg/ha", "किलोग्राम प्रति हेक्टेयर").replace("kg", "किलोग्राम")
        text = text.replace("KhetIQ", "खेती आईक्यू")
        text = text.replace("/", " या ")
        text = re.sub(r'(\d+)\.(\d+)', r'\1 दशमलव \2', text)
    elif lang == "Hinglish":
        text = text.replace("₹", " rupees ").replace("%", " percent ")
        text = text.replace("KVK", "Krishi Vigyan Kendra").replace("DAP", "D A P").replace("NPK", "N P K")
        text = text.replace("PM-KISAN", "PM Kisan").replace("PMFBY", "PM Fasal Bima")
        text = text.replace("kg/ha", "kg per hectare").replace("kg", "kg")
        text = text.replace("KhetIQ", "Kheti I Q")
        text = text.replace("/", " ya ")
        text = re.sub(r'(\d+)\.(\d+)', r'\1 point \2', text)
    else:
        text = text.replace("₹", " rupees ").replace("%", " percent ")
        text = text.replace("KVK", "Krishi Vigyan Kendra").replace("DAP", "D A P").replace("NPK", "N P K")
        text = text.replace("PM-KISAN", "P M Kisan").replace("PMFBY", "P M Fasal Bima")
        text = text.replace("kg/ha", "kilograms per hectare").replace("kg", "kilograms")
        text = text.replace("KhetIQ", "Kheti I Q")
        text = text.replace("/", " or ")
        text = re.sub(r'(\d+)\.(\d+)', r'\1 point \2', text)

    # 3. Strip Emojis and non-speakable Unicode ranges
    text = re.sub(r'[^\w\s\u0900-\u097F.,!?\-]', ' ', text)

    # 4. Clean up repetitive dashes or punctuation
    text = re.sub(r'[-_]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# Session State Initialization
if "selected_lang" not in st.session_state:
    st.session_state["selected_lang"] = "Hindi"
if "active_nav_tab" not in st.session_state:
    st.session_state["active_nav_tab"] = "Home"
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "advisor"
if "latest_advice" not in st.session_state:
    st.session_state["latest_advice"] = None
if "latest_crop" not in st.session_state:
    st.session_state["latest_crop"] = "Wheat"
if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

lang = st.session_state["selected_lang"]

# ---------------------------------------------------------
# Dynamic High-Contrast Farmer Theme CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Base Reset & Typography */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1320px !important;
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Prevent Image Selection/Lightbox Click */
    img {
        pointer-events: none !important;
        user-select: none !important;
    }

    /* Interactive Example Card Links */
    .example-card-link {
        text-decoration: none !important;
        color: inherit !important;
        display: block;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer !important;
    }
    .example-card-link:hover {
        transform: translateY(-4px);
    }
    .example-card-link:hover .example-card-inner {
        box-shadow: 0 8px 24px rgba(22, 128, 61, 0.25) !important;
        border-color: #16a34a !important;
    }

    /* Hero Banner Section */
    .hero-card {
        background: linear-gradient(135deg, #052e16 0%, #15803d 60%, #1e3a8a 100%);
        border-radius: 24px;
        padding: 28px 32px;
        color: #ffffff !important;
        box-shadow: 0 12px 32px rgba(5, 46, 22, 0.35);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 900;
        margin: 0;
        color: #ffffff !important;
        line-height: 1.1;
    }
    .hero-sub {
        font-size: 1.3rem;
        color: #dcfce7 !important;
        font-weight: 700;
        margin-top: 6px;
    }
    .hero-hindi {
        font-size: 1.15rem;
        color: #fef08a !important;
        font-weight: 600;
        margin-top: 6px;
    }

    .hero-badge-pill {
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 30px;
        padding: 6px 14px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
        margin-top: 8px;
    }

    /* Process Flow Indicator Bar */
    .process-bar-container {
        background: #ffffff;
        border: 2px solid #bbf7d0;
        border-radius: 16px;
        padding: 12px 18px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .process-step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        color: #14532d;
    }
    .process-step-badge {
        background: #16a34a;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.9rem;
    }

    /* Sidebar Cards */
    .sidebar-info-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 18px;
        border: 2px solid #e2e8f0;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .sidebar-card-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #14532d;
        margin-top: 0;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-list-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
        font-weight: 600;
        color: #334155;
    }

    /* Guided 3-Column Form Containers */
    .form-column-box {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        height: 100%;
    }
    .form-column-header {
        font-size: 1.05rem;
        font-weight: 800;
        color: #14532d;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 8px;
    }

    /* High Contrast Advisory Response Cards */
    .card-box {
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.07);
        border-width: 2px;
        border-style: solid;
    }
    .card-title-text {
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .box-problem { background-color: #f0f9ff !important; border-color: #0284c7 !important; }
    .box-problem .card-title-text { color: #0369a1 !important; }
    .box-problem p, .box-problem li { color: #0f172a !important; font-weight: 500; font-size: 1.02rem; }

    .box-causes { background-color: #fffbe6 !important; border-color: #d97706 !important; }
    .box-causes .card-title-text { color: #b45309 !important; }
    .box-causes p, .box-causes li { color: #1c1917 !important; font-weight: 500; font-size: 1.02rem; }

    .box-actions { background-color: #f0fdf4 !important; border-color: #16a34a !important; }
    .box-actions .card-title-text { color: #15803d !important; }
    .box-actions p, .box-actions li { color: #052e16 !important; font-weight: 600; font-size: 1.02rem; }

    .box-prevention { background-color: #faf5ff !important; border-color: #9333ea !important; }
    .box-prevention .card-title-text { color: #6b21a8 !important; }
    .box-prevention p, .box-prevention li { color: #1e1b4b !important; font-weight: 500; font-size: 1.02rem; }

    .box-missing { background-color: #fff1f2 !important; border-color: #e11d48 !important; }
    .box-missing .card-title-text { color: #be123c !important; }
    .box-missing p, .box-missing li { color: #4c0519 !important; font-weight: 500; font-size: 1.02rem; }

    .box-expert { background-color: #fdf2f8 !important; border-color: #db2777 !important; }
    .box-expert .card-title-text { color: #9d174d !important; }
    .box-expert p, .box-expert li { color: #500724 !important; font-weight: 500; font-size: 1.02rem; }

    /* Post Advice Tools Bar */
    .tools-bar-card {
        background-color: #f0fdf4;
        border: 2px solid #bbf7d0;
        border-radius: 16px;
        padding: 16px 20px;
        margin-top: 18px;
        margin-bottom: 20px;
    }

    /* Warning Banner */
    .warning-banner {
        background-color: #fffbe6;
        border: 2px solid #f59e0b;
        border-radius: 14px;
        padding: 16px 20px;
        color: #92400e !important;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Large Green Action Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        border-radius: 14px !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 14px rgba(22, 128, 61, 0.35) !important;
        width: 100%;
        transition: all 0.25s ease !important;
        min-height: 46px;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
        box-shadow: 0 6px 18px rgba(22, 128, 61, 0.45) !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Clean Multilingual Text Dictionaries
# ---------------------------------------------------------
LANG_DATA = {
    "Hindi": {
        "nav_home": "🏠 मुख्य पृष्ठ",
        "nav_ask": "💬 फ़सल सलाह",
        "nav_guide": "🌱 फ़सल गाइड",
        "nav_schemes": "🏛️ योजनाएं",
        "nav_weather": "☀️ मौसम",
        "nav_history": "🕒 इतिहास",
        "nav_about": "ℹ️ जानकारी",
        "hero_title": "KhetIQ AI (खेती-आईक्यू)",
        "hero_companion": "आपका एआई कृषि साथी",
        "hero_sub": "अपनी फ़सल की समस्या बताएं। आसान सलाहएं पाएं।",
        "hero_hindi": "किसान भाइयों के लिए हमेशा साथ — एआई-संचालित कृषि मार्गदर्शन।",
        "badge1": "💬 हर समय विशेषज्ञ सलाह",
        "badge2": "🗣️ हिंदी, अंग्रेजी और हिंग्लिश",
        "badge3": "📷 फ़सल फ़ोटो विश्लेषण",
        "badge4": "🌱 हर किसान के लिए आसान",
        "farmer_quote": "हर किसान का सवाल, हमारा साथ 🌾",
        "farmer_sub": "सटीक जानकारी से बेहतर पैदावार और समृद्ध किसान।",
        "process_1": "1. फ़सल और भाषा चुनें",
        "process_2": "2. खेत की जानकारी दें",
        "process_3": "3. समस्या बताएं",
        "process_4": "4. AI सलाह पाएं",
        "why_title": "🌱 खेती-आईक्यू AI क्यों?",
        "why_1_title": "सरल और स्पष्ट",
        "why_1_sub": "भारत के हर किसान के लिए आसान",
        "why_2_title": "बहुभाषी",
        "why_2_sub": "हिंदी, अंग्रेजी और हिंग्लिश सहायता",
        "why_3_title": "आवाज़ सहायता",
        "why_3_sub": "टाइप करने की जगह बोलकर बताएं",
        "why_4_title": "किसान प्राथमिकता",
        "why_4_sub": "खेती की वास्तविक आवश्यकताओं पर निर्मित",
        "learn_title": "💡 आसान चरणों में खेती सीखें",
        "sec1_header": "1️⃣ अपनी फ़सल और भाषा चुनें",
        "select_lang": "अपनी भाषा चुनें:",
        "select_crop": "अपनी फ़सल चुनें:",
        "custom_crop": "अपनी फ़सल का नाम लिखें:",
        "custom_crop_ph": "उदा. सरसों, कपास, चना, मिर्च",
        "crop_age": "फ़सल की उम्र / अवस्था:",
        "crop_age_ph": "उदा. बुआई के 30 दिन बाद",
        "sec2_header": "2️⃣ अपने खेत की जानकारी दें",
        "village": "गांव का नाम:",
        "district": "ज़िला:",
        "state": "राज्य:",
        "weather": "हाल के मौसम की स्थिति:",
        "weather_ph": "उदा. नमी व कोहरा, तेज धूप",
        "spray": "हाल में दिए गए उर्वरक या छिड़काव:",
        "spray_ph": "उदा. यूरिया दिया, नीम तेल",
        "sec3_header": "3️⃣ अपनी फ़सल की समस्या बताएं",
        "quick_presets": "त्वरित लक्षण (भरने के लिए क्लिक करें):",
        "question_label": "अपनी समस्या लिखें या सवाल पूछें:",
        "question_ph": "यहां अपनी समस्या का विवरण लिखें...",
        "voice_btn": "🎙️ बोलकर बताएं (माइक दबाएं)",
        "photo_label": "📷 फ़सल की फ़ोटो लगाएं (ऐच्छिक)",
        "submit_btn": "✨ AI सलाह प्राप्त करें 🚀",
        "advice_results_title": "📊 खेती-आईक्यू AI सलाह परिणाम",
        "quick_tools_title": "🤖 AI सलाह के बाद त्वरित उपकरण",
        "listen": "🔊 सलाह सुनें:",
        "save_report": "💾 रिपोर्ट सहेजें",
        "copy_text": "📋 कॉपी करें",
        "ask_followup": "❓ अगला सवाल पूछें",
        "new_consult": "🔄 नई सलाह लें",
        "try_examples_title": "💡 उदाहरण सवाल (प्रयोग करके देखें)",
        "try_this_btn": "यह सवाल प्रयोग करें",
        "ex1_title": "मेरे गेहूं के पत्ते पीले हो रहे हैं, क्या करूं?",
        "ex2_title": "पत्तों पर कीड़े लगे हैं, क्या करें?",
        "ex3_title": "पत्तों पर काले दाग हैं, क्या करें?",
        "warning_title": "⚠️ महत्वपूर्ण सूचना:",
        "warning_text": "KhetIQ AI सामान्य कृषि सलाह प्रदान करता है। यह किसी योग्य कृषि विशेषज्ञ या Krishi Vigyan Kendra (KVK) की भौतिक जांच का विकल्प नहीं है। रासायनिक दवा/कीटनाशक का उपयोग करने से पहले स्थानीय कृषि अधिकारी से सलाह अवश्य लें।",
        "history_title": "📜 सहेजा गया पिछला परामर्श इतिहास",
        "clear_history_btn": "🗑️ इतिहास साफ़ करें",
        "schemes_page_title": "भारत सरकार की सभी प्रमुख कृषि योजनाएं",
        "schemes_page_sub": "किसान भाइयों के लिए सरकारी सहायता, अनुदान, बीमा और ऋण योजनाओं की पूरी जानकारी।",
        "mandi_page_title": "देश की प्रमुख मंडियों के ताज़ा फ़सल भाव (Agmarknet Mandi Prices)",
        "mandi_page_sub": "गेहूं, धान, सरसों, मक्का और सब्जियों के आज के न्यूनतम, अधिकतम और औसत मंडी रेट देखें।",
        "back_to_advisor": "⬅️ मुख्य फ़सल सलाह पृष्ठ पर लौटें",
        "ask_ai_scheme_btn": "इस योजना के बारे में AI से पूछें",
        "ask_ai_mandi_btn": "बिक्री रणनीति पर AI सलाह पाएं",
        "sections": {
            "problem": "समस्या की समझ",
            "causes": "संभावित कारण",
            "actions": "सुझाए गए कदम",
            "prevention": "बचाव एवं सुरक्षा के उपाय",
            "missing": "अतिरिक्त आवश्यक जानकारी",
            "expert": "कृषि विशेषज्ञ से कब संपर्क करें"
        }
    },
    "English": {
        "nav_home": "🏠 Home",
        "nav_ask": "💬 Ask AI",
        "nav_guide": "🌱 Crop Guide",
        "nav_schemes": "🏛️ Schemes",
        "nav_weather": "☀️ Weather",
        "nav_history": "🕒 History",
        "nav_about": "ℹ️ About",
        "hero_title": "KhetIQ AI",
        "hero_companion": "Your AI Farming Companion",
        "hero_sub": "Ask your farming problem. Get simple guidance.",
        "hero_hindi": "Always by your side — AI-powered farming advisor.",
        "badge1": "💬 Expert Advice Anytime",
        "badge2": "🗣️ Hindi, English & Hinglish",
        "badge3": "📷 Crop Photo Analysis",
        "badge4": "🌱 Simple for Every Farmer",
        "farmer_quote": "Every Farmer's Question, Supported by Us 🌾",
        "farmer_sub": "Accurate information for better harvest and prosperous farmers.",
        "process_1": "1. Select Crop & Language",
        "process_2": "2. Provide Farm Details",
        "process_3": "3. Describe Problem",
        "process_4": "4. Get AI Advice",
        "why_title": "🌱 Why KhetIQ AI?",
        "why_1_title": "Simple & Clear",
        "why_1_sub": "Easy for every farmer in India",
        "why_2_title": "Multilingual",
        "why_2_sub": "Hindi, English & Hinglish support",
        "why_3_title": "Voice Support",
        "why_3_sub": "Speak instead of typing",
        "why_4_title": "Farmer First",
        "why_4_sub": "Built for real field needs",
        "learn_title": "💡 Learn Farming in Simple Steps",
        "sec1_header": "1️⃣ Choose Crop & Language",
        "select_lang": "Select Language:",
        "select_crop": "Select Your Crop:",
        "custom_crop": "Specify Crop Name:",
        "custom_crop_ph": "e.g. Mustard, Cotton, Gram",
        "crop_age": "Crop Age / Growth Stage:",
        "crop_age_ph": "e.g. 30 days post sowing",
        "sec2_header": "2️⃣ Tell Us About Your Farm",
        "village": "Village Name:",
        "district": "District Name:",
        "state": "State Name:",
        "weather": "Recent Weather Conditions:",
        "weather_ph": "e.g. Humidity & fog, hot sun",
        "spray": "Recent Fertilizers / Sprays Applied:",
        "spray_ph": "e.g. Urea top dressing, Neem oil",
        "sec3_header": "3️⃣ Describe Your Crop Problem",
        "quick_presets": "Quick Symptom Presets (Click to Auto-Fill):",
        "question_label": "Describe Symptoms or Ask a Question:",
        "question_ph": "Write your crop problem details here...",
        "voice_btn": "🎙️ Speak Question (Voice Input)",
        "photo_label": "📷 Upload Crop Photo (Optional)",
        "submit_btn": "✨ Get AI Advice 🚀",
        "advice_results_title": "📊 KhetIQ AI Advisory Results",
        "quick_tools_title": "🤖 AI Advisory Quick Tools",
        "listen": "🔊 Listen to Advice:",
        "save_report": "💾 Save Report",
        "copy_text": "📋 Copy Text",
        "ask_followup": "❓ Ask Follow-up",
        "new_consult": "🔄 New Consultation",
        "try_examples_title": "💡 Example Questions (Click to Try)",
        "try_this_btn": "Try This Question",
        "ex1_title": "My wheat leaves are turning yellow, what should I do?",
        "ex2_title": "Insects are attacking crop leaves, what to do?",
        "ex3_title": "Dark fungal spots are spreading on leaves, what to do?",
        "warning_title": "⚠️ Important Notice:",
        "warning_text": "KhetIQ AI provides informational agricultural advice based on AI models and standard agronomic practices. It does NOT replace physical field inspection by a certified Krishi Vigyan Kendra (KVK) scientist.",
        "history_title": "📜 Saved Consultation History",
        "clear_history_btn": "🗑️ Clear History",
        "schemes_page_title": "All Government Agricultural Schemes",
        "schemes_page_sub": "Complete details on benefits, eligibility, documents, and application steps for Indian farmers.",
        "mandi_page_title": "Live Crop Mandi Prices & Market Rates",
        "mandi_page_sub": "Compare daily minimum, maximum, and modal mandi prices (₹/Quintal) across major mandis.",
        "back_to_advisor": "⬅️ Back to Crop Advisory Form",
        "ask_ai_scheme_btn": "Ask AI About This Scheme",
        "ask_ai_mandi_btn": "Get AI Market Selling Guidance",
        "sections": {
            "problem": "Problem Understanding",
            "causes": "Possible Causes",
            "actions": "Recommended Actions",
            "prevention": "Prevention & Protection Tips",
            "missing": "Missing Information Needed",
            "expert": "When to Contact Agricultural Expert"
        }
    },
    "Hinglish": {
        "nav_home": "🏠 Home",
        "nav_ask": "💬 Ask AI",
        "nav_guide": "🌱 Fasal Guide",
        "nav_schemes": "🏛️ Schemes",
        "nav_weather": "☀️ Weather",
        "nav_history": "🕒 History",
        "nav_about": "ℹ️ About",
        "hero_title": "KhetIQ AI",
        "hero_companion": "Aapka AI Farming Partner",
        "hero_sub": "Apne khet ki samasya batayein. Aasaan salah paayein.",
        "hero_hindi": "Kisaan bhaio ke liye hamesha saath — AI-powered guidance.",
        "badge1": "💬 Expert Advice Anytime",
        "badge2": "🗣️ Hindi, English & Hinglish",
        "badge3": "📷 Crop Photo Analysis",
        "badge4": "🌱 Simple for Every Farmer",
        "farmer_quote": "Har Kisaan Ka Sawal, Humara Saath 🌾",
        "farmer_sub": "Sateek jankari se behtar paidaawar aur samriddh kisaan.",
        "process_1": "1. Fasal & Bhasha Chunein",
        "process_2": "2. Khet Ki Jankari Dein",
        "process_3": "3. Samasya Batayein",
        "process_4": "4. AI Salah Paayein",
        "why_title": "🌱 KhetIQ AI Kyun?",
        "why_1_title": "Simple & Clear",
        "why_1_sub": "Har kisaan ke liye aasaan",
        "why_2_title": "Multilingual",
        "why_2_sub": "Hindi, English & Hinglish support",
        "why_3_title": "Voice Support",
        "why_3_sub": "Typing ki jagah bolkar batayein",
        "why_4_title": "Farmer First",
        "why_4_sub": "Kheti ki real needs par aadharit",
        "learn_title": "💡 Easy Steps Mein Kheti Seekhein",
        "sec1_header": "1️⃣ Fasal & Language Choose Karein",
        "select_lang": "Language Select Karein:",
        "select_crop": "Apni Crop Choose Karein:",
        "custom_crop": "Crop Ka Name Type Karein:",
        "custom_crop_ph": "e.g. Sarson, Kapaas, Chana",
        "crop_age": "Crop Ki Age / Growth Stage:",
        "crop_age_ph": "e.g. 30 days after sowing",
        "sec2_header": "2️⃣ Khet Ki Details Dein",
        "village": "Gaon Ka Name:",
        "district": "Zila Name:",
        "state": "Rajya Name:",
        "weather": "Recent Weather Condition:",
        "weather_ph": "e.g. Fog & humidity, hot sun",
        "spray": "Recent Sprays / Fertilizer Applied:",
        "spray_ph": "e.g. Urea top dressing, Neem oil",
        "sec3_header": "3️⃣ Crop Problem Batayein",
        "quick_presets": "Quick Symptom Presets (Click to Fill):",
        "question_label": "Symptoms Describe Karein ya Question Poochhein:",
        "question_ph": "Apni problem yahan likhein...",
        "voice_btn": "🎙️ Bolkar Batayein (Voice Input)",
        "photo_label": "📷 Crop Photo Upload Karein (Optional)",
        "submit_btn": "✨ AI Salah Paayein 🚀",
        "advice_results_title": "📊 KhetIQ AI Advisory Results",
        "quick_tools_title": "🤖 AI Advisory Quick Tools",
        "listen": "🔊 Salah Suniye:",
        "save_report": "💾 Report Save Karein",
        "copy_text": "📋 Copy Karein",
        "ask_followup": "❓ Agla Sawal Poochhein",
        "new_consult": "🔄 Nayi Salah Lein",
        "try_examples_title": "💡 Example Questions (Try Karein)",
        "try_this_btn": "Yeh Sawal Try Karein",
        "ex1_title": "Gehun ke patte peele ho rahe hain, kya karein?",
        "ex2_title": "Patton par keede lage hain, kya karein?",
        "ex3_title": "Patton par kaale daag hain, kya karein?",
        "warning_title": "⚠️ Important Notice:",
        "warning_text": "KhetIQ AI general agricultural guidance provide karta hai. Yeh KVK scientist ki physical field testing ka replacement nahi hai.",
        "history_title": "📜 Saved Consultation History",
        "clear_history_btn": "🗑️ Clear History",
        "schemes_page_title": "Sabhi Government Agriculture Schemes",
        "schemes_page_sub": "Farmers ke liye govt financial help, insurance, loan & subsidy schemes ki poori jankari.",
        "mandi_page_title": "Aaj Ke Taaza Crop Mandi Bhav & Market Rates",
        "mandi_page_sub": "Gehun, Dhaan, Sarson, Tamatar ke aaj ke Mandi rates (₹/Quintal) dekhein.",
        "back_to_advisor": "⬅️ Main Crop Advisory Page Par Lautne",
        "ask_ai_scheme_btn": "Is Scheme Ke Baare Mein AI Se Poochhein",
        "ask_ai_mandi_btn": "Market Selling Strategy Par AI Salah Paayein",
        "sections": {
            "problem": "Problem Understanding",
            "causes": "Possible Causes",
            "actions": "Recommended Actions",
            "prevention": "Prevention Tips",
            "missing": "Missing Info Needed",
            "expert": "Expert Se Kab Contact Karein"
        }
    }
}

# ---------------------------------------------------------
# Handle URL Query Parameters for Example Question Card Clicks
# ---------------------------------------------------------
if "example_q" in st.query_params:
    q_num = str(st.query_params.get("example_q", ""))
    try:
        del st.query_params["example_q"]
    except Exception:
        pass
    
    t_curr = LANG_DATA.get(st.session_state.get("selected_lang", "Hindi"), LANG_DATA["Hindi"])
    if q_num == "1":
        st.session_state["question_input"] = t_curr["ex1_title"]
        st.session_state["latest_crop"] = "Wheat"
    elif q_num == "2":
        st.session_state["question_input"] = t_curr["ex2_title"]
    elif q_num == "3":
        st.session_state["question_input"] = t_curr["ex3_title"]
    st.session_state["active_view"] = "advisor"

# Crop Options per Language
CROPS_GRID_DATA = {
    "Hindi": [
        ("🌾", "गेहूं", "Wheat"),
        ("🌾", "धान", "Rice"),
        ("🌽", "मक्का", "Maize"),
        ("🍅", "टमाटर", "Tomato"),
        ("🥔", "आलू", "Potato"),
        ("🎋", "गन्ना", "Sugarcane"),
        ("🌱", "अन्य फ़सल", "Other")
    ],
    "English": [
        ("🌾", "Wheat", "Wheat"),
        ("🌾", "Rice", "Rice"),
        ("🌽", "Maize", "Maize"),
        ("🍅", "Tomato", "Tomato"),
        ("🥔", "Potato", "Potato"),
        ("🎋", "Sugarcane", "Sugarcane"),
        ("🌱", "Other Crop", "Other")
    ],
    "Hinglish": [
        ("🌾", "Wheat (Gehun)", "Wheat"),
        ("🌾", "Rice (Dhaan)", "Rice"),
        ("🌽", "Maize (Makka)", "Maize"),
        ("🍅", "Tomato (Tamatar)", "Tomato"),
        ("🥔", "Potato (Aloo)", "Potato"),
        ("🎋", "Sugarcane (Ganna)", "Sugarcane"),
        ("🌱", "Other Crop", "Other")
    ]
}

# Symptom Presets per Language
SYMPTOM_PRESETS = {
    "Hindi": [
        ("🍂", "पत्ते पीले", "पत्तियों के सिरे और नीचे की पत्तियां पीली पड़ रही हैं।"),
        ("🐛", "कीड़े लगे", "कीड़े पत्तियां खा रहे हैं और तने को नुकसान पहुंचा रहे हैं।"),
        ("🍄", "फंगल धब्बे", "पत्तियों पर भूरे या काले रंग के धब्बे फैल रहे हैं।"),
        ("🥀", "पौधे मुरझाना", "सिंचाई के बावजूद पौधे तने से मुरझा और सूख रहे हैं।"),
        ("🌱", "कम बढ़वार", "फ़सल की बढ़वार रुकी हुई है और कल्ले कम निकल रहे हैं।"),
        ("🌀", "पत्ते मुड़ना", "पत्ते ऊपर की तरफ मुड़ रहे हैं और छोटे हो रहे हैं।")
    ],
    "English": [
        ("🍂", "Yellowing", "Leaf tips and lower leaves are turning yellow."),
        ("🐛", "Insect Attack", "Insects eating leaf holes and stems."),
        ("🍄", "Fungal Spots", "Dark fungal spots spreading on leaves."),
        ("🥀", "Wilting", "Plants wilting and drying up from stems."),
        ("🌱", "Poor Growth", "Crop growth is stunted with short tillers."),
        ("🌀", "Leaf Curling", "Leaves curling upwards and shrinking.")
    ],
    "Hinglish": [
        ("🍂", "Patte Peele", "Patte peele ho rahe hain."),
        ("🐛", "Keede Lage", "Keede patton ko kha rahe hain."),
        ("🍄", "Fungal Spots", "Patton par daag phail rahe hain."),
        ("🥀", "Murjha Raha H", "Paudhe sookh rahe hain."),
        ("🌱", "Badhwar Kam", "Crop ki growth ruk gayi hai."),
        ("🌀", "Patte Mudna", "Patte upar ki तरफ mud rahe hain.")
    ]
}

# ---------------------------------------------------------
# Comprehensive Government Schemes Dataset
# ---------------------------------------------------------
GOVT_SCHEMES_DATA = {
    "Hindi": [
        {
            "id": "pm_kisan",
            "name": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)",
            "category": "आर्थिक सहायता (Income Support)",
            "benefit": "₹6,000 प्रति वर्ष (₹2,000 की 3 किश्त सीधे बैंक खाते में)",
            "eligibility": ["सभी भूमिधारक किसान परिवार", "भूमि रिकॉर्ड में किसान का नाम अनिवार्य", "सरकारी कर्मचारी / उच्च आय वर्ग के करदाता अपात्र"],
            "documents": ["आधार कार्ड (Aadhaar)", "खसरा/खतौनी भूमि दस्तावेज", "बैंक खाता (DBT सक्षम)", "मोबाइल नंबर"],
            "portal": "https://pmkisan.gov.in",
            "helpline": "155261 / 1800-11-5526",
            "query_preset": "PM-KISAN योजना की किश्त स्थिति और ऑनलाइन आवेदन प्रक्रिया के बारे में विस्तार से बताएं।"
        },
        {
            "id": "pmfby",
            "name": "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
            "category": "फसल सुरक्षा व बीमा (Crop Insurance)",
            "benefit": "प्राकृतिक आपदा, सूखा, बाढ़ व कीट रोग से फसल नुकसान की पूरी भरपाई। कम प्रीमियम रेट (रबी 1.5%, खरीफ 2%, नकदी फसल 5%)।",
            "eligibility": ["अधिसूचित क्षेत्रों में अधिसूचित फसल उगाने वाले सभी किसान", "ऋणी और गैर-ऋणी किसान"],
            "documents": ["बुआई प्रमाण पत्र / पटवारी रिपोर्ट", "भू-स्वामित्व / बटाईदार दस्तावेज", "आधार कार्ड", "बैंक पासबुक"],
            "portal": "https://pmfby.gov.in",
            "helpline": "1800-200-5142",
            "query_preset": "PMFBY फसल बीमा दावा प्रस्तुत करने और नुकसान मूल्यांकन प्रक्रिया की जानकारी दें।"
        },
        {
            "id": "kcc",
            "name": "किसान क्रेडिट कार्ड (Kisan Credit Card - KCC)",
            "category": "कृषि ऋण एवं क्रेडिट (Low Interest Loan)",
            "benefit": "₹3 लाख तक का आसान कृषि ऋण 4% रियायती ब्याज दर पर (समय पर भुगतान पर 3% अतिरिक्त छूट)।",
            "eligibility": ["सभी व्यक्तिगत किसान, बटाईदार और स्वयं सहायता समूह (SHG)", "पशुपालन व मत्स्य पालन किसान"],
            "documents": ["आवेदन पत्र", "पहचान पत्र (आधार / वोटर ID)", "जमीन के खसरे की प्रति", "बैंक खाता विवरण"],
            "portal": "https://myscheme.gov.in/schemes/kcc",
            "helpline": "1800-180-1551",
            "query_preset": "Kisan Credit Card (KCC) बनवाने की प्रक्रिया और ब्याज दर में छूट की पूरी जानकारी दें।"
        },
        {
            "id": "soil_card",
            "name": "मृदा स्वास्थ्य कार्ड योजना (Soil Health Card Scheme)",
            "category": "मिट्टी परीक्षण व उर्वरक (Soil Care)",
            "benefit": "प्रत्येक 2 वर्ष में खेत की मिट्टी की मुफ्त जांच। 12 पोषक तत्वों की स्थिति और संतुलित उर्वरक प्रयोग की सिफारिश।",
            "eligibility": ["भारत के सभी किसान अपने खेत की मिट्टी का नि:शुल्क परीक्षण करवा सकते हैं।"],
            "documents": ["खेत से मिट्टी का नमूना", "किसान का आधार कार्ड", "मोबाइल नंबर"],
            "portal": "https://soilhealth.dac.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "Soil Health Card के अनुसार मिट्टी परीक्षण और यूरिया/DAP के सही संतुलन की जानकारी दें।"
        },
        {
            "id": "pkvy",
            "name": "परम्परागत कृषि विकास योजना (PKVY - Organic Farming)",
            "category": "जैविक खेती अनुदान (Organic Subsidy)",
            "benefit": "3 वर्षों के लिए ₹50,000 प्रति हेक्टेयर वित्तीय सहायता (जैविक खाद, बीज, प्रमाणन व बाजार लिंक हेतु)।",
            "eligibility": ["50 या अधिक किसानों का समूह (क्लस्टर) जिसके पास कुल 50 एकड़ भूमि हो।"],
            "documents": ["किसान क्लस्टर पंजीकरण", "भूमि स्वामित्व प्रमाण", "आधार कार्ड", "बैंक विवरण"],
            "portal": "https://pgsindia-ncof.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "PKVY योजना के तहत जैविक खेती क्लस्टर बनाने और ₹50,000 अनुदान पाने की विधि बताएं।"
        },
        {
            "id": "pmksy",
            "name": "प्रधानमंत्री कृषि सिंचाई योजना (PMKSY - Micro Irrigation)",
            "category": "सिंचाई एवं ड्रिप सब्सिडी (Irrigation Support)",
            "benefit": "ड्रिप (टपक) और स्प्रिंकलर (फव्वारा) सिंचाई प्रणाली पर 45% से 55% तक सरकारी सब्सिडी ('प्रति बूंद अधिक फसल')।",
            "eligibility": ["जल स्रोत और कृषि योग्य भूमि वाले सभी किसान। लघु एवं सीमांत किसानों को अधिक सब्सिडी।"],
            "documents": ["जमीन का जमाबंदी/खसरा", "पानी के स्रोत का विवरण (बोरवेल/कुआं)", "आधार कार्ड", "बैंक पासबुक"],
            "portal": "https://pmksy.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "PMKSY योजना के तहत ड्रिप और स्प्रिंकलर सिंचाई सिस्टम पर सब्सिडी प्राप्त करने की प्रक्रिया बताएं।"
        },
        {
            "id": "smam",
            "name": "कृषि यांत्रिकीकरण उप-मिशन (SMAM - Farm Machinery)",
            "category": "ट्रैक्टर व मशीनरी सब्सिडी (Machinery Subsidy)",
            "benefit": "ट्रैक्टर, रोटावेटर, रीपर, कंबाइन और थ्रेशर की खरीद पर 40% से 50% तक की छूट। कस्टम हायरिंग सेंटर हेतु 80% सहायता।",
            "eligibility": ["व्यक्तिगत किसान, कृषि उद्यमी, स्वयं सहायता समूह एवं FPO"],
            "documents": ["किसान पंजीकरण संख्या (DBT Agriculture)", "आधार कार्ड", "बैंक पासबुक", "मशीन कोटेशन"],
            "portal": "https://agrimachinery.nic.in",
            "helpline": "1800-180-1551",
            "query_preset": "SMAM योजना से ट्रैक्टर और आधुनिक कृषि उपकरणों पर 50% सब्सिडी कैसे प्राप्त करें?"
        },
        {
            "id": "kcc_helpline",
            "name": "किसान कॉल सेंटर (Kisan Call Center - 24x7 Helpline)",
            "category": "मुफ्त विशेषज्ञ परामर्श (Free Advisory)",
            "benefit": "22 स्थानीय भाषाओं में फसल बीमारी, मौसम, खाद की मात्रा और मंडी भाव पर कृषि वैज्ञानिकों द्वारा मुफ्त समाधान।",
            "eligibility": ["भारत का कोई भी किसान किसी भी फोन से डायल कर सकता है।"],
            "documents": ["किसी दस्तावेज की आवश्यकता नहीं (नि:शुल्क फोन सेवा)"],
            "portal": "https://agricoop.nic.in",
            "helpline": "1800-180-1551 (टोल-फ्री)",
            "query_preset": "Kisan Call Center टोल-फ्री नंबर 1800-180-1551 पर किस समय और कैसे विशेषज्ञ से बात करें?"
        }
    ],
    "English": [
        {
            "id": "pm_kisan",
            "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
            "category": "Direct Income Support",
            "benefit": "₹6,000 per year transferred directly to bank accounts (3 installments of ₹2,000 each).",
            "eligibility": ["All small and marginal landholding farmer families", "Land record ownership in farmer's name", "Taxpayers & govt employees excluded"],
            "documents": ["Aadhaar Card", "Land Khatauni/Ownership Papers", "DBT Enabled Bank Account", "Mobile Number"],
            "portal": "https://pmkisan.gov.in",
            "helpline": "155261 / 1800-11-5526",
            "query_preset": "Explain PM-KISAN installment status check and online farmer registration steps."
        },
        {
            "id": "pmfby",
            "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "category": "Crop Insurance Protection",
            "benefit": "Comprehensive insurance coverage against crop damage due to weather, pests & diseases. Low premium (1.5% Rabi, 2% Kharif, 5% Commercial).",
            "eligibility": ["All farmers growing notified crops in notified areas", "Loanee and non-loanee farmers"],
            "documents": ["Sowing Certificate / Patwari report", "Land Ownership / Tenant record", "Aadhaar Card", "Bank Passbook"],
            "portal": "https://pmfby.gov.in",
            "helpline": "1800-200-5142",
            "query_preset": "How to claim crop loss compensation under PMFBY insurance scheme?"
        },
        {
            "id": "kcc",
            "name": "Kisan Credit Card (KCC Scheme)",
            "category": "Low Interest Farm Credit",
            "benefit": "Short-term agricultural loan up to ₹3 Lakh at concessional interest rate of 4% (3% prompt repayment incentive).",
            "eligibility": ["Individual farmers, joint borrowers, tenant farmers, self-help groups (SHG)", "Animal husbandry & fisheries farmers"],
            "documents": ["KCC Application Form", "ID Proof (Aadhaar/Voter ID)", "Land record copy (Khasra)", "Bank details"],
            "portal": "https://myscheme.gov.in/schemes/kcc",
            "helpline": "1800-180-1551",
            "query_preset": "Provide full process for applying Kisan Credit Card (KCC) with 4% interest subvention."
        },
        {
            "id": "soil_card",
            "name": "Soil Health Card Scheme",
            "category": "Soil Testing & Fertilizer Guidance",
            "benefit": "Free soil test every 2 years providing 12 nutrient status reports & customized fertilizer recommendations for optimal yield.",
            "eligibility": ["All farmers in India can get soil testing done free of cost."],
            "documents": ["Soil sample from field", "Farmer Aadhaar Card", "Contact number"],
            "portal": "https://soilhealth.dac.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "How to get Soil Health Card recommendations for balanced fertilizer application?"
        },
        {
            "id": "pkvy",
            "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
            "category": "Organic Farming Subsidy",
            "benefit": "Financial grant of ₹50,000 per hectare over 3 years for organic inputs, seeds, certification, and market linkage.",
            "eligibility": ["Farmer clusters of 50 or more farmers holding a total of 50 acres cultivable land."],
            "documents": ["Cluster Group Registration", "Land ownership proof", "Aadhaar Card", "Bank Account Details"],
            "portal": "https://pgsindia-ncof.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "Explain PKVY scheme benefits for cluster organic farming subsidy."
        },
        {
            "id": "pmksy",
            "name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
            "category": "Irrigation & Drip Subsidy",
            "benefit": "45% to 55% subsidy on Drip & Sprinkler micro-irrigation systems under 'Per Drop More Crop' initiative.",
            "eligibility": ["Farmers having cultivable land with assured water source. Higher subsidy for small/marginal farmers."],
            "documents": ["Land Revenue record (Khatauni)", "Water source proof (Borewell/Well)", "Aadhaar Card", "Bank Passbook"],
            "portal": "https://pmksy.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "How to apply for 55% subsidy on Drip and Sprinkler irrigation under PMKSY?"
        },
        {
            "id": "smam",
            "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
            "category": "Farm Machinery Subsidy",
            "benefit": "40% to 50% subsidy on buying tractors, rotavators, seed drills & harvesters. Up to 80% for Custom Hiring Centers.",
            "eligibility": ["Individual farmers, agricultural entrepreneurs, SHGs, and Farmer Producer Organizations (FPOs)."],
            "documents": ["Farmer Registration ID (DBT Portal)", "Aadhaar Card", "Bank Passbook", "Machinery Quotation"],
            "portal": "https://agrimachinery.nic.in",
            "helpline": "1800-180-1551",
            "query_preset": "How to get subsidy on tractors and farm implements under SMAM scheme?"
        },
        {
            "id": "kcc_helpline",
            "name": "Kisan Call Center (24x7 Free Helpline)",
            "category": "Free Expert Helpline",
            "benefit": "Instant free agricultural advice from scientists in 22 local languages on diseases, weather, fertilizers & mandi rates.",
            "eligibility": ["Accessible to all farmers across India from any mobile or landline."],
            "documents": ["No documents required (Free Telephonic Assistance)"],
            "portal": "https://agricoop.nic.in",
            "helpline": "1800-180-1551 (Toll-Free)",
            "query_preset": "How to call Kisan Call Center toll-free 1800-180-1551 for expert agricultural guidance?"
        }
    ],
    "Hinglish": [
        {
            "id": "pm_kisan",
            "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "category": "Direct Income Help",
            "benefit": "₹6,000 per year directly bank account mein (₹2,000 ki 3 installments).",
            "eligibility": ["Sabhi small & marginal farmer families", "Land record mein farmer ka name hona chahiye"],
            "documents": ["Aadhaar Card", "Khasra/Khatauni land papers", "Bank Account (DBT linked)", "Mobile number"],
            "portal": "https://pmkisan.gov.in",
            "helpline": "155261 / 1800-11-5526",
            "query_preset": "PM-KISAN scheme ki installment status aur online registration process batayein."
        },
        {
            "id": "pmfby",
            "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
            "category": "Crop Insurance",
            "benefit": "Weather, flood ya pest damage par poora crop loss compensation. Low premium (1.5% Rabi, 2% Kharif).",
            "eligibility": ["Notified crop ugane wale sabhi kisaan"],
            "documents": ["Sowing certificate", "Land document", "Aadhaar Card", "Bank Passbook"],
            "portal": "https://pmfby.gov.in",
            "helpline": "1800-200-5142",
            "query_preset": "PMFBY crop insurance claim submit karne aur loss claim ka tareeka batayein."
        },
        {
            "id": "kcc",
            "name": "Kisan Credit Card (KCC Scheme)",
            "category": "Low Interest Loan",
            "benefit": "₹3 Lakh tak ka easy farm loan at 4% effective interest rate.",
            "eligibility": ["Sabhi farmers, tenant farmers, SHG groups"],
            "documents": ["KCC Form", "Aadhaar Card", "Land record copy", "Bank account"],
            "portal": "https://myscheme.gov.in/schemes/kcc",
            "helpline": "1800-180-1551",
            "query_preset": "Kisan Credit Card (KCC) banwane ka full process aur 4% interest discount batayein."
        },
        {
            "id": "soil_card",
            "name": "Soil Health Card Scheme",
            "category": "Soil Testing",
            "benefit": "Har 2 saal mein free mitti test aur fertilizer recommendation card.",
            "eligibility": ["India ke sabhi farmers free soil test kara sakte hain."],
            "documents": ["Mitti ka sample", "Aadhaar Card", "Phone number"],
            "portal": "https://soilhealth.dac.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "Soil Health Card ke according fertilizer dosing ki jankari dein."
        },
        {
            "id": "pkvy",
            "name": "PKVY (Paramparagat Krishi Vikas Yojana)",
            "category": "Organic Farming Subsidy",
            "benefit": "3 saal mein ₹50,000 per hectare grant organic farming ke liye.",
            "eligibility": ["50 ya usse adhik farmers ka group (cluster) with 50 acre land."],
            "documents": ["Cluster registration", "Land proof", "Aadhaar Card", "Bank details"],
            "portal": "https://pgsindia-ncof.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "PKVY organic farming subsidy ₹50,000 lene ki poori jankari dein."
        },
        {
            "id": "pmksy",
            "name": "PMKSY (Micro Irrigation Drip Subsidy)",
            "category": "Irrigation Subsidy",
            "benefit": "Drip & Sprinkler system par 45% se 55% govt subsidy.",
            "eligibility": ["Paani ka source aur kheti ki zameen wale farmers."],
            "documents": ["Land papers", "Borewell/Water source proof", "Aadhaar Card", "Bank passbook"],
            "portal": "https://pmksy.gov.in",
            "helpline": "1800-180-1551",
            "query_preset": "PMKSY scheme mein Drip aur Sprinkler system par 55% subsidy kaise milegi?"
        },
        {
            "id": "smam",
            "name": "SMAM (Farm Machinery Subsidy)",
            "category": "Tractor Machinery Subsidy",
            "benefit": "Tractor, Rotavator & Harvester par 40% - 50% discount subsidy.",
            "eligibility": ["Individual farmers, FPOs & Custom Hiring Centers."],
            "documents": ["Farmer Registration ID", "Aadhaar Card", "Bank Passbook", "Machine Quotation"],
            "portal": "https://agrimachinery.nic.in",
            "helpline": "1800-180-1551",
            "query_preset": "SMAM scheme se tractor aur farm machinery par 50% subsidy lene ka tarika batayein."
        },
        {
            "id": "kcc_helpline",
            "name": "Kisan Call Center (24x7 Helpline)",
            "category": "Free Advice",
            "benefit": "Toll-Free 1800-180-1551 par 22 bhashaon mein free krishi scientist salah.",
            "eligibility": ["Koi bhi kisaan kisi bhi phone se call kar sakta hai."],
            "documents": ["No documents required (Free Service)"],
            "portal": "https://agricoop.nic.in",
            "helpline": "1800-180-1551 (Toll-Free)",
            "query_preset": "Kisan Call Center 1800-180-1551 par kis time call karke doctor se baat karein?"
        }
    ]
}

# ---------------------------------------------------------
# Comprehensive Mandi Commodity Prices Dataset
# ---------------------------------------------------------
MANDI_PRICES_DATA = {
    "Hindi": [
        {
            "crop": "गेहूं (Wheat)",
            "emoji": "🌾",
            "code": "Wheat",
            "mandi": "करनाल (हरियाणा) / इंदौर (म.प्र.) / खन्ना (पंजाब)",
            "min": "₹2,275",
            "max": "₹2,480",
            "modal": "₹2,360",
            "msp": "₹2,275 / कुंतल",
            "trend": "📈 तेजी (+₹25)",
            "trend_type": "up",
            "query_preset": "गेहूं के वर्तमान मंडी भाव तेजी में हैं, क्या अभी बेचना सही रहेगा या रोक कर रखें?"
        },
        {
            "crop": "धान (Paddy / Rice)",
            "emoji": "🌾",
            "code": "Rice",
            "mandi": "अमृतसर (पंजाब) / कुरुक्षेत्र (हरियाणा) / गोंडा (यू.पी.)",
            "min": "₹2,183",
            "max": "₹2,350",
            "modal": "₹2,260",
            "msp": "₹2,183 / कुंतल",
            "trend": "➡️ स्थिर",
            "trend_type": "stable",
            "query_preset": "धान के मंडी रेट और सरकारी खरीद (MSP purchase) की प्रक्रिया के बारे में बताएं।"
        },
        {
            "crop": "सरसों (Mustard / Sarson)",
            "emoji": "🟡",
            "code": "Mustard",
            "mandi": "भरतपुर (राजस्थान) / रेवाड़ी (हरियाणा) / आगरा (यू.पी.)",
            "min": "₹5,450",
            "max": "₹5,880",
            "modal": "₹5,680",
            "msp": "₹5,650 / कुंतल",
            "trend": "📈 मांग में तेजी (+₹60)",
            "trend_type": "up",
            "query_preset": "सरसों के भाव MSP से ऊपर हैं, अच्छी कीमत पाने के लिए बेहतर मंडी रणनीति क्या है?"
        },
        {
            "crop": "मक्का (Maize)",
            "emoji": "🌽",
            "code": "Maize",
            "mandi": "दावणगेरे (कर्नाटक) / गुलाबबाग (बिहार) / छिंदवाड़ा (म.प्र.)",
            "min": "₹2,090",
            "max": "₹2,290",
            "modal": "₹2,160",
            "msp": "₹2,090 / कुंतल",
            "trend": "📈 हल्की तेजी",
            "trend_type": "up",
            "query_preset": "मक्के का मंडी भाव और पोल्ट्री/फीड उद्योग की हालिया मांग की स्थिति बताएं।"
        },
        {
            "crop": "कपास (Cotton / Kapaas)",
            "emoji": "☁️",
            "code": "Cotton",
            "mandi": "राजकोट (गुजरात) / बठिंडा (पंजाब) / यवतमाल (महाराष्ट्र)",
            "min": "₹6,850",
            "max": "₹7,600",
            "modal": "₹7,250",
            "msp": "₹7,020 / कुंतल",
            "trend": "📈 मजबूत मांग",
            "trend_type": "up",
            "query_preset": "कपास के भाव में आगे सुधार होने की संभावना पर सलाह दें।"
        },
        {
            "crop": "चना (Gram / Chana)",
            "emoji": "🧆",
            "code": "Gram",
            "mandi": "लातूर (महाराष्ट्र) / बीकानेर (राजस्थान) / विदिशा (म.प्र.)",
            "min": "₹5,250",
            "max": "₹5,650",
            "modal": "₹5,480",
            "msp": "₹5,440 / कुंतल",
            "trend": "➡️ समान भाव",
            "trend_type": "stable",
            "query_preset": "चने का बाजार भाव और आगामी त्योहारी सीजन की मांग का प्रभाव बताएं।"
        },
        {
            "crop": "टमाटर (Tomato)",
            "emoji": "🍅",
            "code": "Tomato",
            "mandi": "कोलार (कर्नाटक) / नासिक (महाराष्ट्र) / मदनपल्ले (आं.प्र.)",
            "min": "₹1,800",
            "max": "₹2,650",
            "modal": "₹2,250",
            "msp": "मंडी आधारित",
            "trend": "📈 मौसमी तेजी (+₹100)",
            "trend_type": "up",
            "query_preset": "टमाटर के ताज़ा मंडी रेट और खेत से सीधी बिक्री के रास्ते बताएं।"
        },
        {
            "crop": "आलू (Potato)",
            "emoji": "🥔",
            "code": "Potato",
            "mandi": "आगरा (यू.पी.) / हुगली (प.बंगाल) / जालंधर (पंजाब)",
            "min": "₹1,400",
            "max": "₹1,850",
            "modal": "₹1,650",
            "msp": "मंडी आधारित",
            "trend": "📉 आवक अधिक (-₹20)",
            "trend_type": "down",
            "query_preset": "आलू के मंडी रेट कम हैं, कोल्ड स्टोरेज में रखने या बेचने में से क्या बेहतर है?"
        },
        {
            "crop": "प्याज़ (Onion)",
            "emoji": "🧅",
            "code": "Onion",
            "mandi": "लासलगांव (महाराष्ट्र) / नीमच (म.प्र.) / महोबा (यू.पी.)",
            "min": "₹1,900",
            "max": "₹2,850",
            "modal": "₹2,420",
            "msp": "मंडी आधारित",
            "trend": "➡️ स्थिर आवक",
            "trend_type": "stable",
            "query_preset": "प्याज़ के लासलगांव और प्रमुख मंडियों के भाव की स्थिति बताएं।"
        },
        {
            "crop": "गन्ना (Sugarcane)",
            "emoji": "🎋",
            "code": "Sugarcane",
            "mandi": "मेरठ (यू.पी.) / कोल्हापुर (महाराष्ट्र) / यमुनानगर (हरियाणा)",
            "min": "₹315 (FRP)",
            "max": "₹375 (SAP)",
            "modal": "₹355",
            "msp": "FRP ₹315 / कुंतल",
            "trend": "➡️ चीनी मिल चालू",
            "trend_type": "stable",
            "query_preset": "गन्ने के राज्य परामर्शित मूल्य (SAP) और चीनी मिल भुगतान स्थिति की जानकारी दें।"
        }
    ],
    "English": [
        {
            "crop": "Wheat",
            "emoji": "🌾",
            "code": "Wheat",
            "mandi": "Karnal (HR) / Indore (MP) / Khanna (PB)",
            "min": "₹2,275",
            "max": "₹2,480",
            "modal": "₹2,360",
            "msp": "₹2,275 / Qtl",
            "trend": "📈 Firm (+₹25)",
            "trend_type": "up",
            "query_preset": "Wheat mandi prices are firming up. Should I hold or sell current stock?"
        },
        {
            "crop": "Paddy / Rice",
            "emoji": "🌾",
            "code": "Rice",
            "mandi": "Amritsar (PB) / Kurukshetra (HR) / Gonda (UP)",
            "min": "₹2,183",
            "max": "₹2,350",
            "modal": "₹2,260",
            "msp": "₹2,183 / Qtl",
            "trend": "➡️ Steady",
            "trend_type": "stable",
            "query_preset": "Explain Paddy procurement process and Mandi rate trends."
        },
        {
            "crop": "Mustard / Sarson",
            "emoji": "🟡",
            "code": "Mustard",
            "mandi": "Bharatpur (RJ) / Rewari (HR) / Agra (UP)",
            "min": "₹5,450",
            "max": "₹5,880",
            "modal": "₹5,680",
            "msp": "₹5,650 / Qtl",
            "trend": "📈 High Demand (+₹60)",
            "trend_type": "up",
            "query_preset": "Mustard prices are above MSP. How to get maximum market value?"
        },
        {
            "crop": "Maize",
            "emoji": "🌽",
            "code": "Maize",
            "mandi": "Davanagere (KA) / Gulabbagh (BR) / Chhindwara (MP)",
            "min": "₹2,090",
            "max": "₹2,290",
            "modal": "₹2,160",
            "msp": "₹2,090 / Qtl",
            "trend": "📈 Slight Gain",
            "trend_type": "up",
            "query_preset": "What is the demand outlook for Maize in poultry feed industry?"
        },
        {
            "crop": "Cotton / Kapaas",
            "emoji": "☁️",
            "code": "Cotton",
            "mandi": "Rajkot (GJ) / Bathinda (PB) / Yavatmal (MH)",
            "min": "₹6,850",
            "max": "₹7,600",
            "modal": "₹7,250",
            "msp": "₹7,020 / Qtl",
            "trend": "📈 Strong Demand",
            "trend_type": "up",
            "query_preset": "Provide selling advice for Cotton crops based on international rates."
        },
        {
            "crop": "Gram / Chana",
            "emoji": "🧆",
            "code": "Gram",
            "mandi": "Latur (MH) / Bikaner (RJ) / Vidisha (MP)",
            "min": "₹5,250",
            "max": "₹5,650",
            "modal": "₹5,480",
            "msp": "₹5,440 / Qtl",
            "trend": "➡️ Stable",
            "trend_type": "stable",
            "query_preset": "What are current Chana mandi rates and pulse market trends?"
        },
        {
            "crop": "Tomato",
            "emoji": "🍅",
            "code": "Tomato",
            "mandi": "Kolar (KA) / Nashik (MH) / Madanapalle (AP)",
            "min": "₹1,800",
            "max": "₹2,650",
            "modal": "₹2,250",
            "msp": "Market Driven",
            "trend": "📈 Seasonal Upward (+₹100)",
            "trend_type": "up",
            "query_preset": "Give advice on fresh Tomato selling prices and local mandis."
        },
        {
            "crop": "Potato",
            "emoji": "🥔",
            "code": "Potato",
            "mandi": "Agra (UP) / Hooghly (WB) / Jalandhar (PB)",
            "min": "₹1,400",
            "max": "₹1,850",
            "modal": "₹1,650",
            "msp": "Market Driven",
            "trend": "📉 High Arrivals (-₹20)",
            "trend_type": "down",
            "query_preset": "Potato market is down. Is cold storage advisable right now?"
        },
        {
            "crop": "Onion",
            "emoji": "🧅",
            "code": "Onion",
            "mandi": "Lasalgaon (MH) / Neemuch (MP) / Mahoba (UP)",
            "min": "₹1,900",
            "max": "₹2,850",
            "modal": "₹2,420",
            "msp": "Market Driven",
            "trend": "➡️ Balanced Supply",
            "trend_type": "stable",
            "query_preset": "What are the latest Lasalgaon Onion market arrival rates?"
        },
        {
            "crop": "Sugarcane",
            "emoji": "🎋",
            "code": "Sugarcane",
            "mandi": "Meerut (UP) / Kolhapur (MH) / Yamunanagar (HR)",
            "min": "₹315 (FRP)",
            "max": "₹375 (SAP)",
            "modal": "₹355",
            "msp": "FRP ₹315 / Qtl",
            "trend": "➡️ Mills Active",
            "trend_type": "stable",
            "query_preset": "Provide Sugarcane FRP/SAP state prices and payment schedules."
        }
    ],
    "Hinglish": [
        {
            "crop": "Wheat (Gehun)",
            "emoji": "🌾",
            "code": "Wheat",
            "mandi": "Karnal (HR) / Indore (MP) / Khanna (PB)",
            "min": "₹2,275",
            "max": "₹2,480",
            "modal": "₹2,360",
            "msp": "₹2,275 / Qtl",
            "trend": "📈 Tezi (+₹25)",
            "trend_type": "up",
            "query_preset": "Gehun ke mandi rates mein tezi hai. Kya abhi bechein ya rukaayein?"
        },
        {
            "crop": "Paddy (Dhaan)",
            "emoji": "🌾",
            "code": "Rice",
            "mandi": "Amritsar (PB) / Kurukshetra (HR) / Gonda (UP)",
            "min": "₹2,183",
            "max": "₹2,350",
            "modal": "₹2,260",
            "msp": "₹2,183 / Qtl",
            "trend": "➡️ Sthir",
            "trend_type": "stable",
            "query_preset": "Dhaan ke mandi bhav aur govt MSP khareed ki details batayein."
        },
        {
            "crop": "Mustard (Sarson)",
            "emoji": "🟡",
            "code": "Mustard",
            "mandi": "Bharatpur (RJ) / Rewari (HR) / Agra (UP)",
            "min": "₹5,450",
            "max": "₹5,880",
            "modal": "₹5,680",
            "msp": "₹5,650 / Qtl",
            "trend": "📈 Demand Tezi (+₹60)",
            "trend_type": "up",
            "query_preset": "Sarson rates MSP se upar hain, best price paane ka tareeka batayein."
        },
        {
            "crop": "Maize (Makka)",
            "emoji": "🌽",
            "code": "Maize",
            "mandi": "Davanagere (KA) / Gulabbagh (BR) / Chhindwara (MP)",
            "min": "₹2,090",
            "max": "₹2,290",
            "modal": "₹2,160",
            "msp": "₹2,090 / Qtl",
            "trend": "📈 Halki Tezi",
            "trend_type": "up",
            "query_preset": "Makka mandi bhav aur poultry industry demand details."
        },
        {
            "crop": "Cotton (Kapaas)",
            "emoji": "☁️",
            "code": "Cotton",
            "mandi": "Rajkot (GJ) / Bathinda (PB) / Yavatmal (MH)",
            "min": "₹6,850",
            "max": "₹7,600",
            "modal": "₹7,250",
            "msp": "₹7,020 / Qtl",
            "trend": "📈 Strong Demand",
            "trend_type": "up",
            "query_preset": "Cotton selling advice aur market rates guidance."
        },
        {
            "crop": "Gram (Chana)",
            "emoji": "🧆",
            "code": "Gram",
            "mandi": "Latur (MH) / Bikaner (RJ) / Vidisha (MP)",
            "min": "₹5,250",
            "max": "₹5,650",
            "modal": "₹5,480",
            "msp": "₹5,440 / Qtl",
            "trend": "➡️ Samaan Bhav",
            "trend_type": "stable",
            "query_preset": "Chana mandi rates aur pulses market strategy."
        },
        {
            "crop": "Tomato (Tamatar)",
            "emoji": "🍅",
            "code": "Tomato",
            "mandi": "Kolar (KA) / Nashik (MH) / Madanapalle (AP)",
            "min": "₹1,800",
            "max": "₹2,650",
            "modal": "₹2,250",
            "msp": "Market Driven",
            "trend": "📈 Tezi (+₹100)",
            "trend_type": "up",
            "query_preset": "Tamatar ke fresh mandi rates aur direct market selling guidance."
        },
        {
            "crop": "Potato (Aloo)",
            "emoji": "🥔",
            "code": "Potato",
            "mandi": "Agra (UP) / Hooghly (WB) / Jalandhar (PB)",
            "min": "₹1,400",
            "max": "₹1,850",
            "modal": "₹1,650",
            "msp": "Market Driven",
            "trend": "📉 Aavak Zyada (-₹20)",
            "trend_type": "down",
            "query_preset": "Aloo rates kam hain, Cold Storage mein rakhna sahi rahega?"
        },
        {
            "crop": "Onion (Pyaz)",
            "emoji": "🧅",
            "code": "Onion",
            "mandi": "Lasalgaon (MH) / Neemuch (MP) / Mahoba (UP)",
            "min": "₹1,900",
            "max": "₹2,850",
            "modal": "₹2,420",
            "msp": "Market Driven",
            "trend": "➡️ Sthir",
            "trend_type": "stable",
            "query_preset": "Lasalgaon aur major mandis mein Pyaz ke rates batayein."
        },
        {
            "crop": "Sugarcane (Ganna)",
            "emoji": "🎋",
            "code": "Sugarcane",
            "mandi": "Meerut (UP) / Kolhapur (MH) / Yamunanagar (HR)",
            "min": "₹315 (FRP)",
            "max": "₹375 (SAP)",
            "modal": "₹355",
            "msp": "FRP ₹315 / कुंतल",
            "trend": "➡️ Mill Crusher Active",
            "trend_type": "stable",
            "query_preset": "Ganna SAP rates aur sugar mill payment update."
        }
    ]
}

# ---------------------------------------------------------
# Clean Un-Truncated Top Navigation Bar Rendering
# ---------------------------------------------------------
def render_navbar():
    t = LANG_DATA[lang]
    
    col_logo, col_lang = st.columns([3.5, 2.5])
    with col_logo:
        st.markdown(clean_html("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <div style="font-size:2.4rem;">🌾</div>
            <div>
                <div style="font-size:1.5rem; font-weight:900; color:#15803d; line-height:1;">KhetIQ AI</div>
                <div style="font-size:0.8rem; font-weight:600; color:#64748b;">Smart Answers. Better Harvests.</div>
            </div>
        </div>
        """), unsafe_allow_html=True)
    
    with col_lang:
        st.markdown(f"**🌐 {t['select_lang']}**")
        lang_sel = st.radio(
            "Language Selector",
            ["Hindi", "English", "Hinglish"],
            index=["Hindi", "English", "Hinglish"].index(st.session_state["selected_lang"]),
            key="top_lang_radio",
            horizontal=True,
            label_visibility="collapsed"
        )
        if lang_sel != st.session_state["selected_lang"]:
            st.session_state["selected_lang"] = lang_sel
            st.rerun()

# ---------------------------------------------------------
# Hero Banner Card Rendering (Fixed Non-Clickable Image)
# ---------------------------------------------------------
def render_hero_banner():
    t = LANG_DATA[lang]
    
    col_hero_left, col_hero_right = st.columns([7, 5])
    with col_hero_left:
        st.markdown(clean_html(f"""
        <div class="hero-card">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                <span style="background:#16a34a; color:white; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:800;">
                    🌿 KhetIQ AI
                </span>
                <span style="color:#fef08a; font-weight:700; font-size:0.9rem;">Behtar Kheti Behtar Kal</span>
            </div>
            <div class="hero-title">{t['hero_title']}</div>
            <div class="hero-sub">{t['hero_companion']}</div>
            <div class="hero-hindi">✨ {t['hero_sub']}</div>
            <div style="margin-top:14px;">
                <span class="hero-badge-pill">{t['badge1']}</span>
                <span class="hero-badge-pill">{t['badge2']}</span>
                <span class="hero-badge-pill">{t['badge3']}</span>
                <span class="hero-badge-pill">{t['badge4']}</span>
            </div>
        </div>
        """), unsafe_allow_html=True)
        
    with col_hero_right:
        b64_farmer = get_base64_image(os.path.join("assets", "farmer_hero.png"))
        if b64_farmer:
            st.markdown(clean_html(f"""
            <div style="background:#ffffff; border:2px solid #bbf7d0; border-radius:20px; padding:12px; text-align:center; box-shadow:0 4px 14px rgba(0,0,0,0.05);">
                <img src="data:image/png;base64,{b64_farmer}" style="max-height:180px; width:auto; border-radius:14px; object-fit:cover; pointer-events:none; display:inline-block;">
                <div style="margin-top:8px; font-weight:800; color:#15803d; font-size:0.95rem;">
                    "{t['farmer_quote']}"
                </div>
            </div>
            """), unsafe_allow_html=True)
        else:
            st.markdown(clean_html("""
            <div style="background:#dcfce7; border:3px solid #16a34a; border-radius:20px; padding:20px; text-align:center;">
                <div style="font-size:3rem;">👨‍🌾 📱</div>
                <h4 style="color:#15803d; margin:4px 0;">Empowering Indian Farmers</h4>
            </div>
            """), unsafe_allow_html=True)

# ---------------------------------------------------------
# 8 FULLY INTERACTIVE QUICK ACTION ICON CARDS
# ---------------------------------------------------------
def render_quick_actions():
    t = LANG_DATA[lang]
    a_cols = st.columns(8)
    
    actions = [
        ("❓", "Ask AI" if lang != "Hindi" else "सवाल पूछें", "ask"),
        ("📷", "Upload Photo" if lang != "Hindi" else "फ़ोटो लगाएं", "photo"),
        ("🌱", "Crop Guide" if lang != "Hindi" else "फ़सल गाइड", "guide"),
        ("☀️", "Weather" if lang != "Hindi" else "मौसम", "weather"),
        ("🏛️", "Schemes" if lang != "Hindi" else "योजनाएं", "schemes"),
        ("🌾", "Mandi Prices" if lang != "Hindi" else "मंडी भाव", "mandi"),
        ("🕒", "History" if lang != "Hindi" else "इतिहास", "history"),
        ("👨‍🌾", "Find Expert" if lang != "Hindi" else "विशेषज्ञ", "expert")
    ]
    
    for idx, (icon, label_txt, act_id) in enumerate(actions):
        with a_cols[idx]:
            if st.button(f"{icon}\n{label_txt}", key=f"q_action_btn_{act_id}", use_container_width=True):
                if act_id == "ask":
                    st.session_state["active_view"] = "advisor"
                    st.session_state["question_input"] = ""
                    st.toast("🌱 Ready to ask a question! Fill details in Step 3.")
                    st.rerun()
                elif act_id == "photo":
                    st.session_state["active_view"] = "advisor"
                    st.toast("📷 Upload crop photo in Step 3 below!")
                    st.rerun()
                elif act_id == "guide":
                    st.session_state["active_view"] = "advisor"
                    st.session_state["question_input"] = "फ़सल देखभाल, सिंचाई प्रबंधन और उत्तम कृषि तकनीकों की जानकारी दें।" if lang == "Hindi" else "Provide comprehensive crop care, irrigation management and agronomic best practices."
                    st.toast("🌱 Crop care query filled in Step 3!")
                    st.rerun()
                elif act_id == "weather":
                    st.session_state["active_view"] = "advisor"
                    st.session_state["question_input"] = "हाल के मौसम और कोहरे का मेरी फ़सल पर प्रभाव और सुरक्षा के उपाय बताएं।" if lang == "Hindi" else "Explain recent weather, fog and humidity impact on crop health and protection steps."
                    st.toast("☀️ Weather query filled in Step 3!")
                    st.rerun()
                elif act_id == "schemes":
                    st.session_state["active_view"] = "schemes"
                    st.toast("🏛️ Showing all Government Agricultural Schemes!")
                    st.rerun()
                elif act_id == "mandi":
                    st.session_state["active_view"] = "mandi"
                    st.toast("🌾 Showing all Mandi Market Crop Prices!")
                    st.rerun()
                elif act_id == "history":
                    st.session_state["active_view"] = "advisor"
                    st.toast("🕒 Saved consultation history is stored in SQLite database!")
                    st.rerun()
                elif act_id == "expert":
                    st.session_state["active_view"] = "advisor"
                    st.session_state["question_input"] = "कृषि विज्ञान केंद्र (KVK) विशेषज्ञ या किसान कॉल सेंटर 1800-180-1551 से परामर्श का तरीका बताएं।" if lang == "Hindi" else "How to contact local KVK agricultural extension experts or Kisan Call Center 1800-180-1551."
                    st.toast("📞 Kisan Call Center Helpline: 1800-180-1551")
                    st.rerun()

# ---------------------------------------------------------
# View Tab Selector Switcher (Advisor / Schemes / Mandi)
# ---------------------------------------------------------
def render_view_selector():
    v1, v2, v3 = st.columns(3)
    curr_view = st.session_state.get("active_view", "advisor")
    
    lbl_adv = "💬 " + ("Crop Advisory Form" if lang == "English" else ("फ़सल सलाह फॉर्म" if lang == "Hindi" else "Crop Advisory Form"))
    lbl_sch = "🏛️ " + ("Govt Schemes (All 8)" if lang == "English" else ("सरकारी योजनाएं (सभी 8)" if lang == "Hindi" else "Govt Schemes (Sabhi 8)"))
    lbl_man = "🌾 " + ("Mandi Prices (All 10)" if lang == "English" else ("मंडी भाव (सभी 10)" if lang == "Hindi" else "Mandi Prices (Sabhi 10)"))

    with v1:
        is_sel = (curr_view == "advisor")
        btn_badge = " ✅" if is_sel else ""
        if st.button(f"{lbl_adv}{btn_badge}", key="view_tab_advisor", use_container_width=True):
            st.session_state["active_view"] = "advisor"
            st.rerun()
    with v2:
        is_sel = (curr_view == "schemes")
        btn_badge = " ✅" if is_sel else ""
        if st.button(f"{lbl_sch}{btn_badge}", key="view_tab_schemes", use_container_width=True):
            st.session_state["active_view"] = "schemes"
            st.rerun()
    with v3:
        is_sel = (curr_view == "mandi")
        btn_badge = " ✅" if is_sel else ""
        if st.button(f"{lbl_man}{btn_badge}", key="view_tab_mandi", use_container_width=True):
            st.session_state["active_view"] = "mandi"
            st.rerun()

# ---------------------------------------------------------
# Process Flow Indicator Bar
# ---------------------------------------------------------
def render_process_bar():
    t = LANG_DATA[lang]
    st.markdown(clean_html(f"""
    <div class="process-bar-container">
        <div class="process-step-item">
            <div class="process-step-badge">1</div>
            <span>{t['process_1']}</span>
        </div>
        <div style="color:#cbd5e1; font-weight:bold;">➔</div>
        <div class="process-step-item">
            <div class="process-step-badge">2</div>
            <span>{t['process_2']}</span>
        </div>
        <div style="color:#cbd5e1; font-weight:bold;">➔</div>
        <div class="process-step-item">
            <div class="process-step-badge">3</div>
            <span>{t['process_3']}</span>
        </div>
        <div style="color:#cbd5e1; font-weight:bold;">➔</div>
        <div class="process-step-item">
            <div class="process-step-badge" style="background:#2563eb;">4</div>
            <span>{t['process_4']}</span>
        </div>
    </div>
    """), unsafe_allow_html=True)

def render_card(title, icon, content_items, card_type, is_single_text=False):
    box_class = f"box-{card_type}"
    
    if is_single_text:
        body_html = f"<p style='margin:0;'>{content_items}</p>"
    else:
        if isinstance(content_items, list) and len(content_items) > 0:
            lis = "".join([f"<li style='margin-bottom:6px;'>{item}</li>" for item in content_items])
            body_html = f"<ul style='margin:0; padding-left:20px;'>{lis}</ul>"
        else:
            body_html = "<p style='margin:0; opacity:0.8;'>No details provided.</p>"

    st.markdown(clean_html(f"""
    <div class="card-box {box_class}">
        <div class="card-title-text">{icon} {title}</div>
        <div style="margin-top: 8px;">
            {body_html}
        </div>
    </div>
    """), unsafe_allow_html=True)

# ---------------------------------------------------------
# RENDER ALL GOVERNMENT SCHEMES CATALOG VIEW
# ---------------------------------------------------------
def render_schemes_view():
    t = LANG_DATA[lang]
    schemes = GOVT_SCHEMES_DATA.get(lang, GOVT_SCHEMES_DATA["Hindi"])
    
    st.markdown(clean_html(f"""
    <div style="background: linear-gradient(135deg, #064e3b 0%, #047857 100%); border-radius: 20px; padding: 24px 28px; color: white; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(4,120,87,0.25);">
        <h2 style="margin:0; color:#ffffff; font-size:2.2rem; font-weight:900;">🏛️ {t['schemes_page_title']}</h2>
        <p style="margin-top:6px; color:#a7f3d0; font-size:1.1rem; font-weight:600; margin-bottom:0;">{t['schemes_page_sub']}</p>
    </div>
    """), unsafe_allow_html=True)
    
    col_back, col_filter = st.columns([4, 8])
    with col_back:
        if st.button(t["back_to_advisor"], key="btn_back_schemes_top", use_container_width=True):
            st.session_state["active_view"] = "advisor"
            st.rerun()
    
    with col_filter:
        st.info("💡 " + ("Click any scheme's AI button below to ask detailed questions!" if lang != "Hindi" else "किसी भी योजना के बारे में विस्तार से पूछने के लिए नीचे 'AI से पूछें' बटन पर क्लिक करें!"))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render all 8 schemes in structured cards
    for idx, sch in enumerate(schemes):
        elig_items = "".join([f"<li style='margin-bottom:4px;'>{item}</li>" for item in sch['eligibility']])
        doc_items = "".join([f"<li style='margin-bottom:4px;'>{item}</li>" for item in sch['documents']])
        
        card_html = f"""
<div style="background:#ffffff; border:2px solid #a7f3d0; border-radius:18px; padding:20px 24px; margin-bottom:20px; box-shadow:0 4px 16px rgba(0,0,0,0.04);">
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
<h3 style="margin:0; color:#064e3b; font-size:1.4rem; font-weight:900;">
{sch['name']}
</h3>
<span style="background:#ecfdf5; color:#047857; border:1px solid #6ee7b7; padding:4px 14px; border-radius:20px; font-weight:700; font-size:0.88rem;">
🏷️ {sch['category']}
</span>
</div>
<div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:14px; padding:14px 18px; margin-bottom:16px;">
<div style="font-weight:800; color:#166534; font-size:1.05rem; margin-bottom:4px;">
💰 {"मुख्य लाभ (Financial Benefit):" if lang == "Hindi" else "Financial Benefit:"}
</div>
<div style="color:#0f172a; font-weight:600; font-size:1.02rem;">
{sch['benefit']}
</div>
</div>
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:16px; margin-bottom:16px;">
<div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:12px; padding:14px;">
<div style="font-weight:800; color:#0f172a; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
📋 {"पात्रता (Eligibility Criteria):" if lang == "Hindi" else "Eligibility Criteria:"}
</div>
<ul style="margin:0; padding-left:18px; color:#334155; font-size:0.92rem; font-weight:500;">
{elig_items}
</ul>
</div>
<div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:12px; padding:14px;">
<div style="font-weight:800; color:#0f172a; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
📄 {"आवश्यक दस्तावेज (Required Documents):" if lang == "Hindi" else "Required Documents:"}
</div>
<ul style="margin:0; padding-left:18px; color:#334155; font-size:0.92rem; font-weight:500;">
{doc_items}
</ul>
</div>
</div>
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; background:#f1f5f9; padding:10px 16px; border-radius:12px; margin-bottom:12px;">
<div style="font-size:0.9rem; color:#475569; font-weight:600;">
🌐 {"आधिकारिक पोर्टल:" if lang == "Hindi" else "Official Portal:"} <a href="{sch['portal']}" target="_blank" style="color:#0284c7; font-weight:800;">{sch['portal']}</a>
<span style="margin: 0 8px;">|</span>
📞 Helpline: <span style="color:#15803d; font-weight:800;">{sch['helpline']}</span>
</div>
</div>
</div>
"""
        st.markdown(clean_html(card_html), unsafe_allow_html=True)
        
        c_btn, _ = st.columns([7, 5])
        with c_btn:
            if st.button(f"💬 {t['ask_ai_scheme_btn']} ({sch['id'].upper()})", key=f"btn_ask_sch_{idx}", use_container_width=True):
                st.session_state["question_input"] = sch["query_preset"]
                st.session_state["active_view"] = "advisor"
                st.toast(f"🏛️ Selected {sch['name']}! Ready to consult AI.")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t["back_to_advisor"], key="btn_back_schemes_bottom", use_container_width=True):
        st.session_state["active_view"] = "advisor"
        st.rerun()

# ---------------------------------------------------------
# RENDER ALL MANDI PRICES CATALOG VIEW
# ---------------------------------------------------------
def render_mandi_view():
    t = LANG_DATA[lang]
    mandi_items = MANDI_PRICES_DATA.get(lang, MANDI_PRICES_DATA["Hindi"])
    
    st.markdown(clean_html(f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%); border-radius: 20px; padding: 24px 28px; color: white; margin-bottom: 20px; box-shadow: 0 8px 24px rgba(29,78,216,0.25);">
        <h2 style="margin:0; color:#ffffff; font-size:2.2rem; font-weight:900;">🌾 {t['mandi_page_title']}</h2>
        <p style="margin-top:6px; color:#bfdbfe; font-size:1.1rem; font-weight:600; margin-bottom:0;">{t['mandi_page_sub']}</p>
    </div>
    """), unsafe_allow_html=True)
    
    col_back, col_info = st.columns([4, 8])
    with col_back:
        if st.button(t["back_to_advisor"], key="btn_back_mandi_top", use_container_width=True):
            st.session_state["active_view"] = "advisor"
            st.rerun()
    with col_info:
        st.info("💡 " + ("Click any crop button below to get AI selling market advice!" if lang != "Hindi" else "फ़सल बिक्री और मंडी रणनीति के लिए किसी भी फ़सल पर 'AI सलाह लें' क्लिक करें!"))

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary Stat Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="🌾 " + ("Crops Tracked" if lang != "Hindi" else "कुल फ़सलें"),
            value=f"{len(mandi_items)} Crops",
            delta="Agmarknet Mandis"
        )
    with m2:
        st.metric(
            label="🌾 " + ("Wheat Average Rate" if lang != "Hindi" else "गेहूं औसत मंडी भाव"),
            value="₹2,360 / Qtl",
            delta="+₹25 (Upward)"
        )
    with m3:
        st.metric(
            label="🟡 " + ("Mustard Average Rate" if lang != "Hindi" else "सरसों औसत मंडी भाव"),
            value="₹5,680 / Qtl",
            delta="+₹60 (High Demand)"
        )
    with m4:
        st.metric(
            label="🍅 " + ("Tomato Average Rate" if lang != "Hindi" else "टमाटर औसत भाव"),
            value="₹2,250 / Qtl",
            delta="Seasonal Peak"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### 📊 " + ("Daily Mandi Market Price Catalog (Agmarknet Live Standard Rates)" if lang != "Hindi" else "आज के सभी फ़सल मंडी रेट एवं न्यूनतम समर्थन मूल्य (MSP)"))

    # Mandi Items Cards Grid (2-column responsive layout)
    grid_c1, grid_c2 = st.columns(2)
    
    for idx, item in enumerate(mandi_items):
        target_col = grid_c1 if (idx % 2 == 0) else grid_c2
        with target_col:
            badge_bg = "#ecfdf5" if item["trend_type"] == "up" else ("#fef2f2" if item["trend_type"] == "down" else "#f1f5f9")
            badge_color = "#15803d" if item["trend_type"] == "up" else ("#dc2626" if item["trend_type"] == "down" else "#475569")
            
            mandi_card_html = f"""
<div style="background:#ffffff; border:2px solid #bfdbfe; border-radius:18px; padding:18px; margin-bottom:18px; box-shadow:0 4px 14px rgba(0,0,0,0.04);">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
<div style="font-size:1.3rem; font-weight:900; color:#1e3a8a;">
{item['emoji']} {item['crop']}
</div>
<span style="background:{badge_bg}; color:{badge_color}; padding:4px 12px; border-radius:20px; font-weight:800; font-size:0.85rem;">
{item['trend']}
</span>
</div>
<div style="font-size:0.88rem; color:#64748b; font-weight:600; margin-bottom:12px;">
📍 <b>{"प्रमुख मंडी स्थान:" if lang == "Hindi" else "Major Mandi Hubs:"}</b> {item['mandi']}
</div>
<div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:14px; padding:12px; margin-bottom:12px; display:grid; grid-template-columns: 1fr 1fr 1.2fr; gap:8px; text-align:center;">
<div>
<div style="font-size:0.78rem; color:#64748b; font-weight:700;">{"न्यूनतम भाव" if lang == "Hindi" else "Min Rate"}</div>
<div style="font-size:1.05rem; font-weight:800; color:#334155;">{item['min']}</div>
</div>
<div>
<div style="font-size:0.78rem; color:#64748b; font-weight:700;">{"अधिकतम भाव" if lang == "Hindi" else "Max Rate"}</div>
<div style="font-size:1.05rem; font-weight:800; color:#334155;">{item['max']}</div>
</div>
<div style="background:#dcfce7; border-radius:10px; padding:4px;">
<div style="font-size:0.78rem; color:#166534; font-weight:800;">{"औसत (Modal) भाव" if lang == "Hindi" else "Modal Price"}</div>
<div style="font-size:1.2rem; font-weight:900; color:#15803d;">{item['modal']}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; font-size:0.85rem; color:#475569; font-weight:600; margin-bottom:10px;">
<span>🏛️ <b>Govt MSP:</b> <span style="color:#1e40af; font-weight:800;">{item['msp']}</span></span>
<span>📅 <b>Updated:</b> Today</span>
</div>
</div>
"""
            st.markdown(clean_html(mandi_card_html), unsafe_allow_html=True)
            
            if st.button(f"💬 {t['ask_ai_mandi_btn']} ({item['code']})", key=f"btn_mandi_crop_{idx}", use_container_width=True):
                st.session_state["question_input"] = item["query_preset"]
                st.session_state["latest_crop"] = item["code"]
                st.session_state["active_view"] = "advisor"
                st.toast(f"🌾 Selected {item['crop']} Mandi Query! Ready for AI Advice.")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t["back_to_advisor"], key="btn_back_mandi_bottom", use_container_width=True):
        st.session_state["active_view"] = "advisor"
        st.rerun()

# ---------------------------------------------------------
# MAIN APPLICATION WORKFLOW
# ---------------------------------------------------------
def main():
    t = LANG_DATA[lang]
    
    # 1. Render Top Navbar with clean Language selector
    render_navbar()

    # 2. Render Hero Banner
    render_hero_banner()

    # 3. Render Interactive Quick Actions
    render_quick_actions()
    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Render View Selector Tabs
    render_view_selector()
    st.markdown("<br>", unsafe_allow_html=True)

    # Determine Active View Mode
    curr_view = st.session_state.get("active_view", "advisor")

    if curr_view == "schemes":
        render_schemes_view()
    elif curr_view == "mandi":
        render_mandi_view()
    else:
        # Sidebar Control Status & Demo Toggle
        api_key = get_api_key()
        if api_key:
            demo_mode = st.sidebar.checkbox("Safe Demo Mode", value=False)
        else:
            demo_mode = True

        # ---------------------------------------------------------
        # MAIN 2-COLUMN LAYOUT: SIDEBAR HELP (LEFT) & FORM (RIGHT)
        # ---------------------------------------------------------
        col_left_help, col_right_form = st.columns([3.2, 8.8])

        # LEFT SIDEBAR CARDS
        with col_left_help:
            st.markdown(clean_html(f"""
            <div class="sidebar-info-card">
                <div class="sidebar-card-title">{t['why_title']}</div>
                <div class="sidebar-list-item">
                    <div>👥</div>
                    <div><b>{t['why_1_title']}</b><br><span style="font-size:0.82rem; color:#64748b;">{t['why_1_sub']}</span></div>
                </div>
                <div class="sidebar-list-item">
                    <div>💬</div>
                    <div><b>{t['why_2_title']}</b><br><span style="font-size:0.82rem; color:#64748b;">{t['why_2_sub']}</span></div>
                </div>
                <div class="sidebar-list-item">
                    <div>🎙️</div>
                    <div><b>{t['why_3_title']}</b><br><span style="font-size:0.82rem; color:#64748b;">{t['why_3_sub']}</span></div>
                </div>
                <div class="sidebar-list-item">
                    <div>❤️</div>
                    <div><b>{t['why_4_title']}</b><br><span style="font-size:0.82rem; color:#64748b;">{t['why_4_sub']}</span></div>
                </div>
            </div>
            """), unsafe_allow_html=True)

            st.markdown(clean_html(f"""
            <div style="background:linear-gradient(135deg, #16a34a 0%, #15803d 100%); border-radius:16px; padding:18px; color:white; text-align:center; margin-bottom:18px; box-shadow:0 4px 14px rgba(22,163,74,0.3);">
                <div style="font-size:2.5rem;">👨‍🌾</div>
                <h4 style="margin:6px 0; color:#fef08a;">"{t['farmer_quote']}"</h4>
                <p style="font-size:0.85rem; color:#dcfce7;">{t['farmer_sub']}</p>
            </div>
            """), unsafe_allow_html=True)

            st.markdown(clean_html(f"""
            <div class="sidebar-info-card">
                <div class="sidebar-card-title">{t['learn_title']}</div>
                <div class="sidebar-list-item">📷 Photo Tips</div>
                <div class="sidebar-list-item">🍂 Yellow Leaves</div>
                <div class="sidebar-list-item">💧 Soil Moisture</div>
                <div class="sidebar-list-item">🐛 Pest Inspection</div>
                <div class="sidebar-list-item">🛡️ Spray Rules</div>
            </div>
            """), unsafe_allow_html=True)

        # RIGHT MAIN FORM AREA
        with col_right_form:
            # Process Bar Indicator
            render_process_bar()

            # 3-Column Guided Advisory Form
            fc1, fc2, fc3 = st.columns(3)

            # FORM COLUMN 1: CROP SELECTION
            with fc1:
                st.markdown(f'<div class="form-column-box">', unsafe_allow_html=True)
                st.markdown(f'<div class="form-column-header">{t["sec1_header"]}</div>', unsafe_allow_html=True)
                
                st.markdown(f"**{t['select_crop']}**")
                
                crop_items = CROPS_GRID_DATA[lang]
                cg1, cg2 = st.columns(2)
                for idx, (emoji, c_lbl, c_code) in enumerate(crop_items):
                    target_col = cg1 if (idx % 2 == 0) else cg2
                    with target_col:
                        is_sel = (st.session_state["latest_crop"] == c_code)
                        sel_badge = " ✅" if is_sel else ""
                        if st.button(f"{emoji} {c_lbl}{sel_badge}", key=f"form_crop_{idx}", use_container_width=True):
                            st.session_state["latest_crop"] = c_code

                selected_crop_code = st.session_state["latest_crop"]
                
                custom_crop_name = ""
                if selected_crop_code == "Other":
                    custom_crop_name = st.text_input(
                        f"✍️ {t['custom_crop']}",
                        placeholder=t["custom_crop_ph"]
                    )

                crop_age_val = st.text_input(
                    f"📅 {t['crop_age']}",
                    placeholder=t["crop_age_ph"]
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # FORM COLUMN 2: FARM DETAILS & LOCATION
            with fc2:
                st.markdown(f'<div class="form-column-box">', unsafe_allow_html=True)
                st.markdown(f'<div class="form-column-header">{t["sec2_header"]}</div>', unsafe_allow_html=True)
                
                village_val = st.text_input(f"🏠 {t['village']}", placeholder="e.g. Rampur")
                district_val = st.text_input(f"📍 {t['district']}", placeholder="e.g. Karnal")
                state_val = st.text_input(f"🗺️ {t['state']}", placeholder="e.g. Haryana")
                
                weather_val = st.text_input(
                    f"☀️ {t['weather']}",
                    placeholder=t["weather_ph"]
                )
                spray_val = st.text_input(
                    f"🧪 {t['spray']}",
                    placeholder=t["spray_ph"]
                )
                
                st.markdown(clean_html("""
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px; padding:10px; text-align:center; margin-top:12px;">
                    <div style="font-size:1.8rem;">🏞️ 🚜</div>
                </div>
                """), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # FORM COLUMN 3: PROBLEM DESCRIPTION, VOICE & PHOTO
            with fc3:
                st.markdown(f'<div class="form-column-box">', unsafe_allow_html=True)
                st.markdown(f'<div class="form-column-header">{t["sec3_header"]}</div>', unsafe_allow_html=True)
                
                st.markdown(f"**{t['quick_presets']}**")
                presets = SYMPTOM_PRESETS[lang]
                ps1, ps2 = st.columns(2)
                for idx, (p_emoji, p_lbl, p_desc) in enumerate(presets):
                    target_col = ps1 if (idx % 2 == 0) else ps2
                    with target_col:
                        if st.button(f"{p_emoji} {p_lbl}", key=f"f_preset_{idx}", use_container_width=True):
                            st.session_state["question_input"] = p_desc
                            st.rerun()

                question_text = st.text_area(
                    f"✍️ {t['question_label']}",
                    value=st.session_state["question_input"],
                    placeholder=t["question_ph"],
                    height=110
                )

                # Web Speech API Micro Component (Optimized for Hinglish/Hindi Speech Codes: hi-IN / en-IN)
                speech_lang_code = "hi-IN" if lang in ["Hindi", "Hinglish"] else "en-US"
                speech_html = f"""
                <div style="background:#f0fdf4; border:2px solid #16a34a; border-radius:14px; padding:12px; text-align:center; font-family:sans-serif; margin-top:8px;">
                    <button id="micBtn" style="background:#15803d; color:white; border:none; padding:10px 20px; border-radius:22px; font-weight:bold; font-size:0.92rem; cursor:pointer; width:100%; box-shadow:0 3px 8px rgba(0,0,0,0.15);">
                        {t['voice_btn']}
                    </button>
                    <div style="margin-top:6px; font-size:0.8rem; color:#15803d; font-weight:bold;">
                        Mic Language: <span id="langDisplay">{speech_lang_code}</span> 
                        <button id="toggleLangBtn" style="background:#dcfce7; border:1px solid #16a34a; color:#14532d; padding:2px 8px; border-radius:10px; cursor:pointer; font-size:0.75rem; margin-left:6px;">
                            Switch to en-IN (Indian English)
                        </button>
                    </div>
                    <p id="micStatus" style="margin:6px 0 0 0; font-size:0.82rem; color:#14532d; font-weight:600;">
                        Click button and speak clearly into your mic.
                    </p>
                    <div id="micResult" contenteditable="true" style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:8px; margin-top:6px; font-size:0.88rem; color:#0f172a; min-height:40px; text-align:left; font-weight:500;">
                        (Spoken words will appear here...)
                    </div>
                </div>

                <script>
                const micBtn = document.getElementById('micBtn');
                const micStatus = document.getElementById('micStatus');
                const micResult = document.getElementById('micResult');
                const toggleLangBtn = document.getElementById('toggleLangBtn');
                const langDisplay = document.getElementById('langDisplay');

                let currentSpeechLang = '{speech_lang_code}';

                toggleLangBtn.onclick = () => {{
                    if (currentSpeechLang === 'hi-IN') {{
                        currentSpeechLang = 'en-IN';
                        toggleLangBtn.innerText = "Switch to hi-IN (Hindi)";
                    }} else {{
                        currentSpeechLang = 'hi-IN';
                        toggleLangBtn.innerText = "Switch to en-IN (Indian English)";
                    }}
                    langDisplay.innerText = currentSpeechLang;
                }};

                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

                if (!SpeechRecognition) {{
                    micStatus.innerHTML = "⚠️ Browser voice recognition not supported. You can type in the text box.";
                    micBtn.disabled = true;
                    micBtn.style.opacity = 0.5;
                }} else {{
                    const recognition = new SpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = true;

                    let active = false;

                    micBtn.onclick = () => {{
                        if (!active) {{
                            try {{
                                recognition.lang = currentSpeechLang;
                                recognition.start();
                                active = true;
                                micBtn.style.background = "#dc2626";
                                micBtn.innerHTML = "🔴 Listening... Speak Now";
                                micStatus.innerHTML = "🎙️ Mic active (" + currentSpeechLang + ")! Speak clearly.";
                            }} catch(e) {{
                                micStatus.innerHTML = "⚠️ Mic error: " + e.message;
                            }}
                        }} else {{
                            recognition.stop();
                            active = false;
                            micBtn.style.background = "#15803d";
                            micBtn.innerHTML = "{t['voice_btn']}";
                            micStatus.innerHTML = "Stopped.";
                        }}
                    }};

                    recognition.onresult = (event) => {{
                        let output = '';
                        for (let i = event.resultIndex; i < event.results.length; i++) {{
                            output += event.results[i][0].transcript;
                        }}
                        micResult.innerText = output;
                    }};

                    recognition.onerror = (event) => {{
                        micStatus.innerHTML = "⚠️ Mic status: " + event.error + ". Allow microphone permission in browser.";
                        micBtn.style.background = "#15803d";
                        micBtn.innerHTML = "{t['voice_btn']}";
                        active = false;
                    }};

                    recognition.onend = () => {{
                        micBtn.style.background = "#15803d";
                        micBtn.innerHTML = "{t['voice_btn']}";
                        active = false;
                        micStatus.innerHTML = "✅ Voice recorded successfully!";
                    }};
                }}
                </script>
                """
                components.html(speech_html, height=180)

                uploaded_image_file = st.file_uploader(
                    f"{t['photo_label']}",
                    type=["jpg", "jpeg", "png"],
                    label_visibility="collapsed"
                )
                
                uploaded_image = None
                if uploaded_image_file:
                    try:
                        uploaded_image = Image.open(uploaded_image_file)
                        st.image(uploaded_image, width=140, caption="Uploaded Photo")
                    except Exception:
                        pass

                st.markdown('</div>', unsafe_allow_html=True)

            # BIG GREEN SUBMIT BUTTON ACROSS FORM
            st.markdown("<br>", unsafe_allow_html=True)
            effective_crop = selected_crop_code
            if selected_crop_code == "Other" and custom_crop_name.strip():
                effective_crop = custom_crop_name.strip()

            submit_btn = st.button(t["submit_btn"], use_container_width=True)

            if submit_btn:
                if not question_text or question_text.strip() == "":
                    st.error("⚠️ Please enter a question or click a symptom button before requesting advice.")
                else:
                    is_safe, safety_err = check_query_safety(question_text, lang)
                    if not is_safe:
                        st.error(safety_err)
                    else:
                        full_question = question_text
                        if weather_val.strip():
                            full_question += f"\n- Weather: {weather_val.strip()}"
                        if spray_val.strip():
                            full_question += f"\n- Sprays/Fertilizers: {spray_val.strip()}"

                        with st.spinner(f"🌱 Preparing AI advisory for {effective_crop}..."):
                            advice_result = get_ai_agricultural_advice(
                                crop=effective_crop,
                                question=full_question,
                                language=lang,
                                village=village_val,
                                district=district_val,
                                state=state_val,
                                crop_age=crop_age_val,
                                image=uploaded_image,
                                force_demo=demo_mode
                            )

                            st.session_state["latest_advice"] = advice_result
                            st.session_state["latest_crop"] = effective_crop

                            try:
                                save_consultation(
                                    language=lang,
                                    crop=effective_crop,
                                    village=village_val,
                                    district=district_val,
                                    state=state_val,
                                    crop_age=crop_age_val,
                                    question=full_question,
                                    has_image=(uploaded_image is not None),
                                    response_data=advice_result
                                )
                            except Exception:
                                pass

        # ---------------------------------------------------------
        # DISPLAY ADVISORY RESULTS CARDS
        # ---------------------------------------------------------
        if st.session_state["latest_advice"] is not None:
            adv = st.session_state["latest_advice"]
            sec = t["sections"]

            st.markdown("---")
            st.markdown(f"## {t['advice_results_title']}")

            if "api_error" in adv:
                st.info(f"ℹ️ System Notice: AI API unavailable ({adv['api_error']}). Displaying Safe Demo Mode advisory.")

            st.success(f"✅ Advisory generated for **{st.session_state['latest_crop']}** in **{lang}**")

            # Generate Complete Advisory Solution Report Text (Problem + Full Solutions + Causes + Prevention + Helpline)
            v_val = village_val if 'village_val' in locals() else ""
            d_val = district_val if 'district_val' in locals() else ""
            s_val = state_val if 'state_val' in locals() else ""
            
            full_report_text = generate_full_advisory_report(
                crop=st.session_state['latest_crop'],
                lang=lang,
                village=v_val,
                district=d_val,
                state=s_val,
                adv=adv
            )

            col_left_cards, col_right_cards = st.columns(2)

            with col_left_cards:
                render_card(
                    sec["problem"], "💡", adv.get("problem_understanding", ""), "problem", is_single_text=True
                )
                render_card(
                    sec["actions"], "✅", adv.get("recommended_actions", []), "actions"
                )
                supp_missing = format_missing_info_check(
                    st.session_state['latest_crop'], "", "", "", "", lang
                )
                combined_missing = list(set(adv.get("missing_information", []) + supp_missing))
                render_card(
                    sec["missing"], "❓", combined_missing, "missing"
                )

            with col_right_cards:
                render_card(
                    sec["causes"], "🔍", adv.get("possible_causes", []), "causes"
                )
                render_card(
                    sec["prevention"], "🛡️", adv.get("prevention_tips", []), "prevention"
                )
                render_card(
                    sec["expert"], "👨‍🌾", adv.get("when_to_contact_expert", []), "expert"
                )

            # POST-ADVICE QUICK ACTION TOOLS BAR
            st.markdown(clean_html(f"""
            <div class="tools-bar-card">
                <h4 style="margin-top:0; color:#14532d;">{t['quick_tools_title']}</h4>
            </div>
            """), unsafe_allow_html=True)
            
            tb1, tb2, tb3, tb4, tb5 = st.columns(5)
            
            # 1. Native HTML5 Web Speech Synthesis Player (Sanitized Errorless Audio Playback)
            raw_problem_txt = sanitize_text_for_speech(adv.get('problem_understanding', ''), lang)
            raw_actions_list = [sanitize_text_for_speech(a, lang) for a in adv.get('recommended_actions', [])]
            raw_actions_txt = ". ".join([a for a in raw_actions_list if a])
            
            speech_raw_text = f"Crop {st.session_state['latest_crop']}. Problem: {raw_problem_txt}. Solution Steps: {raw_actions_txt}"
            speech_lang = "hi-IN" if lang in ["Hindi", "Hinglish"] else "en-IN"

            tts_html = f"""
            <div style="background:#f0fdf4; border:2px solid #16a34a; border-radius:14px; padding:10px; text-align:center; font-family:sans-serif;">
                <button id="ttsPlayBtn" style="background:#15803d; color:white; border:none; padding:10px 14px; border-radius:18px; font-weight:800; font-size:0.9rem; cursor:pointer; width:100%; box-shadow:0 3px 8px rgba(0,0,0,0.15);">
                    🔊 {t['listen']}
                </button>
                <div id="ttsStatus" style="font-size:0.75rem; color:#14532d; margin-top:4px; font-weight:bold;">
                    Click to listen to full advice
                </div>
            </div>

            <script>
            const ttsBtn = document.getElementById('ttsPlayBtn');
            const ttsStatus = document.getElementById('ttsStatus');
            const rawSummary = {json.dumps(speech_raw_text)};
            
            const containsDevanagari = /[\u0900-\u097F]/.test(rawSummary);
            const targetLang = containsDevanagari ? 'hi-IN' : 'en-IN';

            let synth = window.speechSynthesis;
            let isSpeaking = false;
            let selectedVoice = null;

            function loadVoice() {{
                if (!synth) return;
                const voices = synth.getVoices();
                if (voices.length > 0) {{
                    if (containsDevanagari) {{
                        selectedVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('HI') || v.name.toLowerCase().includes('hindi')) ||
                                        voices.find(v => v.lang.includes('IN') || v.lang.includes('in')) ||
                                        null;
                    }} else {{
                        selectedVoice = voices.find(v => v.lang.includes('en-IN') || v.lang.includes('en_IN') || (v.lang.includes('IN') && v.lang.includes('en'))) ||
                                        voices.find(v => v.lang.startsWith('en')) ||
                                        null;
                    }}
                }}
            }}

            if (synth) {{
                loadVoice();
                if (synth.onvoiceschanged !== undefined) {{
                    synth.onvoiceschanged = loadVoice;
                }}
            }}

            ttsBtn.onclick = () => {{
                if (!synth) {{
                    ttsStatus.innerHTML = "⚠️ Speech synthesis unavailable.";
                    return;
                }}
                if (isSpeaking) {{
                    synth.cancel();
                    isSpeaking = false;
                    ttsBtn.style.background = "#15803d";
                    ttsBtn.innerHTML = "🔊 {t['listen']}";
                    ttsStatus.innerHTML = "Audio stopped.";
                }} else {{
                    loadVoice();
                    const sentences = rawSummary.split(/(?<=[.!?])\\s+/).filter(s => s.trim().length > 0);
                    if (sentences.length === 0) return;

                    isSpeaking = true;
                    ttsBtn.style.background = "#dc2626";
                    ttsBtn.innerHTML = "⏹️ Stop Audio";
                    ttsStatus.innerHTML = "🔊 Reading advice aloud...";

                    let curIdx = 0;
                    function playNext() {{
                        if (curIdx >= sentences.length || !isSpeaking) {{
                            isSpeaking = false;
                            ttsBtn.style.background = "#15803d";
                            ttsBtn.innerHTML = "🔊 {t['listen']}";
                            ttsStatus.innerHTML = "✅ Audio completed!";
                            return;
                        }}

                        const utter = new SpeechSynthesisUtterance(sentences[curIdx].trim());
                        utter.lang = targetLang;
                        utter.rate = 0.92;
                        utter.pitch = 1.0;
                        if (selectedVoice) {{
                            utter.voice = selectedVoice;
                        }}

                        utter.onend = () => {{
                            curIdx++;
                            playNext();
                        }};

                        utter.onerror = () => {{
                            curIdx++;
                            playNext();
                        }};

                        synth.speak(utter);
                    }}

                    playNext();
                }}
            }};
            </script>
            """

            with tb1:
                components.html(clean_html(tts_html), height=105)

            # 2. Download Full Solution Report
            with tb2:
                st.download_button(
                    label=t["save_report"],
                    data=full_report_text,
                    file_name=f"KhetIQ_Solution_Report_{st.session_state['latest_crop']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            # 3. Interactive Text Area for Copying Full Report
            with tb3:
                if st.button(t["copy_text"], key="btn_copy_tool", use_container_width=True):
                    st.session_state["show_copy_box"] = not st.session_state.get("show_copy_box", False)
                    st.rerun()

            # 4. Ask Followup Question
            with tb4:
                if st.button(t["ask_followup"], key="btn_followup_tool", use_container_width=True):
                    st.session_state["question_input"] = f"Regarding {st.session_state['latest_crop']}: "
                    st.rerun()

            # 5. New Consultation Reset
            with tb5:
                if st.button(t["new_consult"], key="btn_new_tool", use_container_width=True):
                    st.session_state["latest_advice"] = None
                    st.session_state["question_input"] = ""
                    st.rerun()

            if st.session_state.get("show_copy_box", False):
                st.text_area(
                    "📋 " + ("Copy Complete Solution Report Text:" if lang != "Hindi" else "संपूर्ण समाधान रिपोर्ट पाठ कॉपी करें:"),
                    value=full_report_text,
                    height=240
                )

        # ---------------------------------------------------------
        # VISUAL "TRY THESE EXAMPLES" CARDS ROW (Fully Multilingual & Interactive)
        # ---------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"## {t['try_examples_title']}")

        ex_col1, ex_col2, ex_col3 = st.columns(3)

        b64_yellow = get_base64_image(os.path.join("assets", "yellow_leaves.png"))
        b64_pest = get_base64_image(os.path.join("assets", "pest_insect.png"))
        b64_black = get_base64_image(os.path.join("assets", "black_spots.png"))

        ex1_text = t["ex1_title"]
        ex2_text = t["ex2_title"]
        ex3_text = t["ex3_title"]

        with ex_col1:
            if st.button(f"🍂 {ex1_text}", key="ex_card_title_btn_1", use_container_width=True):
                st.session_state["question_input"] = ex1_text
                st.session_state["latest_crop"] = "Wheat"
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

            img_html1 = f'<img src="data:image/png;base64,{b64_yellow}" style="max-height:140px; width:100%; border-radius:12px; object-fit:cover; pointer-events:none;">' if b64_yellow else '<div style="font-size:3rem;">🍂 🟡</div>'
            st.markdown(clean_html(f"""
            <a href="?example_q=1" target="_self" class="example-card-link">
                <div class="example-card-inner" style="background:#ffffff; border-radius:14px; padding:14px; border:2px solid #cbd5e1; text-align:center; margin-top:4px; margin-bottom:8px;">
                    {img_html1}
                    <div style="margin-top:6px;"><span style="background:#fef9c3; border:1px solid #fde047; color:#854d0e; padding:2px 10px; border-radius:12px; font-weight:800; font-size:0.85rem;">🍂 🟡 {t['try_this_btn']}</span></div>
                    <h4 style="margin-top:8px; color:#14532d; font-size:0.95rem;">{ex1_text}</h4>
                </div>
            </a>
            """), unsafe_allow_html=True)

            if st.button(f"👉 {t['try_this_btn']}", key="ex_btn_1", use_container_width=True):
                st.session_state["question_input"] = ex1_text
                st.session_state["latest_crop"] = "Wheat"
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

        with ex_col2:
            if st.button(f"🐛 {ex2_text}", key="ex_card_title_btn_2", use_container_width=True):
                st.session_state["question_input"] = ex2_text
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

            img_html2 = f'<img src="data:image/png;base64,{b64_pest}" style="max-height:140px; width:100%; border-radius:12px; object-fit:cover; pointer-events:none;">' if b64_pest else '<div style="font-size:3rem;">🐛 🌿</div>'
            st.markdown(clean_html(f"""
            <a href="?example_q=2" target="_self" class="example-card-link">
                <div class="example-card-inner" style="background:#ffffff; border-radius:14px; padding:14px; border:2px solid #cbd5e1; text-align:center; margin-top:4px; margin-bottom:8px;">
                    {img_html2}
                    <div style="margin-top:6px;"><span style="background:#dcfce7; border:1px solid #86efac; color:#166534; padding:2px 10px; border-radius:12px; font-weight:800; font-size:0.85rem;">🐛 🌿 {t['try_this_btn']}</span></div>
                    <h4 style="margin-top:8px; color:#14532d; font-size:0.95rem;">{ex2_text}</h4>
                </div>
            </a>
            """), unsafe_allow_html=True)

            if st.button(f"👉 {t['try_this_btn']}", key="ex_btn_2", use_container_width=True):
                st.session_state["question_input"] = ex2_text
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

        with ex_col3:
            if st.button(f"🍄 {ex3_text}", key="ex_card_title_btn_3", use_container_width=True):
                st.session_state["question_input"] = ex3_text
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

            img_html3 = f'<img src="data:image/png;base64,{b64_black}" style="max-height:140px; width:100%; border-radius:12px; object-fit:cover; pointer-events:none;">' if b64_black else '<div style="font-size:3rem;">🍄 ⚫</div>'
            st.markdown(clean_html(f"""
            <a href="?example_q=3" target="_self" class="example-card-link">
                <div class="example-card-inner" style="background:#fefce8; border-radius:14px; padding:14px; border:2px solid #eab308; text-align:center; margin-top:4px; margin-bottom:8px;">
                    {img_html3}
                    <div style="margin-top:6px;"><span style="background:#fef08a; border:1px solid #ca8a04; color:#854d0e; padding:2px 10px; border-radius:12px; font-weight:800; font-size:0.85rem;">🍄 ⚫ {t['try_this_btn']}</span></div>
                    <h4 style="margin-top:8px; color:#a16207; font-size:0.95rem;">{ex3_text}</h4>
                </div>
            </a>
            """), unsafe_allow_html=True)

            if st.button(f"👉 {t['try_this_btn']}", key="ex_btn_3", use_container_width=True):
                st.session_state["question_input"] = ex3_text
                st.session_state["active_view"] = "advisor"
                st.toast("💡 Question filled in Step 3! Click Get AI Advice.")
                st.rerun()

        # ---------------------------------------------------------
        # SAVED CONSULTATION HISTORY SECTION
        # ---------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"## {t['history_title']}")
        st.caption("Click any past consultation record below to view details or previous AI advice:")

        hist_h1, hist_h2 = st.columns([3, 1])
        with hist_h2:
            if st.button(t["clear_history_btn"], key="btn_clear_hist_main"):
                clear_history()
                st.toast("History database cleared.")
                st.rerun()

        history_records = get_recent_consultations(limit=30)
        if not history_records:
            st.info("No past consultation history recorded yet. Submit your first crop query above!")
        else:
            for rec in history_records:
                loc_str = ", ".join([x for x in [rec.get("village"), rec.get("district"), rec.get("state")] if x])
                loc_display = f"📍 {loc_str}" if loc_str else "📍 Location Not Specified"
                expander_title = f"🌾 {rec.get('crop')} | {rec.get('timestamp')} | {rec.get('language')} | {loc_display}"
                
                with st.expander(expander_title):
                    st.markdown(f"**Question / Symptoms:** {rec.get('question')}")
                    if rec.get('crop_age'):
                        st.markdown(f"**Crop Age:** {rec.get('crop_age')}")
                    
                    resp = rec.get("response_data", {})
                    if resp:
                        st.markdown("---")
                        st.markdown(f"**💡 Problem:** {resp.get('problem_understanding', '')}")
                        if resp.get('recommended_actions'):
                            st.markdown("**✅ Actions:**")
                            for act in resp.get('recommended_actions'):
                                st.markdown(f"- {act}")

    # ---------------------------------------------------------
    # LEGAL WARNING BANNER
    # ---------------------------------------------------------
    st.markdown(clean_html(f"""
    <div class="warning-banner">
        <div style="font-size:1.8rem;">⚠️</div>
        <div>
            <b>{t['warning_title']}</b> {t['warning_text']}
        </div>
    </div>
    """), unsafe_allow_html=True)

    # ---------------------------------------------------------
    # RICH DARK GREEN FOOTER
    # ---------------------------------------------------------
    st.markdown(clean_html("""
    <div style="background:#052e16; border-radius:20px; padding:24px 32px; color:white; text-align:center; margin-top:20px;">
        <div style="font-size:1.8rem; font-weight:900; color:#4ade80;">🌿 KhetIQ AI</div>
        <p style="color:#dcfce7; font-weight:600; margin-top:4px;">Empowering Farmers. Enriching Fields. 🌾</p>
        <div style="margin-top:10px; font-size:0.8rem; color:#64748b;">
            एक बेहतर कल के लिए / For a Greener Tomorrow &copy; 2026 KhetIQ AI
        </div>
    </div>
    """), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
