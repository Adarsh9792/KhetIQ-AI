import os
import json
import re
from typing import Dict, Any, Optional
from PIL import Image
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Path to agricultural knowledge base
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base.txt")

def get_api_key() -> Optional[str]:
    """Retrieves GEMINI_API_KEY from environment variables."""
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip() and not key.startswith("your_"):
        return key.strip()
    return None

def load_knowledge_base() -> str:
    """Loads the agricultural knowledge base text."""
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    return ""

def generate_demo_response(
    crop: str,
    question: str,
    language: str,
    has_image: bool = False
) -> Dict[str, Any]:
    """
    Generates realistic, safe, and structured agricultural advice in Safe Demo Mode
    when GEMINI_API_KEY is not configured or in demo testing.
    """
    crop_lower = crop.lower()
    q_lower = question.lower()

    if "wheat" in crop_lower or "गेहूं" in crop_lower:
        if language == "Hindi":
            return {
                "problem_understanding": "गेहूं की फ़सल में पत्तियों का पीला पड़ना या धब्बे होना पीला रतुआ (Yellow Rust) या नाइट्रोजन की कमी का संकेत है।",
                "possible_causes": [
                    "ठंडे और नमी वाले मौसम में फफूंद जनित पीला रतुआ (Puccinia striiformis) संक्रमण।",
                    "सिंचाई के बाद नाइट्रोजन (यूरिया) का असंतुलित उपयोग या जड़ों में पानी का भराव।"
                ],
                "recommended_actions": [
                    "प्रभावित पत्तियों का ध्यानपूर्वक निरीक्षण करें और देखें कि क्या पीली धारियाँ निकल रही हैं।",
                    "यदि पीला रतुआ है, तो शुरुआती अवस्था में नीम तेल (5ml प्रति लीटर पानी) का छिड़काव करें।",
                    "नाइट्रोजन की संतुलित मात्रा (यूरिया) दें, लेकिन जड़ों में अत्यधिक पानी न भरने दें।"
                ],
                "prevention_tips": [
                    "रोग प्रतिरोधी किस्मों (जैसे HD 2967, DBW 187) का चयन करें।",
                    "बुआई से पहले बीजोपचार जरूर करें।"
                ],
                "missing_information": [
                    "फ़सल की बुआई की सटीक तारीख और वर्तमान उम्र।",
                    "क्या पत्तियों पर हाथ लगाने पर पीला पाउडर चिपकता है?"
                ],
                "when_to_contact_expert": [
                    "यदि पीलापन 2-3 दिनों में पूरे खेत में तेजी से फैल रहा हो।",
                    "रासायनिक फफूंदनाशक का सुरक्षित प्रयोग करने से पहले निकटतम कृषि विज्ञान केंद्र (KVK) संपर्क करें।"
                ]
            }
        elif language == "Hinglish":
            return {
                "problem_understanding": "Wheat crop mein leaves ka peela padna Yellow Rust (Peela Ratua) ya Nitrogen deficiency ka symptom ho sakta hai.",
                "possible_causes": [
                    "Cool aur humid weather mein fungal infection (Yellow Rust).",
                    "Irrigation ke baad Nitrogen / Urea ka imbalance ya waterlogging."
                ],
                "recommended_actions": [
                    "Check karein ki leaves par yellow stripe shape spots hain ya nahi.",
                    "Neem Oil (5ml per litre water) spray karein for initial organic control.",
                    "Proper drainage maintain karein aur soil testing ke basis par urea dein."
                ],
                "prevention_tips": [
                    "Disease-resistant varieties (Jaise DBW 187, HD 3086) use karein.",
                    "Sowing se pehle fungicide seed treatment zaroori hai."
                ],
                "missing_information": [
                    "Crop ki exact age aur sowing date.",
                    "Kya yellow color leaves touch karne par haath par powder jaisa lagta hai?"
                ],
                "when_to_contact_expert": [
                    "Agar yellowing 2-3 din mein pure khet mein tezi se fael rahi ho.",
                    "Chemical fungicide spray ki exact dosage ke liye local Krishi Officer se milein."
                ]
            }
        else:
            return {
                "problem_understanding": "Yellowing or spots on wheat leaves suggest potential Yellow Rust (Puccinia striiformis) or Nitrogen deficiency.",
                "possible_causes": [
                    "Fungal infection favored by cool, cloudy, and humid weather conditions.",
                    "Nutrient imbalance or root waterlogging following heavy irrigation."
                ],
                "recommended_actions": [
                    "Inspect affected leaves for longitudinal yellow powdery pustules.",
                    "Apply Neem oil solution (5ml/L) as a safe early bio-control measure.",
                    "Ensure adequate drainage and balanced NPK fertilizer top-dressing."
                ],
                "prevention_tips": [
                    "Plant disease-resistant certified varieties (e.g., HD 3086, DBW 187).",
                    "Practice seed treatment prior to sowing."
                ],
                "missing_information": [
                    "Exact crop age in days and recent irrigation schedule.",
                    "Whether yellow powdery dust rubs off when touching leaf surfaces."
                ],
                "when_to_contact_expert": [
                    "If symptoms spread rapidly across large patches of the field within 48 hours.",
                    "Before spraying synthetic fungicides to obtain certified dosage guidance from local KVK scientists."
                ]
            }

    elif "tomato" in crop_lower or "टमाटर" in crop_lower:
        if language == "Hindi":
            return {
                "problem_understanding": "टमाटर की फ़सल में पत्तियों का मुड़ना (Leaf Curl Virus) या झुलसा रोग (Blight) का लक्षण दिखाई दे रहा है।",
                "possible_causes": [
                    "सफेद मक्खी (Whitefly) द्वारा फैलाया जाने वाला टमाटर पत्ती मरोड़ विषाणु।",
                    "आर्द्र मौसम में अगेती या पछेती झुलसा रोग का प्रकोप।"
                ],
                "recommended_actions": [
                    "सफेद मक्खियों को नियंत्रित करने के लिए पीले चिपचिपे कार्ड (Yellow Sticky Traps) लगाएं।",
                    "गंभीर रूप से संक्रमित छोटे पौधों को उखाड़कर नष्ट कर दें।",
                    "जैविक नियंत्रण के लिए नीम तेल छिड़कें।"
                ],
                "prevention_tips": [
                    "पौधों के चारों ओर जालीदार नेट (Insect Net) का प्रयोग करें।",
                    "खेत में खरपतवार न जमने दें।"
                ],
                "missing_information": [
                    "पौधे की उम्र और हाल ही में छिड़के गए रसायन।",
                    "क्या पत्तियों पर छोटे सफेद कीड़े उड़ते दिखाई दे रहे हैं?"
                ],
                "when_to_contact_expert": [
                    "यदि फल बनने से पहले 50% से अधिक पौधे प्रभावित हो गए हों।",
                    "कीटनाशक अनुशंसित मात्रा जानने के लिए ब्लॉक कृषि अधिकारी से मिलें।"
                ]
            }
        elif language == "Hinglish":
            return {
                "problem_understanding": "Tomato plants mein leaf curling (Leaf Curl Virus) ya leaf spots (Blight) ka issue lag raha hai.",
                "possible_causes": [
                    "Whitefly vector dwara faelne wala Leaf Curl Virus.",
                    "Humid weather mein early/late blight fungal growth."
                ],
                "recommended_actions": [
                    "Field mein Yellow Sticky Traps (10-15 per acre) lagayein.",
                    "Neem oil spray karein whitefly population kam karne ke liye.",
                    "Waterlogging avoid karein aur drip irrigation use karein."
                ],
                "prevention_tips": [
                    "Weed-free field maintain karein.",
                    "Resistant hybrid seeds choose karein."
                ],
                "missing_information": [
                    "Crop age in weeks aur fruit stage.",
                    "Kya leaves ke neeche chhote white flies dikh rahe hain?"
                ],
                "when_to_contact_expert": [
                    "Agar maximum plants mein stunting aur leaves curling start ho gayi ho.",
                    "Chemical pesticide spray ke liye local Agricultural Extension Officer se consult karein."
                ]
            }
        else:
            return {
                "problem_understanding": "Symptoms in tomato crop indicate possible Tomato Leaf Curl Virus or Early/Late Blight fungal infection.",
                "possible_causes": [
                    "Viral transmission carried by Whitefly vectors.",
                    "High atmospheric humidity promoting leaf fungal spots."
                ],
                "recommended_actions": [
                    "Install yellow sticky traps (10-12 per acre) to catch adult whiteflies.",
                    "Remove and safely burn severely stunt virus-infected seedlings.",
                    "Apply organic neem oil solution (5ml/L) as a safe preventive spray."
                ],
                "prevention_tips": [
                    "Keep borders free from weeds and alternate host plants.",
                    "Use certified disease-resistant tomato hybrids."
                ],
                "missing_information": [
                    "Crop stage (nursery, flowering, or fruiting).",
                    "Presence of visible white tiny insects under the leaves."
                ],
                "when_to_contact_expert": [
                    "If leaf curling spreads across over 40% of crop canopy.",
                    "To consult local KVK experts before deploying synthetic pest sprays."
                ]
            }

    # Default general advice for other crops or generic queries
    if language == "Hindi":
        return {
            "problem_understanding": f"{crop} की फ़सल के संबंध में आपकी जिज्ञासा प्राप्त हुई है। लक्षणों के आधार पर कीट प्रकोप या पोषक तत्वों का असंतुलन प्रतीत होता है।",
            "possible_causes": [
                "मौसम में बदलाव, हवा में नमी या तापमान में उतार-चढ़ाव।",
                "मुख्य पोषक तत्वों (नाइट्रोजन, फास्फोरस, पोटाश या जस्ता) की कमी।"
            ],
            "recommended_actions": [
                "पौधों के प्रभावित भागों (पत्तियों, तने और जड़ों) का सावधानीपूर्वक निरीक्षण करें।",
                "जैविक सुधार के रूप में नीम आधारित स्प्रे (Neem formulation) का प्रयोग करें।",
                "खेत में जल निकासी की सही व्यवस्था सुनिश्चित करें।"
            ],
            "prevention_tips": [
                "समय पर बुआई और फसल चक्र (Crop Rotation) का पालन करें।",
                "मिट्टी की जांच (Soil Test) के अनुसार ही उर्वरकों की मात्रा दें।"
            ],
            "missing_information": [
                "फ़सल की बुआई की तारीख और मौसम का हाल।",
                "पौधे पर धब्बों या कीटों का स्पष्ट विवरण या तस्वीर।"
            ],
            "when_to_contact_expert": [
                "यदि समस्या तेजी से पूरे खेत में फैल रही हो।",
                "रासायनिक उपचार की पुष्टि के लिए अपने स्थानीय कृषि अधिकारी (BAO/KVK) से संपर्क करें।"
            ]
        }
    elif language == "Hinglish":
        return {
            "problem_understanding": f"{crop} crop ke baare mein aapki inquiry mili hai. Symptoms ke basis par pest attack ya nutrient deficiency ho sakti hai.",
            "possible_causes": [
                "Weather changes, humidity ya temperature fluctuations.",
                "Essential nutrients (NPK, Zinc, Iron) ki kami."
            ],
            "recommended_actions": [
                "Affected plant parts (leaves, stem, roots) ko dhyaan se observe karein.",
                "Neem-based organic spray use karein early protection ke liye.",
                "Field mein proper water drainage maintain karein."
            ],
            "prevention_tips": [
                "Crop rotation follow karein.",
                "Soil testing report ke hisab se fertilizer apply karein."
            ],
            "missing_information": [
                "Crop ki age aur location details.",
                "Pest attack ya spots ki exact photo ya clear description."
            ],
            "when_to_contact_expert": [
                "Agar disease pooray khet mein tezi se spread ho raha ho.",
                "Chemical pesticide treatment ke liye Krishi Vigyan Kendra (KVK) scientist se advice lein."
            ]
        }
    else:
        return {
            "problem_understanding": f"Analysis received regarding {crop} crop query. Preliminary indicators suggest possible pest pressure or nutrient imbalance.",
            "possible_causes": [
                "Environmental stress such as rapid temperature shift or high relative humidity.",
                "Macro/micronutrient deficiencies (NPK or Zinc imbalance)."
            ],
            "recommended_actions": [
                "Examine root zone and lower leaf surfaces for early pest activity.",
                "Apply organic bio-pesticide (Neem oil 5ml/L) as safe initial measure.",
                "Ensure balanced soil moisture without water stagnation."
            ],
            "prevention_tips": [
                "Adhere to proper crop rotation and field sanitation.",
                "Use fertilizer dosage strictly based on recent Soil Health Card recommendations."
            ],
            "missing_information": [
                "Exact crop age, field location, and recent rainfall/irrigation history.",
                "Close-up photo or precise physical description of affected plant tissue."
            ],
            "when_to_contact_expert": [
                "If wilting or leaf damage spreads to more than 30% of the standing crop.",
                "Prior to buying synthetic crop protection chemicals from local agri-dealers."
            ]
        }

def get_ai_agricultural_advice(
    crop: str,
    question: str,
    language: str = "English",
    village: str = "",
    district: str = "",
    state: str = "",
    crop_age: str = "",
    image: Optional[Image.Image] = None,
    force_demo: bool = False
) -> Dict[str, Any]:
    """
    Calls the Gemini API (using google-genai package) to analyze crop issue and produce advice.
    Falls back gracefully to Safe Demo Mode if API key is missing or call fails.
    """
    api_key = get_api_key()

    if force_demo or not api_key:
        return generate_demo_response(crop, question, language, has_image=(image is not None))

    kb_text = load_knowledge_base()

    # System instruction prompt
    system_prompt = f"""
You are KhetIQ AI, an empathetic, highly skilled, and safety-conscious Agricultural Expert Advisor for Indian farmers.

CRITICAL INSTRUCTIONS & CONSTRAINTS:
1. Target Audience: Smallholder farmers in India. Use simple, direct, practical language.
2. Target Language: {language}.
   - If language is "Hindi", respond ONLY in pure Devanagari Hindi (हिंदी).
   - If language is "Hinglish", respond in conversational Hinglish (Hindi written in Roman script).
   - If language is "English", respond in clear, accessible English.
3. Incorporate Knowledge Base Context where applicable:
{kb_text[:3000]}

4. YOU MUST RETURN ONLY A VALID JSON OBJECT with the following exact key structure:
{{
  "problem_understanding": "Clear, short summary of what the farmer is experiencing",
  "possible_causes": ["Cause 1", "Cause 2"],
  "recommended_actions": ["Action 1 (emphasize organic/safe IPM methods)", "Action 2"],
  "prevention_tips": ["Tip 1", "Tip 2"],
  "missing_information": ["Missing detail 1", "Missing detail 2"],
  "when_to_contact_expert": ["Condition 1 to consult KVK/Agri Officer", "Condition 2"]
}}

5. SAFETY & LEGAL MANDATE:
   - Do NOT provide dangerous, unverified, or lethal chemical pesticide dosages.
   - Advise organic, bio-control, or cultural methods first (e.g. Neem oil, sticky traps, drainage).
   - Always instruct farmer to verify chemical products at the local Krishi Vigyan Kendra (KVK) or Block Agriculture Office.
   - Do not claim a 100% conclusive diagnostic certainty without enough evidence.
"""

    user_content = f"""
Farmer Query Details:
- Crop: {crop}
- Location: {village}, {district}, {state}
- Crop Age/Stage: {crop_age}
- Question/Symptoms: {question}
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        contents = []
        if image is not None:
            contents.append(image)
        contents.append(user_content)

        # Updated Active Gemini models list
        models_to_try = [
            'gemini-3.6-flash',
            'gemini-3.5-flash',
            'gemini-flash-latest',
            'gemini-2.5-pro'
        ]

        response = None
        last_error = None

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.3
                    )
                )
                if response and response.text:
                    break
            except Exception as err:
                last_error = err
                continue

        if not response or not response.text:
            raise Exception(str(last_error or "All Gemini models failed."))

        response_text = response.text.strip()
        
        # Clean markdown wrappers if any
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON response
        parsed = json.loads(response_text)
        
        # Ensure all required keys exist
        required_keys = [
            "problem_understanding", "possible_causes", "recommended_actions",
            "prevention_tips", "missing_information", "when_to_contact_expert"
        ]
        for key in required_keys:
            if key not in parsed:
                parsed[key] = [] if key != "problem_understanding" else "Analysis completed."
                
        return parsed

    except Exception as e:
        # If API call fails, fallback to Demo response with notice
        demo_resp = generate_demo_response(crop, question, language, has_image=(image is not None))
        demo_resp["api_error"] = str(e)
        return demo_resp
