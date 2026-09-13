from typing import Dict, Any, Tuple, Optional

DISCLAIMERS = {
    "English": (
        "⚠️ **Safety & Legal Disclaimer**: KhetIQ AI provides informational agricultural advice based on AI models "
        "and standard agronomic knowledge. It is NOT a replacement for on-field diagnosis by a certified Agricultural Extension Officer "
        "or Krishi Vigyan Kendra (KVK) scientist. Always consult local agricultural authorities before applying chemical treatments."
    ),
    "Hindi": (
        "⚠️ **सुरक्षा और कानूनी अस्वीकरण**: KhetIQ AI केवल कृत्रिम बुद्धिमत्ता और मानक कृषि ज्ञान पर आधारित सलाह प्रदान करता है। "
        "यह कृषि विज्ञान केंद्र (KVK) के वैज्ञानिकों या स्थानीय कृषि अधिकारी की प्रत्यक्ष जांच का विकल्प नहीं है। "
        "कीटनाशकों या रसायनों का उपयोग करने से पहले हमेशा स्थानीय कृषि विशेषज्ञों से पुष्टि करें।"
    ),
    "Hinglish": (
        "⚠️ **Safety aur Legal Disclaimer**: KhetIQ AI AI models aur standard agricultural knowledge ke basis par jaankari deta hai. "
        "Yeh Krishi Vigyan Kendra (KVK) scientists ya local Agri Officer ki physical field check ka replacement nahi hai. "
        "Chemical pesticide use karne se pehle local agricultural expert se zaroor consult karein."
    )
}

HIGH_RISK_KEYWORDS = [
    "poison", "suicide", "toxic dose", "lethal dose", "zahar", "zeher", "aatmahatya",
    "drink pesticide", "chemical burn", "concentrated acid", "banned chemical"
]

def check_query_safety(query: str, language: str = "English") -> Tuple[bool, Optional[str]]:
    """
    Checks if the user query contains dangerous, high-risk, or non-agricultural safety hazards.
    Returns (is_safe, safety_message).
    """
    query_lower = query.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in query_lower:
            if language == "Hindi":
                msg = "⚠️ आपकी टिप्पणी में संवेदनशील या असुरक्षित शब्द पाए गए हैं। KhetIQ AI केवल सुरक्षित कृषि सलाह प्रदान करता है। आपातकालीन सहायता के लिए कृपया स्थानीय हेल्पलाइन या निकटतम अस्पताल से संपर्क करें।"
            elif language == "Hinglish":
                msg = "⚠️ Aapki query mein sensitive ya unsafe terms paye gaye hain. KhetIQ AI sirf safe farming advice deta hai. Emergency help ke liye local helpline se contact karein."
            else:
                msg = "⚠️ Unsafe or hazardous request detected. KhetIQ AI strictly provides safe agricultural guidance. For emergency support, please contact local authorities immediately."
            return False, msg
    return True, None

def format_missing_info_check(
    crop: str,
    crop_age: str,
    village: str,
    district: str,
    state: str,
    language: str
) -> list:
    """Identifies missing key contextual parameters and builds safety questions."""
    missing = []
    
    if not crop_age or crop_age.strip() == "":
        if language == "Hindi":
            missing.append("फ़सल की सटीक उम्र या अवस्था (उदा. बुआई के 30 दिन बाद, फूल आने की अवस्था)।")
        elif language == "Hinglish":
            missing.append("Crop ki exact age ya stage (e.g. 25-30 days post sowing, flowering stage).")
        else:
            missing.append("Exact crop age or growth stage (e.g., 30 days post-sowing, flowering stage).")

    if not district or not state:
        if language == "Hindi":
            missing.append("ज़िला और राज्य की जानकारी (ताकि मौसम और स्थानीय मिट्टी का सटीक आकलन हो सके)।")
        elif language == "Hinglish":
            missing.append("District aur State ki information (mausam aur mitti ke sahi assessment ke liye).")
        else:
            missing.append("District and State location details (for weather and regional soil context).")

    if language == "Hindi":
        missing.append("हाल के मौसम की स्थिति (जैसे कि क्या हाल ही में भारी बारिश, कोहरा या अत्यधिक गर्मी हुई है)।")
        missing.append("पत्तियों के निचले हिस्से या तने का कोई अन्य स्पष्ट लक्षण।")
    elif language == "Hinglish":
        missing.append("Recent weather condition (jaise heavy rain, fog, ya extreme heat).")
        missing.append("Leaves ke neeche ya stem par koi specific spots ya insects.")
    else:
        missing.append("Recent local weather conditions (e.g., excessive moisture, high humidity, or heatwave).")
        missing.append("Close-up symptoms on lower leaf surfaces, roots, or stems.")

    return missing

def get_safety_disclaimer(language: str = "English") -> str:
    """Returns standard language-specific agricultural safety disclaimer."""
    return DISCLAIMERS.get(language, DISCLAIMERS["English"])
