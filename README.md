# 🌾 KhetIQ AI: Multilingual AI-Powered Agricultural Expert Advisor

**Smart Answers. Better Harvests.**

KhetIQ AI is an interactive, multilingual AI-powered web application built for smallholder farmers, agricultural extension workers, and agronomists. It provides practical, safety-checked, and structured agricultural advice in **Hindi**, **English**, and **Hinglish**.

---

## 🌟 Key Features

1. **🌾 Crop-Specific Diagnostics**: Tailored advice for Wheat, Rice, Maize, Tomato, Potato, Sugarcane, and other crops.
2. **🌐 Multilingual Support**:
   - **Hindi (हिंदी)**: Devanagari script for local farmers.
   - **English**: Standard agricultural terms.
   - **Hinglish**: Conversational Roman Hindi.
3. **📷 Multimodal Image Upload**: Optional photo upload of diseased leaves/crops analyzed via Google Gemini 2.5 Flash Vision.
4. **📊 Structured 6-Section Advisory Dashboard**:
   - 💡 **Problem Understanding**
   - 🔍 **Possible Causes**
   - ✅ **Recommended Actions**
   - 🛡️ **Prevention Tips**
   - ❓ **Missing Information**
   - 👨‍🌾 **When to Contact an Agricultural Expert**
5. **📜 Consultation History (SQLite)**: Saves all past queries and advice locally for offline review.
6. **🛡️ Agricultural Safety System**:
   - Prevents unsafe high-risk chemical dosage recommendations.
   - Enforces KVK (Krishi Vigyan Kendra) and Extension Officer verification disclaimers.
   - Identifies missing diagnostic parameters (e.g., crop age, weather, exact location).
7. **⚡ Safe Demo Mode**: Works out of the box even without an active API key using rich pre-configured agronomic responses.

---

## 🏗️ Project Directory Structure

```text
KhetIQ-AI/
├── app.py                      # Main Streamlit web application & UI
├── requirements.txt            # Python dependencies (Streamlit, Gemini API, Pillow, dotenv)
├── .env.example                # Environment variable configuration template
├── .gitignore                  # Git ignore definitions
├── README.md                   # Complete documentation & setup instructions
├── data/
│   └── knowledge_base.txt      # Agricultural knowledge base context
├── services/
│   ├── __init__.py
│   ├── ai_service.py           # Gemini API integration, multimodal prompts, and demo fallback
│   └── safety_service.py       # Agricultural safety verifier & disclaimer generator
└── database/
    ├── __init__.py
    └── database.py             # SQLite helper functions for advisory history
```

---

## ⚙️ Installation & Setup Guide

### 1. Prerequisites
- **Python 3.9+** installed on your system.

### 2. Clone / Setup Project
Navigate to the project folder:
```bash
cd c:\Users\adarshsenyadav\Desktop\KhetIQ-AI
```

### 3. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Open `.env` and add your **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/)):
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```
*(Note: If no key is set, KhetIQ AI automatically activates **Safe Demo Mode**).*

---

## 🚀 Running the Application

Launch the Streamlit web application with the following command:

```bash
streamlit run app.py
```

The web app will automatically open in your default browser at:
`http://localhost:8501`

---

## 🛡️ AI Safety Rules & Disclaimers

- **Informational Advice**: KhetIQ AI provides guidance based on standard agronomic practice and AI analysis. It is **not** a replacement for physical field inspection by certified Agricultural Officers.
- **Pesticide Safety**: The application prioritizes organic control (e.g., Neem oil, yellow sticky traps, field sanitation). Farmers are instructed never to apply unverified synthetic chemical sprays without consulting their local **Krishi Vigyan Kendra (KVK)** or **Block Agriculture Officer (BAO)**.

---

## 📜 License & Acknowledgments

Built for the Indian agricultural community. Designed for extension workers, Krishi Vigyan Kendras, and progressive farmers.
