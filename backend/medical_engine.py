"""
Niramaya Health AI - Dynamic Medical Intelligence & Health Domain Engine
Accepts ANY random health/medical question dynamically.
Strictly rejects non-health related queries.
Integrates trained ML models (Logistic Regression + Symptom Features + Precaution CSVs).
"""

import os
import re
import joblib
import pandas as pd

# Load Trained ML Models and Medical CSV Datasets
BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, 'model_LR')
MODEL_V1_PATH = os.path.join(MODEL_DIR, 'logistic_regression_model.pkl')
FEATURES_V1_PATH = os.path.join(MODEL_DIR, 'symptom_features.pkl')
MODEL_V2_PATH = os.path.join(MODEL_DIR, 'disease_prediction_model.pkl')
MLB_V2_PATH = os.path.join(MODEL_DIR, 'symptom_mlb.pkl')
DESC_PATH = os.path.join(MODEL_DIR, 'Symptom_Description.csv')
PREC_PATH = os.path.join(MODEL_DIR, 'Symptom_Precaution.csv')

lr_model = None
symptom_features = []
rf_model = None
symptom_mlb = None
df_desc = pd.DataFrame()
df_prec = pd.DataFrame()

try:
    if os.path.exists(MODEL_V1_PATH):
        lr_model = joblib.load(MODEL_V1_PATH)
    if os.path.exists(FEATURES_V1_PATH):
        symptom_features = list(joblib.load(FEATURES_V1_PATH))
    if os.path.exists(MODEL_V2_PATH):
        rf_model = joblib.load(MODEL_V2_PATH)
    if os.path.exists(MLB_V2_PATH):
        symptom_mlb = joblib.load(MLB_V2_PATH)
    if os.path.exists(DESC_PATH):
        df_desc = pd.read_csv(DESC_PATH)
    if os.path.exists(PREC_PATH):
        df_prec = pd.read_csv(PREC_PATH)
except Exception as e:
    print(f"Medical engine ML load notice: {e}")

# ==============================================================================
# Strict Symptom-Only Domain Guardrail (NO General ChatGPT-style Chat)
# ==============================================================================

# Obvious non-health / general-chatbot domains to strictly reject
OUT_OF_DOMAIN_PATTERNS = [
    r'\b(python|javascript|java|c\+\+|html|css|programming|coding|algorithm|compiler|database|sql|github|developer|debug|syntax|script|api key|software|react|nodejs|flask|django)\b',
    r'\b(prime minister|president of|election|politics|parliament|bjp|congress|politician|government policy|democracy|minister)\b',
    r'\b(cricket|football|fifa|ipl|wicket|match score|messi|ronaldo|champions trophy|batting|bowling|tennis|badminton|olympics|world cup)\b',
    r'\b(movie|cinema|actor|actress|bollywood|hollywood|trailer|song|music|lyrics|director|film|album|singer|netflix)\b',
    r'\b(bitcoin|crypto|cryptocurrency|stock market|share market|trading|sensex|nifty|mutual fund|forex|bank account|rupee rate|earn money|make money|business plan|startup)\b',
    r'\b(capital of|weather|forecast|flight ticket|train ticket|hotel booking|railway|irctc|geography|tallest mountain|river|planet|galaxy|universe|spain|france|london|paris)\b',
    r'\b(tell me a joke|write a poem|write a story|write an email|write a letter|write an essay|sing a song|solve math|calculate|essay on|riddle|funny story|translate|summarize|homework|assignment|resume|cover letter)\b',
    r'\b(how to cook|recipe for|bake a cake|car repair|bike repair|engine|mechanic|iphone|android phone|laptop|computer|wifi|television|tv)\b',
    r'\b(chatgpt|openai|chat with me|let\'s chat|lets chat|talk to me|who made you|who created you|horoscope|astrology|love advice|relationship advice|interview questions|quantum physics|teacher|school|college|exam)\b'
]

# Strictly unambiguous single-word medical symptoms, diseases & Hindi/Hinglish symptom terms
# Matched ONLY on whole-word boundaries (\b...\b) — NEVER substring inside unrelated words!
EXACT_MEDICAL_TERMS = {
    # Core symptoms & typos
    'fever', 'fevr', 'feaver', 'pyrexia', 'chills', 'shivering', 'sweating',
    'headache', 'headche', 'hedache', 'heache', 'migraine', 'migrene', 'cephalalgia',
    'cough', 'coughing', 'caugh', 'phlegm', 'sputum', 'mucus', 'wheezing', 'wheeze',
    'flu', 'influenza', 'sneeze', 'sneezing', 'congestion', 'sinus', 'sinusitis',
    'tonsillitis', 'pharyngitis', 'laryngitis', 'tonsil', 'tonsils',
    'ache', 'aches', 'aching', 'pain', 'pains', 'painful', 'cramp', 'cramps', 'stiffness', 'soreness', 'hurts', 'hurting',
    'nausea', 'nauseous', 'queasy', 'vomit', 'vomiting', 'vomitting',
    'diarrhea', 'diarrhoea', 'diarhea', 'dysentery', 'constipation', 'constipated',
    'indigestion', 'acidity', 'heartburn', 'gerd', 'reflux', 'bloating', 'bloated', 'flatulence', 'belching', 'gastritis', 'colitis', 'ibs',
    'hemorrhoid', 'hemorrhoids', 'piles', 'fissure', 'fistula', 'hernia', 'appendicitis',
    'angina', 'palpitation', 'palpitations', 'tachycardia', 'bradycardia', 'arrhythmia',
    'breathless', 'breathlessness', 'dyspnea', 'suffocation', 'asthma', 'bronchitis', 'copd', 'pneumonia',
    'dizzy', 'dizziness', 'dizines', 'vertigo', 'lightheaded', 'lightheadedness', 'faint', 'fainting', 'syncope', 'blackout',
    'fatigue', 'tiredness', 'weakness', 'lethargy', 'lethargic', 'exhaustion', 'malaise',
    'numbness', 'tingling', 'paralysis', 'tremor', 'tremors', 'seizure', 'seizures', 'convulsion', 'convulsions',
    'insomnia', 'insomia', 'sleepless', 'sleeplessness', 'anxiety', 'anxious', 'depression', 'depressed',
    'rash', 'rashes', 'itching', 'itchy', 'pruritus', 'allergy', 'allergic', 'allergies', 'hives', 'urticaria',
    'swelling', 'swollen', 'edema', 'oedema', 'inflammation', 'inflamed',
    'acne', 'pimple', 'pimples', 'eczema', 'psoriasis', 'dandruff', 'hairfall', 'alopecia',
    'bleeding', 'hemorrhage', 'bruise', 'bruising', 'hematoma', 'ulcer', 'ulcers', 'wound', 'wounds', 'injury', 'injuries', 'blister', 'blisters', 'boil', 'boils', 'pus',
    'dehydration', 'dehydrated', 'uti', 'nephritis',
    'diabetes', 'diabetic', 'hyperglycemia', 'hypoglycemia', 'insulin',
    'hypertension', 'hypotension', 'thyroid', 'hypothyroidism', 'hyperthyroidism', 'cholesterol', 'anemia', 'anaemia', 'anaemic', 'anemic',
    'arthritis', 'osteoarthritis', 'rheumatoid', 'myalgia', 'gout', 'sciatica', 'sprain', 'strain', 'fracture', 'backache', 'earache', 'toothache', 'stomachache',
    'conjunctivitis', 'tinnitus', 'cataract', 'glaucoma',
    'infection', 'infections', 'infectious', 'viral', 'bacterial', 'fungal',
    'dengue', 'malaria', 'typhoid', 'cholera', 'jaundice', 'hepatitis', 'tuberculosis', 'chikungunya', 'covid', 'coronavirus', 'measles', 'chickenpox', 'rabies', 'tetanus',
    'stroke', 'tumor', 'tumour', 'cancer', 'leukemia',
    'symptom', 'symptoms', 'illness', 'sickness', 'disease', 'diseases', 'syndrome', 'disorder', 'diagnosis', 'prognosis',
    'prescription', 'dosage', 'antibiotic', 'antibiotics', 'paracetamol', 'ibuprofen', 'antacid', 'ors',
    # Hindi / Hinglish unambiguous symptom terms
    'bukhar', 'bukhaar', 'dard', 'peeda', 'peedha',
    'khansi', 'khaansi', 'sardi', 'jukam', 'jukaam', 'zukaam', 'nazla',
    'ulti', 'ultiyan', 'ubkai', 'dast', 'jalan', 'chakkar', 'kamzori', 'thakan', 'thakawaat',
    'sujan', 'soojan', 'khujli', 'daane', 'funsi', 'foda', 'khoon', 'kharash',
    'dawai', 'dawa', 'ilaj', 'ilaaj', 'bimari', 'bimaar', 'tabiyat', 'upchar', 'perhez', 'savdhani'
}

# Multi-word medical symptom phrases (matched on word boundaries)
MEDICAL_PHRASES = [
    'sore throat', 'runny nose', 'blocked nose', 'stuffy nose', 'nasal congestion',
    'shortness of breath', 'difficulty breathing', 'trouble breathing', 'chest tightness', 'chest pain',
    'stomach pain', 'stomach ache', 'belly pain', 'abdominal pain', 'upset stomach', 'food poisoning',
    'loose motion', 'loose motions', 'watery stool', 'blood in stool', 'black stool',
    'back pain', 'lower back', 'neck pain', 'joint pain', 'knee pain', 'shoulder pain', 'body pain', 'muscle pain', 'leg pain', 'arm pain',
    'head pain', 'ear pain', 'eye pain', 'red eye', 'red eyes', 'blurred vision', 'blurry vision', 'dry eyes', 'watery eyes',
    'tooth pain', 'gum bleeding', 'bleeding gums', 'mouth ulcer', 'canker sore',
    'skin rash', 'skin itching', 'skin infection', 'skin allergy', 'hair loss', 'hair fall',
    'weight loss', 'weight lose', 'weight gain', 'loss of appetite', 'no appetite', 'night sweats',
    'high temperature', 'high fever', 'mild fever', 'low fever', 'body heat',
    'blood pressure', 'high bp', 'low bp', 'blood sugar', 'high sugar', 'low sugar', 'sugar level',
    'kidney stone', 'kidney stones', 'gall stone', 'gallstones', 'fatty liver', 'urinary tract', 'burning urination', 'frequent urination', 'painful urination',
    'acid reflux', 'gastric problem', 'gas problem', 'gas in stomach', 'digestive issue', 'digestive issues', 'digestive problem', 'digestive problems', 'digestive health', 'gut health', 'gut issue', 'gut problem',
    'panic attack', 'mental stress', 'cant sleep', "can't sleep", 'cannot sleep', 'trouble sleeping', 'sleep problem', 'sleep disorder',
    'cold and cough', 'cough and cold', 'have a cold', 'common cold', 'catching a cold', 'bad cold', 'severe cold',
    'heart rate', 'heart beat', 'heartbeat', 'heart attack', 'heart pain', 'racing heart',
    'sir dard', 'sar dard', 'pet dard', 'pet kharab', 'pet me dard', 'pet me jalan',
    'chhati dard', 'chhati me dard', 'seene me dard', 'saans fulna', 'saans lene me dikkat', 'saans me taklif',
    'gala dard', 'gale me dard', 'gale me kharash', 'khich khich',
    'badan dard', 'body dard', 'kamar dard', 'peeth dard', 'jism dard',
    'ghutna dard', 'guthno me dard', 'jod dard', 'jodon ka dard',
    'chakkar aana', 'khoon aana', 'lal daane', 'gharelu nuskhe'
]

# Body parts that count as health queries ONLY when paired with a clinical/symptom qualifier
ANATOMY_WORDS = {
    'stomach', 'abdomen', 'abdominal', 'belly', 'gut', 'digestive', 'digestion', 'bowel', 'colon', 'liver', 'kidney', 'kidneys', 'bladder', 'pancreas', 'gallbladder',
    'chest', 'heart', 'cardiac', 'lung', 'lungs', 'throat', 'tonsil', 'sinus', 'nose', 'nasal',
    'head', 'brain', 'nerve', 'nerves', 'spine', 'spinal', 'back', 'neck', 'shoulder', 'knee', 'joint', 'joints', 'muscle', 'muscles', 'bone', 'bones', 'ankle', 'wrist', 'elbow', 'hip',
    'skin', 'scalp', 'hair', 'eye', 'eyes', 'ear', 'ears', 'mouth', 'tongue', 'tooth', 'teeth', 'gum', 'gums',
    'urine', 'urinary', 'blood', 'pulse', 'breath', 'breathing', 'period', 'periods', 'menstrual'
}

SYMPTOM_QUALIFIERS = {
    'pain', 'ache', 'hurts', 'hurting', 'sore', 'burn', 'burning', 'itch', 'itching', 'rash', 'swell', 'swelling', 'swollen',
    'red', 'redness', 'bleed', 'bleeding', 'cramp', 'cramps', 'stiff', 'tight', 'tightness', 'numb', 'tingling', 'weak', 'weakness',
    'problem', 'problems', 'issue', 'issues', 'infection', 'infected', 'inflammation', 'inflamed', 'disorder', 'disease', 'condition',
    'dry', 'watery', 'blurry', 'blurred', 'blocked', 'congestion', 'heavy', 'heaviness', 'lump', 'ulcer', 'sore', 'discharge',
    'fever', 'cough', 'cold', 'gas', 'acid', 'acidity', 'stone', 'stones', 'loss', 'fall', 'gain', 'high', 'low', 'irregular',
    'doctor', 'medicine', 'treatment', 'remedy', 'cure', 'care', 'health', 'precaution', 'symptom', 'symptoms', 'relief', 'check'
}


def is_health_related(query: str) -> bool:
    """
    Strict Symptom & Medical Domain Guardrail:
    - ONLY allows genuine health symptoms, medical conditions, or body-organ clinical queries.
    - STRICTLY refuses ChatGPT-style general chat (coding, trivia, politics, sports, weather, essays, etc.).
    - Uses whole-word boundaries (NEVER sloppy substring matching that lets 'ear' match 'year' or 'pain' match 'spain').
    """
    if not query or not query.strip():
        return False
    clean = query.lower().strip()

    # 1. Immediately reject explicit non-medical / general-chatbot queries
    for pat in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pat, clean):
            # Allow ONLY if accompanied by explicit physical injury / clinical emergency
            if re.search(r'\b(injury|fracture|bleeding|hospital|emergency|burn wound)\b', clean):
                return True
            return False

    # Tokenize into exact whole words
    words = set(re.findall(r"[a-zA-Z']+", clean))

    # 2. Match multi-word medical phrases on word boundaries
    for phrase in MEDICAL_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', clean):
            return True

    # 3. Match exact trained ML symptom features on word boundaries
    if len(symptom_features) > 0:
        for f in symptom_features:
            f_clean = str(f).lower().replace('_', ' ').strip()
            if len(f_clean) >= 3 and re.search(r'\b' + re.escape(f_clean) + r'\b', clean):
                return True

    # 4. Match exact unambiguous medical/symptom words
    if words & EXACT_MEDICAL_TERMS:
        return True

    # 5. Match anatomical/organ terms ONLY when combined with a symptom/clinical qualifier
    if (words & ANATOMY_WORDS) and (words & SYMPTOM_QUALIFIERS):
        return True

    # 6. Allow standalone medical/digestive/gut single-phrase inputs like "digestive" or "cold" (without weather words)
    if 'cold' in words and not (words & {'weather', 'outside', 'today', 'winter', 'water', 'drink', 'coffee', 'tea', 'ice', 'room', 'ac'}):
        if len(words) <= 5 or (words & {'have', 'having', 'got', 'feel', 'feeling', 'suffering', 'severe', 'mild', 'bad', 'my', 'i'}):
            return True

    # 7. Everything else is outside the symptom-checker domain -> strictly refuse
    return False


def get_non_health_refusal_message() -> str:
    """Standard message returned when a user asks a general ChatGPT-style / non-symptom question."""
    return (
        "⚠️ **Medical & Symptom Checker Domain Restriction:**\n\n"
        "I am your **Niramaya AI Health Assistant**. I am specialized **exclusively in health symptoms, medical conditions, and clinical precautions** — I do **not** act as a general chatbot like ChatGPT.\n\n"
        "I cannot answer non-medical questions (such as general knowledge, coding, essays, politics, sports, weather, recipes, or casual conversation).\n\n"
        "👉 **Please describe your health symptoms** (e.g., *fever, headache, cough, sore throat, body pain, dizziness, stomach ache, digestive issues, skin rash*) to receive instant clinical assessment, home care, and precautions."
    )

# ==============================================================================
# Comprehensive Symptom-Specific Clinical Knowledge Profiles
# ==============================================================================

CLINICAL_PROFILES = {
    'digestive': {
        'name': 'Gastrointestinal & Digestive Health (पाचन तंत्र)',
        'keywords': [
            'digest', 'digestive', 'digestion', 'stomach', 'belly', 'abdomen', 'abdominal',
            'acidity', 'gas', 'bloat', 'bloating', 'indigestion', 'heartburn', 'gerd', 'reflux',
            'constipat', 'bowel', 'bowels', 'stool', 'stools', 'gut', 'colitis', 'ibs',
            'flatulence', 'belch', 'belching', 'burp', 'burping', 'food poisoning', 'liver',
            'gallbladder', 'pancrea', 'piles', 'hemorrhoid', 'hemorrhoids', 'fistula', 'fissure',
            'pet dard', 'pet kharab', 'pet me jalan', 'jalan'
        ],
        'condition': 'Functional Dyspepsia & Gastrointestinal Disturbance (पाचन संबंधी समस्या)',
        'overview': (
            "Gastrointestinal symptoms reflect altered motility, mucosal irritation, acid imbalances, or disrupted gut flora (dysbiosis). "
            "Proper digestive function relies on timely enzyme secretion, balanced microbial ecology, and calm autonomic gut-brain axis regulation."
        ),
        'causes': [
            "Gastric hyperacidity, GERD (acid reflux), or mucosal irritation from spicy or unhygienic foods",
            "Irritable Bowel Syndrome (IBS) or food intolerance (lactose, gluten, or excessive artificial sugars)",
            "Disruption of healthy intestinal microflora (gut dysbiosis) following irregular diet or antibiotic usage",
            "Sluggish bowel motility, low dietary fiber intake, or stress-mediated gut spasms"
        ],
        'home_care': [
            "Probiotic Support: Consume fresh homemade curd, plain yogurt, or buttermilk with roasted cumin powder",
            "Digestive Infusions: Sip lukewarm water infused with fennel seeds (saunf) and ginger after meals",
            "Bland Nutrition: Opt for light moong dal khichdi, steamed rice, boiled oats, and ripe bananas (BRAT diet)",
            "Meal Timing: Allow 2 to 3 hours between your last meal and bedtime to prevent nocturnal acid reflux"
        ],
        'precautions': [
            "Strictly avoid deep-fried oily foods, heavy creamy gravies, carbonated sodas, and excessive caffeine",
            "Eat small, frequent meals and chew every bite thoroughly; avoid skipping meals or fasting for prolonged hours",
            "Do not lie flat immediately after eating; maintain an upright posture for at least 45 minutes"
        ],
        'red_flags': [
            "🚨 Severe, sharp, or sudden agonizing abdominal pain with guarding or abdominal rigidity",
            "🚨 Presence of blood in stools (black tarry stool or bright red blood) or coffee-ground vomiting",
            "🚨 Persistent inability to keep fluids or food down for over 24 hours",
            "🚨 High fever accompanied by chills or yellowish discoloration of the eyes and skin (jaundice)"
        ]
    },
    'throat_ent': {
        'name': 'Pharyngeal & Upper Respiratory ENT (गला व टॉन्सिल)',
        'keywords': [
            'throat', 'sore throat', 'tonsil', 'tonsillitis', 'pharyngitis', 'laryngitis',
            'swallow', 'swallowing', 'hoarse', 'hoarseness', 'vocal', 'voice', 'gala', 'gale',
            'kharash', 'khich khich'
        ],
        'condition': 'Acute Pharyngitis & Pharyngeal Mucosal Irritation (गले में खराश व संक्रमण)',
        'overview': (
            "Throat irritation and pharyngitis involve acute inflammation of the mucous membranes lining the pharynx, tonsils, or larynx. "
            "It is most commonly triggered by viral or bacterial invasion, post-nasal drip, or acid reflux reaching the posterior pharynx."
        ),
        'causes': [
            "Viral pharyngitis (rhinovirus, adenovirus, or influenza virus infection)",
            "Bacterial tonsillopharyngitis (such as Streptococcus pyogenes / strep throat)",
            "Laryngopharyngeal reflux (LPR / silent acid reflux irritating the throat during sleep)",
            "Post-nasal drip from allergic rhinitis, exposure to dry refrigerated air, or vocal strain"
        ],
        'home_care': [
            "Warm Saline Gargles: Gargle with 1/2 teaspoon of salt in a glass of warm water 3 to 4 times daily",
            "Soothing Sips: Drink warm water with pure honey, grated ginger, and holy basil (tulsi) leaves",
            "Steam Inhalation: Inhale warm water vapor for 5 to 7 minutes to lubricate dry pharyngeal mucosa",
            "Soft Nourishment: Eat warm vegetable broths, clear soups, and pureed dishes that slide easily down the throat"
        ],
        'precautions': [
            "Strictly avoid cold refrigerated drinks, ice cream, spicy peppers, and acidic citrus juices",
            "Avoid shouting, whispering, or constant throat-clearing; rest your vocal cords",
            "Do not share drinking glasses or utensils to prevent airborne viral spread"
        ],
        'red_flags': [
            "🚨 Inability to swallow saliva, fluids, or food; severe painful swallowing (odynophagia)",
            "🚨 Difficulty breathing, audible whistling breath sounds (stridor), or throat constriction",
            "🚨 Marked asymmetric swelling of tonsils or inability to open mouth fully (trismus / peritonsillar abscess)",
            "🚨 High persistent fever (>102°F) accompanied by visible white pus patches on the tonsils"
        ]
    },
    'respiratory_cough': {
        'name': 'Respiratory Airway & Bronchial Tract (खांसी व श्वास)',
        'keywords': [
            'cough', 'coughing', 'cold', 'sneeze', 'sneezing', 'congestion', 'runny nose',
            'blocked nose', 'sinus', 'sinusitis', 'phlegm', 'sputum', 'mucus', 'wheez',
            'bronchitis', 'asthma', 'breath', 'breathing', 'breathless', 'breathlessness',
            'shortness of breath', 'dyspnea', 'suffocation', 'khansi', 'sardi', 'jukam', 'saans'
        ],
        'condition': 'Upper Respiratory Congestion & Bronchial Irritation (श्वास नली संक्रमण व खांसी)',
        'overview': (
            "Respiratory symptoms reflect inflammation and hyperreactivity of the tracheobronchial tree and nasal mucosa. "
            "Coughing is the body's vital physiological protective reflex to clear foreign matter, irritants, and excess mucus."
        ),
        'causes': [
            "Acute viral upper respiratory tract infection (common cold, viral flu, or bronchitis)",
            "Bronchial airway hyperreactivity or seasonal allergic rhinitis triggered by dust, pollen, or pollution",
            "Accumulation of post-nasal drip in the hypopharynx causing nocturnal coughing fits",
            "Secondary bacterial bronchial congestion following an initial viral cold"
        ],
        'home_care': [
            "Steam Inhalation: Inhale plain warm water steam for 5 to 10 minutes twice daily to loosen viscous mucus",
            "Warm Turmeric Milk: Drink a cup of warm milk with a pinch of turmeric and black pepper before bed",
            "Airway Hydration: Drink at least 2.5 to 3 liters of warm water and clear broths to thin airway secretions",
            "Head Elevation: Sleep with an extra pillow to prevent mucus from pooling in your upper throat at night"
        ],
        'precautions': [
            "Avoid exposure to cold wind, air conditioning drafts, tobacco smoke, and vehicle exhaust",
            "Cover your nose and mouth when coughing or sneezing; wash hands thoroughly with soap",
            "Avoid suppressive cough syrups if you have productive phlegm without medical guidance"
        ],
        'red_flags': [
            "🚨 Rapid, labored breathing, shortness of breath, or flaring of nostrils",
            "🚨 Coughing up blood (hemoptysis) or rust-colored thick phlegm",
            "🚨 High fever persisting beyond 3 days or accompanied by sharp localized chest pain on deep inspiration",
            "🚨 Bluish discoloration of lips, tongue, or nailbeds (cyanosis / oxygen drop)"
        ]
    },
    'fever_infection': {
        'name': 'Systemic Pyrexia & Infectious Illness (बुखार व संक्रमण)',
        'keywords': [
            'fever', 'pyrexia', 'temperature', 'chills', 'shivering', 'sweat', 'sweating',
            'night sweats', 'bukhar', 'tapman'
        ],
        'condition': 'Acute Pyrexia & Systemic Immune Response (वायरल बुखार व संक्रमण)',
        'overview': (
            "Fever (pyrexia) is an active immune-mediated defense mechanism orchestrated by the hypothalamus in response to pyrogens. "
            "Elevating body temperature inhibits the replication of pathogens and accelerates the activation of white blood cells."
        ),
        'causes': [
            "Systemic viral infection (such as seasonal influenza, viral flu, dengue, or chikungunya)",
            "Bacterial focal infection (urinary tract, respiratory tract, or gastrointestinal tract)",
            "Localized inflammatory response following exposure, exhaustion, or immunization"
        ],
        'home_care': [
            "Complete Bed Rest: Minimize all physical exertion to conserve metabolic energy for immune defense",
            "Electrolyte Hydration: Drink generous amounts of ORS, tender coconut water, diluted fruit juices, and clear soups",
            "Tepid Sponging: Gently wipe the forehead, neck, armpits, and extremities with lukewarm water (never ice water)",
            "Light Nourishment: Consume easily digestible foods like thin dal soup, barley water, rice porridge, and stewed fruits"
        ],
        'precautions': [
            "Do not bundle up the patient in heavy blankets or tight synthetic clothes; allow body heat to dissipate naturally",
            "Record body temperature with a digital thermometer every 4 hours in a logbook",
            "Never self-administer unprescribed multiple analgesics or antibiotics"
        ],
        'red_flags': [
            "🚨 Temperature exceeding 103°F (39.4°C) or fever not coming down with standard antipyretics",
            "🚨 Fever accompanied by severe stiff neck, confusion, delirium, or seizures (convulsions)",
            "🚨 Appearance of pinpoint red or purple spots on the skin (petechiae / dengue warning sign)",
            "🚨 Inability to drink fluids accompanied by extreme weakness or unresponsiveness"
        ]
    },
    'vomiting_diarrhea': {
        'name': 'Acute Enteric & Gastroenteritis (उल्टी व दस्त)',
        'keywords': [
            'vomit', 'vomiting', 'nausea', 'queasy', 'diarrhea', 'diarrhoea', 'loose motion',
            'motions', 'dysentery', 'ulti', 'dast'
        ],
        'condition': 'Acute Gastroenteritis & Dehydration Risk (उल्टी, दस्त व आंत्र संक्रमण)',
        'overview': (
            "Vomiting and loose motions represent protective gastrointestinal purging responses to toxins, viral pathogens, or bacteria. "
            "The principal clinical danger is rapid depletion of bodily fluids and vital electrolytes (sodium, potassium)."
        ),
        'causes': [
            "Acute viral gastroenteritis (norovirus or rotavirus infection of enteric mucosa)",
            "Bacterial food poisoning from contaminated street food, unpasteurized dairy, or spoiled water",
            "Acute drug-induced gastric intolerance or sudden osmotic intestinal irritation"
        ],
        'home_care': [
            "Oral Rehydration Therapy: Sip WHO-formula ORS solution, tender coconut water, or salted rice kanji after each loose stool",
            "Frequent Small Sips: Take small sips (30-50ml) every 10-15 minutes rather than large glasses to avoid triggering the gag reflex",
            "Gentle Re-feeding: Once vomiting ceases for 4 hours, start with plain boiled rice, bananas, and dry toast",
            "Probiotic Restitution: Fresh homemade curd or lactobacillus culture to restore gut mucosal defenses"
        ],
        'precautions': [
            "Strictly avoid whole milk, cheese, butter, fried snacks, and heavily spiced dishes until digestion normalizes",
            "Wash hands thoroughly with soap and clean water before eating and after using the restroom",
            "Do not take unprescribed antimotility pills (like loperamide) if you have high fever or bloody stools"
        ],
        'red_flags': [
            "🚨 Total inability to retain liquids for more than 12 hours with dry mouth and sunken eyes",
            "🚨 Absence of urination for over 8 hours (indicative of acute renal dehydration strain)",
            "🚨 Stools containing visible blood, dark black tarry material, or copious mucus",
            "🚨 Severe unremitting abdominal colic, high fever, or profound lethargy"
        ]
    },
    'headache_migraine': {
        'name': 'Neurological & Cephalea (सिर दर्द व माइग्रेन)',
        'keywords': [
            'headache', 'migraine', 'head ache', 'head pain', 'cephalalgia', 'sir dard', 'sar dard'
        ],
        'condition': 'Cephalea & Tension / Migraine Assessment (सिर दर्द व माइग्रेन)',
        'overview': (
            "Headaches typically arise from irritation of pain-sensitive cranial structures, pericranial muscle tension, or neurovascular spasms. "
            "Differentiating primary headaches (tension, migraine) from secondary systemic headaches is essential for safe management."
        ),
        'causes': [
            "Tension-type headache from sustained mental stress, eye fatigue, prolonged screen exposure, or neck stiffness",
            "Vascular migraine triggered by irregular sleep patterns, skipping meals, hormonal shifts, or bright sensory glare",
            "Dehydration, reduced fluid intake, sinus barometric pressure, or caffeine withdrawal"
        ],
        'home_care': [
            "Quiet Darkened Rest: Rest in a dark, quiet, well-ventilated room free from screen glare and acoustic stimulation",
            "Rapid Hydration: Drink 500ml of clean, cool water immediately (dehydration is a leading trigger of sudden headaches)",
            "Cold Compress Therapy: Apply an ice pack wrapped in a cloth or a cool damp compress over the forehead or back of neck",
            "Gentle Postural Relief: Perform slow neck rolls and gentle shoulder stretches to release cervical muscle contraction"
        ],
        'precautions': [
            "Avoid staring into mobile, tablet, or monitor screens during an active headache episode",
            "Avoid skipping meals; maintain consistent daily eating and sleeping schedules",
            "Limit regular intake of over-the-counter painkillers to prevent rebound medication-overuse headaches"
        ],
        'red_flags': [
            "🚨 Sudden explosive, severe 'thunderclap' headache reaching peak intensity within seconds",
            "🚨 Headache accompanied by high fever, neck stiffness (inability to touch chin to chest), or confusion",
            "🚨 Focal neurological deficits: facial dropping, arm weakness, slurred speech, or vision loss",
            "🚨 Headache following recent head trauma or progressive worsening over days"
        ]
    },
    'cardiovascular_chest': {
        'name': 'Cardiothoracic & Circulation (सीने में दर्द व हृदय)',
        'keywords': [
            'chest', 'chest pain', 'angina', 'heart', 'cardiac', 'palpitation', 'palpitations',
            'tachycardia', 'chhati dard', 'seene me dard'
        ],
        'condition': 'Cardiothoracic Assessment & Precautionary Triage (सीने में दर्द व हृदय मूल्यांकन)',
        'overview': (
            "Chest symptoms demand rigorous clinical scrutiny to distinguish benign musculoskeletal or esophageal irritation from acute coronary syndromes. "
            "Any sudden, crushing, or radiating chest sensation requires immediate emergency medical exclusion."
        ),
        'causes': [
            "Musculoskeletal chest wall tenderness (costochondritis, intercostal strain, or heavy lifting)",
            "Gastroesophageal reflux (GERD) or esophageal spasms creating burning sub-sternal retrosternal discomfort",
            "Cardiac ischemia, coronary insufficiency, or acute coronary syndrome (requires urgent emergency evaluation)",
            "Acute panic attack, hyperventilation, or situational cardiac anxiety"
        ],
        'home_care': [
            "Immediate Seated Rest: Stop all physical activity immediately; sit upright in a comfortable, supported chair",
            "Loosen Clothing: Unbutton tight collars, neckties, belts, and waistbands to facilitate unobstructed breathing",
            "Calm Breathing: Practice slow, deliberate diaphragmatic breathing to stabilize pulse and oxygenation"
        ],
        'precautions': [
            "Never ignore sudden, heavy, or persistent central chest discomfort",
            "Do not perform strenuous chores, lift heavy objects, or climb flights of stairs",
            "Do not consume heavy oily meals or lie down flat"
        ],
        'red_flags': [
            "🚨 Squeezing, crushing, heavy pressure, or fullness in the center or left side of the chest",
            "🚨 Discomfort radiating to the left shoulder, arm, neck, jaw, throat, or back",
            "🚨 Chest pain accompanied by cold sweats, shortness of breath, dizziness, or fainting",
            "🚨 IMMEDIATELY CALL EMERGENCY MEDICAL SERVICES (108 / 112 / 911) WITHOUT DELAY"
        ]
    },
    'dermatology_skin': {
        'name': 'Dermatology & Cutaneous Health (त्वचा व एलर्जी)',
        'keywords': [
            'rash', 'skin', 'itch', 'itching', 'allergy', 'hives', 'urticaria', 'swell',
            'swelling', 'acne', 'pimple', 'pimples', 'eczema', 'psoriasis', 'khujli', 'daane', 'sujan'
        ],
        'condition': 'Dermatological Irritation & Cutaneous Allergic Reaction (त्वचा पर चकत्ते व खुजली)',
        'overview': (
            "Cutaneous symptoms typically stem from epidermal barrier disruption, mast cell histamine release, or inflammatory dermatoses. "
            "Accurate self-care emphasizes calming surface inflammation and preventing secondary bacterial superinfections from excoriation."
        ),
        'causes': [
            "Contact dermatitis from harsh laundry detergents, synthetic cosmetics, dyes, or metallic jewelry",
            "Allergic urticaria (hives) triggered by insect bites, seasonal pollen, dietary allergens, or medications",
            "Superficial fungal dermatophytosis or localized bacterial folliculitis",
            "Barrier dehydration (xerosis) or flare of chronic atopic eczema / dermatitis"
        ],
        'home_care': [
            "Cool Compresses: Place clean, cold, damp cotton cloths over inflamed itchy patches for 10-15 minutes",
            "Soothing Lotions: Apply pure aloe vera gel or calamine lotion to soothe surface burning and pruritus",
            "Tepid Showers: Bathe with lukewarm water (never hot water) using mild, soap-free cleansing bars",
            "Skin Barrier Care: Gently pat skin dry and apply a fragrance-free hypoallergenic moisturizing cream"
        ],
        'precautions': [
            "Strictly avoid scratching, rubbing, or scrubbing irritated skin; keep fingernails trimmed short",
            "Avoid scented body sprays, deodorants, bleach-washed fabrics, and tight synthetic apparel",
            "Wear loose, soft, breathable 100% pure cotton garments"
        ],
        'red_flags': [
            "🚨 Rapidly spreading hives with facial swelling, lip or tongue edema, or difficulty breathing (Anaphylaxis)",
            "🚨 Widespread blistering, skin detachment, or raw painful ulcerated lesions",
            "🚨 Skin rash accompanied by high fever, confusion, or purple petechial bruising",
            "🚨 Severe local warmth, intense throbbing pain, and red streaks radiating from a wound (cellulitis)"
        ]
    },
    'musculoskeletal_joints': {
        'name': 'Musculoskeletal & Orthopedic Joints (जोड़ व मांसपेशियां)',
        'keywords': [
            'joint', 'joints', 'knee', 'hip', 'shoulder', 'elbow', 'wrist', 'ankle',
            'arthritis', 'back', 'backache', 'back pain', 'spine', 'neck', 'muscle',
            'muscles', 'bone', 'bones', 'gout', 'kamar dard', 'badan dard', 'jodon ka dard'
        ],
        'condition': 'Musculoskeletal Strain & Joint / Spinal Inflammation (मांसपेशियों व जोड़ों में दर्द)',
        'overview': (
            "Musculoskeletal complaints commonly involve ligamentous sprains, muscular myofascial trigger points, spinal misalignment, or synovial inflammation. "
            "Recovery is driven by restoring mechanical alignment, reducing localized swelling, and supporting tissue healing."
        ),
        'causes': [
            "Postural strain from prolonged sedentary desk work, poor lumbar support, or forward head posture",
            "Acute muscular sprain or ligamentous micro-tear following unconditioned exercise or awkward lifting",
            "Osteoarthritis (degenerative cartilage loss), inflammatory synovitis, or elevated uric acid (gout)",
            "Deficiency of essential bone and neuromuscular nutrients, specifically Vitamin D3 and calcium"
        ],
        'home_care': [
            "Thermal Application: Use an ice pack wrapped in a cloth for acute swollen sprains; use warm heating pads for chronic muscle tightness",
            "Ergonomic Posture: Maintain an upright spine with feet flat on the floor; take a 2-minute mobility break every 45 minutes",
            "Gentle Mobilization: Perform gentle non-weight-bearing range-of-motion movements (ankle pumps, gentle neck rotations)",
            "Anti-Inflammatory Nutrition: Consume warm turmeric milk, ginger tea, and calcium-rich foods (milk, almonds, sesame)"
        ],
        'precautions': [
            "Avoid lifting heavy weights, sudden spinal twisting, or strenuous athletic impact while in pain",
            "Avoid sitting on soft, sagging mattresses or slouching on couches without lower back support",
            "Wear supportive footwear with shock-absorbing soles rather than flat unpadded sandals"
        ],
        'red_flags': [
            "🚨 Complete inability to bear weight on the affected limb or joint locked in an abnormal position",
            "🚨 Marked redness, hot sensation, and severe acute swelling over a single joint with high fever",
            "🚨 Severe back pain accompanied by numbness/tingling down legs, groin numbness, or bladder/bowel incontinence",
            "🚨 Severe unremitting bone pain following a significant fall or traumatic impact"
        ]
    },
    'dizziness_weakness': {
        'name': 'Hemodynamics & Neurometabolic Vitality (चक्कर व कमज़ोरी)',
        'keywords': [
            'dizzy', 'dizziness', 'vertigo', 'lightheaded', 'faint', 'fainting', 'fatigue',
            'tired', 'weak', 'weakness', 'exhaustion', 'chakkar', 'kamzori', 'thakan'
        ],
        'condition': 'Hemodynamic & Vestibular Vitality Assessment (चक्कर आना व शारीरिक कमज़ोरी)',
        'overview': (
            "Dizziness, lightheadedness, and systemic weakness arise when cerebral perfusion, blood glucose delivery, or vestibular inner ear balance is compromised. "
            "Immediate self-care centers on stabilizing circulation and restoring cellular hydration."
        ),
        'causes': [
            "Orthostatic hypotension (a transient drop in blood pressure when rising rapidly from lying or seated posture)",
            "Systemic dehydration, reduced intravascular blood volume, or sodium/potassium electrolyte deficit",
            "Inner ear vestibular organ disturbance (such as benign paroxysmal positional vertigo / BPPV)",
            "Nutritional deficiencies (iron-deficiency anemia, vitamin B12 shortage) or transient hypoglycemia (low blood sugar)"
        ],
        'home_care': [
            "Immediate Recumbency: Sit down immediately or lie down flat with your legs elevated on pillows to restore cerebral blood flow",
            "Rapid Hydration: Drink a glass of water containing oral electrolytes (ORS or fresh lemon water with a pinch of salt and sugar)",
            "Gradual Movements: Change positions in stages: sit up on the edge of the bed for 30-60 seconds before standing up",
            "Steady Nutrition: Eat small, regular meals containing complex carbohydrates, fresh fruit, and iron-rich lentils"
        ],
        'precautions': [
            "Do not attempt to operate motor vehicles, machinery, or climb ladders/stairs while experiencing dizzy spells",
            "Avoid rapid head rotations, sudden bending over, or skipping meals",
            "Avoid hot, steamy showers or poorly ventilated crowded areas that induce vasodilation"
        ],
        'red_flags': [
            "🚨 Dizziness accompanied by central chest pain, irregular racing heartbeat, or severe breathlessness",
            "🚨 Complete loss of consciousness (syncope / fainting) or sudden mental confusion",
            "🚨 Neurological signs: slurred speech, facial asymmetry, or weakness/numbness in one arm or leg",
            "🚨 Sudden severe spinning vertigo accompanied by acute loss of hearing or intractable vomiting"
        ]
    }
}

# ==============================================================================
# 1. BioGPT Engine — Biomedical Knowledge, Medical Explanations & Disease Context
# ==============================================================================

def _match_clinical_profiles(clean_lower: str) -> list:
    matched = []
    for key, prof in CLINICAL_PROFILES.items():
        for kw in prof['keywords']:
            if re.search(r'\b' + re.escape(kw) + r'\b', clean_lower):
                matched.append(key)
                break
    return matched


def _lookup_csv_description(disease_name: str):
    """Looks up authentic disease summary from Symptom_Description.csv."""
    if df_desc.empty or not disease_name or 'disease' not in df_desc.columns:
        return None
    target = disease_name.strip().lower()
    exact = df_desc[df_desc['disease'].str.lower().str.strip() == target]
    if not exact.empty:
        val = str(exact['description'].values[0]).strip()
        if val and val.lower() != 'no summary available.':
            return val
    # Normalized alphanumeric match
    norm_target = re.sub(r'[^a-z0-9]+', ' ', target).strip()
    for _, row in df_desc.iterrows():
        d_norm = re.sub(r'[^a-z0-9]+', ' ', str(row['disease']).lower()).strip()
        if d_norm == norm_target or (len(norm_target) >= 5 and (norm_target in d_norm or d_norm in norm_target)):
            val = str(row['description']).strip()
            if val and val.lower() != 'no summary available.':
                return val
    return None


def _lookup_csv_precautions(disease_name: str) -> list:
    """Looks up authentic clinical precautions from Symptom_Precaution.csv."""
    if df_prec.empty or not disease_name or 'disease' not in df_prec.columns:
        return []
    target = disease_name.strip().lower()
    cols = [c for c in df_prec.columns if 'precaution' in c.lower()]
    exact = df_prec[df_prec['disease'].str.lower().str.strip() == target]
    if not exact.empty:
        found = [str(exact[c].values[0]).strip() for c in cols if pd.notna(exact[c].values[0]) and str(exact[c].values[0]).strip()]
        if found:
            return found
    norm_target = re.sub(r'[^a-z0-9]+', ' ', target).strip()
    for _, row in df_prec.iterrows():
        d_norm = re.sub(r'[^a-z0-9]+', ' ', str(row['disease']).lower()).strip()
        if d_norm == norm_target or (len(norm_target) >= 5 and (norm_target in d_norm or d_norm in norm_target)):
            found = [str(row[c]).strip() for c in cols if pd.notna(row[c]) and str(row[c]).strip()]
            if found:
                return found
    return []


def generate_biogpt_response(prompt: str, local_biogpt_text: str = None) -> dict:
    """
    BioGPT Responsibility:
    Biomedical knowledge, pathophysiology, medical explanations, disease information,
    and symptom-related clinical context. (Distinct from Gemini conversational guidance.)
    """
    if not prompt or not prompt.strip():
        return {
            "model": "BioGPT",
            "role": "Biomedical Knowledge & Medical Explanations",
            "source": "BioGPT Biomedical Knowledge Engine",
            "answer": "Please enter health symptoms or a medical condition for biomedical context and disease information."
        }

    clean = prompt.strip()
    if not is_health_related(clean):
        return {
            "model": "BioGPT",
            "role": "Biomedical Knowledge & Medical Explanations",
            "source": "Domain Guardrail",
            "answer": get_non_health_refusal_message()
        }

    clean_lower = clean.lower()
    matched_keys = _match_clinical_profiles(clean_lower)
    lrv1_feats = extract_lrv1_features(clean)
    topic_title = clean.rstrip('?!.').strip()[:60].title()

    # Pull biomedical disease context from Symptom_Description.csv if top LRv1 disease has a real description
    biomedical_disease_notes = []
    if lr_model is not None and lrv1_feats:
        try:
            vec = [1 if str(f) in lrv1_feats else 0 for f in symptom_features]
            probs = lr_model.predict_proba(pd.DataFrame([vec], columns=symptom_features))[0]
            top_indices = probs.argsort()[::-1][:3]
            for idx in top_indices:
                d_name = str(lr_model.classes_[idx])
                d_desc = _lookup_csv_description(d_name)
                if d_desc:
                    biomedical_disease_notes.append(f"**{d_name}:** {d_desc}")
        except Exception:
            pass

    if len(matched_keys) == 1:
        prof = CLINICAL_PROFILES[matched_keys[0]]
        organ_system = prof['name']
        condition_title = prof['condition']
        pathophysiology = prof['overview']
        etiology_list = prof['causes']
        clinical_context = (
            f"Biomedically, '{clean}' maps to the **{organ_system}** domain. "
            f"Clinical evaluation correlates symptom onset, systemic inflammatory markers, and organ-specific physiological response."
        )
    elif len(matched_keys) > 1:
        matched_profs = [CLINICAL_PROFILES[k] for k in matched_keys]
        organ_system = " + ".join([p['name'].split('(')[0].strip() for p in matched_profs])
        condition_title = f"Multi-System Clinical Presentation: {organ_system}"
        pathophysiology = (
            f"Concurrent manifestations across **{organ_system}** indicate multi-system physiological involvement. "
            "In clinical pathology, overlapping symptoms frequently arise from a shared systemic etiology (such as viral viremia, "
            "inflammatory cytokine release, autonomic dysregulation, or secondary mucosal involvement) affecting multiple organ tracts."
        )
        etiology_list = []
        for p in matched_profs:
            etiology_list.extend(p['causes'][:2])
        clinical_context = (
            "Multi-symptom presentations require distinguishing a single unifying diagnosis from concurrent independent conditions "
            "by correlating temporal progression, fever curves, and organ-specific clinical findings."
        )
    else:
        organ_system = "General Clinical & Systemic Medicine"
        condition_title = f"Biomedical Context: {topic_title}"
        pathophysiology = (
            f"Clinical inquiry regarding '{clean}' pertains to physiological homeostasis and host response mechanisms. "
            "Symptoms represent measurable manifestations of underlying tissue irritation, metabolic imbalance, or immune activation."
        )
        etiology_list = [
            "Infectious etiology (viral, bacterial, or parasitic host-pathogen interaction)",
            "Inflammatory, metabolic, or nutritional imbalance affecting target organ function",
            "Environmental, allergic, or physiological stress-induced homeostatic disturbance"
        ]
        clinical_context = (
            f"Documenting clinical characteristics of '{clean}' (anatomical distribution, onset pattern, and associated systemic signs) "
            "supports accurate biomedical differential evaluation."
        )

    etiology_md = "\n".join([f"- {c}" for c in etiology_list])
    disease_info_md = (
        "\n".join([f"- {note}" for note in biomedical_disease_notes])
        if biomedical_disease_notes
        else f"- Related clinical entity: **{condition_title}** — characterized by the pathophysiological mechanisms summarized above."
    )

    local_biogpt_section = ""
    source_label = "BioGPT Biomedical Knowledge Engine + Clinical Reference Corpus"
    if local_biogpt_text and local_biogpt_text.strip():
        local_biogpt_section = f"\n\n**Local Microsoft BioGPT Literature Context:**\n{local_biogpt_text.strip()}"
        source_label = "Microsoft BioGPT (Local Transformer) + Clinical Reference Corpus"

    answer = (
        f"**Condition / Clinical Assessment (Biomedical):** {condition_title}\n\n"
        f"**Organ System & Symptom-Related Context:**\n"
        f"- **Target System:** {organ_system}\n"
        f"- **Clinical Context:** {clinical_context}\n\n"
        f"**Pathophysiology & Medical Explanation:**\n"
        f"{pathophysiology}\n\n"
        f"**Disease Information (Reference Medical Knowledge):**\n"
        f"{disease_info_md}\n\n"
        f"**Biomedical Etiology & Underlying Mechanisms:**\n"
        f"{etiology_md}"
        f"{local_biogpt_section}\n\n"
        f"*(Biomedical Reference Notice: Provided for medical education and symptom context only — not a substitute for clinical diagnosis by a licensed physician.)*"
    )

    return {
        "model": "BioGPT",
        "role": "Biomedical Knowledge & Medical Explanations",
        "source": source_label,
        "organ_system": organ_system,
        "answer": answer
    }


# ==============================================================================
# 2. Gemini Engine — Natural-Language AI Health Assistant, Guidance & Follow-Ups
# ==============================================================================

FOLLOW_UP_BY_PROFILE = {
    'digestive': [
        "Did these digestive symptoms start after eating a specific meal, outside food, or taking any new medication?",
        "Are you experiencing burning pain before or after meals, bloating, or any change in stool color/frequency?",
        "How many days have these stomach/digestive symptoms persisted?"
    ],
    'throat_ent': [
        "Do you feel sharp pain while swallowing liquids or food, or is it mainly scratchiness and hoarseness?",
        "Have you noticed swollen glands in your neck, fever, or white patches on your tonsils?",
        "Are you also having a runny nose, cough, or acid reflux at night?"
    ],
    'respiratory_cough': [
        "Is your cough dry and tickly, or are you bringing up mucus/phlegm (and what color is it)?",
        "Do you experience wheezing, chest tightness, or shortness of breath during light activity or at night?",
        "How long has the cough or congestion lasted, and do you have a history of asthma or allergies?"
    ],
    'fever_infection': [
        "What is the highest temperature recorded on a thermometer, and how many days has the fever lasted?",
        "Does the fever come with chills, shivering, body aches, or skin rashes?",
        "Are you able to drink fluids normally and pass urine regularly?"
    ],
    'vomiting_diarrhea': [
        "How many episodes of vomiting or loose stools have occurred in the last 24 hours?",
        "Are you able to keep small sips of water or ORS down without vomiting?",
        "Have you noticed fever, severe abdominal cramps, or any blood in vomit or stool?"
    ],
    'headache_migraine': [
        "Where is the headache located (forehead, temples, one side, or back of the head) and does it throb or feel tight?",
        "Are you sensitive to bright light, loud sounds, or experiencing nausea or visual changes?",
        "Have you had poor sleep, skipped meals, heavy screen exposure, or dehydration today?"
    ],
    'cardiovascular_chest': [
        "Does the chest discomfort feel heavy/squeezing, sharp when breathing, or burning after eating?",
        "Does the pain spread to your left arm, shoulder, neck, jaw, or back?",
        "Are you also having sweating, dizziness, or shortness of breath right now? (If yes, seek emergency care immediately.)"
    ],
    'dermatology_skin': [
        "Where on your body did the rash or itching start, and is it spreading or forming blisters?",
        "Have you recently tried a new soap, detergent, cosmetic, food, or medication?",
        "Is the skin area hot to the touch, oozing, or accompanied by fever or facial swelling?"
    ],
    'musculoskeletal_joints': [
        "Did the pain start after lifting, exercise, a fall, or prolonged sitting/desk work?",
        "Is the affected joint visibly swollen, warm, red, or stiff in the morning?",
        "Do you feel any numbness, tingling, or radiating pain down your arms or legs?"
    ],
    'dizziness_weakness': [
        "Does the dizziness feel like the room is spinning (vertigo) or like you might faint when standing up?",
        "Have you had enough water and regular meals today, or have you had a recent illness?",
        "Are you experiencing palpitations, blurred vision, or numbness on one side of your body?"
    ]
}


def generate_gemini_guidance(prompt: str) -> dict:
    """
    Gemini Responsibility (Fallback / Offline Health Assistant):
    Natural-language health assistant providing plain-language symptom understanding,
    practical everyday health guidance, general precautions, and targeted follow-up questions.
    (Distinct from BioGPT biomedical pathophysiology!)
    """
    if not prompt or not prompt.strip():
        return {
            "model": "Gemini",
            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
            "source": "Gemini Health Assistant Engine",
            "follow_up_questions": [],
            "answer": "Please describe what symptoms you are feeling in your own words so I can offer helpful health guidance and precautions."
        }

    clean = prompt.strip()
    if not is_health_related(clean):
        return {
            "model": "Gemini",
            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
            "source": "Domain Guardrail",
            "follow_up_questions": [],
            "answer": get_non_health_refusal_message()
        }

    clean_lower = clean.lower()
    matched_keys = _match_clinical_profiles(clean_lower)

    if len(matched_keys) == 1:
        prof = CLINICAL_PROFILES[matched_keys[0]]
        plain_summary = (
            f"It sounds like you are dealing with **{clean}**, which commonly relates to **{prof['name'].split('(')[0].strip()}**. "
            "Focusing on gentle symptom relief, hydration, and watching for warning signs is a safe first step while deciding whether to consult a doctor."
        )
        guidance_items = prof['home_care']
        precaution_items = prof['precautions']
        red_flags = prof['red_flags'][:3]
        follow_ups = FOLLOW_UP_BY_PROFILE.get(matched_keys[0], [])
    elif len(matched_keys) > 1:
        matched_profs = [CLINICAL_PROFILES[k] for k in matched_keys]
        areas = ", ".join([p['name'].split('(')[0].strip() for p in matched_profs])
        plain_summary = (
            f"You mentioned multiple symptoms together (**{clean}**), involving **{areas}**. "
            "When symptoms appear at the same time, taking extra rest, staying hydrated, and tracking which symptom started first helps a doctor pinpoint the exact cause quickly."
        )
        guidance_items, precaution_items, red_flags, follow_ups = [], [], [], []
        for k in matched_keys:
            p = CLINICAL_PROFILES[k]
            guidance_items.extend(p['home_care'][:2])
            precaution_items.extend(p['precautions'][:2])
            red_flags.extend(p['red_flags'][:1])
            follow_ups.extend(FOLLOW_UP_BY_PROFILE.get(k, [])[:2])
        follow_ups = follow_ups[:4]
    else:
        plain_summary = (
            f"Thank you for sharing what you are experiencing (**{clean}**). "
            "Because symptoms can have several everyday or medical triggers, gentle supportive care and noting how your symptoms change over the next 24–48 hours is very helpful."
        )
        guidance_items = [
            "Stay well-hydrated throughout the day with clean water, oral electrolytes, or warm herbal drinks",
            "Eat light, freshly prepared, easily digestible meals and avoid skipping meals",
            "Prioritize 7–8 hours of restful sleep and pause strenuous physical exertion until you feel better"
        ]
        precaution_items = [
            "Avoid self-medicating with antibiotics or repeated painkillers without medical advice",
            "Keep a brief symptom note (start time, triggers, severity from 1–10) to share with a doctor",
            "Book a consultation with a healthcare provider if symptoms persist beyond 2–3 days or worsen"
        ]
        red_flags = [
            "🚨 Persistent high fever (>102°F / 38.9°C) or sudden severe pain",
            "🚨 Trouble breathing, chest tightness, fainting, or sudden confusion",
            "🚨 Inability to keep fluids down or rapid worsening of your condition"
        ]
        follow_ups = [
            "When did these symptoms first begin, and are they constant or coming and going?",
            "On a scale of 1 to 10, how mild or severe is your discomfort right now?",
            "Are you experiencing any accompanying symptoms such as fever, fatigue, nausea, or pain elsewhere?",
            "Do you have any existing medical conditions or daily medications a doctor should know about?"
        ]

    guidance_md = "\n".join([f"- {g}" for g in guidance_items])
    precautions_md = "\n".join([f"- {p}" for p in precaution_items])
    red_flags_md = "\n".join([f"- {r}" for r in red_flags])
    followups_md = "\n".join([f"- {q}" for q in follow_ups])

    answer = (
        f"**Understanding Your Symptoms (Health Assistant Guidance):**\n"
        f"{plain_summary}\n\n"
        f"**Practical Self-Care & Everyday Health Guidance:**\n"
        f"{guidance_md}\n\n"
        f"**General Precautions:**\n"
        f"{precautions_md}\n\n"
        f"**When to Seek Prompt Medical Care:**\n"
        f"{red_flags_md}\n\n"
        f"**Helpful Follow-Up Questions to Clarify Your Symptoms:**\n"
        f"{followups_md}\n\n"
        f"*(Health Assistant Note: General guidance only — please consult a qualified doctor for personal diagnosis or treatment.)*"
    )

    return {
        "model": "Gemini",
        "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
        "source": "Gemini Health Assistant Engine (Structured Fallback)",
        "follow_up_questions": follow_ups,
        "answer": answer
    }


def generate_clinical_response(prompt: str) -> str:
    """Backwards-compatible helper returning BioGPT biomedical explanation text."""
    return generate_biogpt_response(prompt)["answer"]


# ==============================================================================
# 3 & 4. Independent ML Disease Prediction Engines:
#   - LRv1: LogisticRegression (logistic_regression_model.pkl, 489 features, 261 classes)
#   - LRv2: RandomForestClassifier (disease_prediction_model.pkl + symptom_mlb.pkl, 131 features, 41 classes)
#   ZERO fabricated probabilities — strictly real predict_proba() inference!
# ==============================================================================

# Verified natural-language / Hindi-Hinglish synonym maps to each model's REAL feature vocabulary
LRV1_SYNONYMS = {
    'fever': 'fever', 'fevr': 'fever', 'feaver': 'fever', 'high fever': 'fever', 'mild fever': 'fever', 'bukhar': 'fever', 'bukhaar': 'fever',
    'headache': 'headache', 'headche': 'headache', 'hedache': 'headache', 'heache': 'headache', 'sir dard': 'headache', 'sar dard': 'headache', 'migraine': 'headache',
    'cough': 'coughing', 'caugh': 'coughing', 'khansi': 'coughing', 'dry cough': 'dry cough', 'chronic cough': 'chronic cough',
    'sore throat': 'sore throat', 'throat pain': 'sore throat', 'gale me dard': 'sore throat', 'gale me kharash': 'sore throat', 'throat irritation': 'sore throat',
    'stomach pain': 'stomach pain', 'stomach ache': 'stomach pain', 'stomachache': 'stomach pain', 'pet dard': 'stomach pain', 'abdominal pain': 'lower abdominal pain',
    'vomiting': 'vomiting', 'vomit': 'vomiting', 'vomitting': 'vomiting', 'ulti': 'vomiting',
    'nausea': 'nausea', 'queasy': 'nausea',
    'diarrhea': 'diarrhea', 'diarrhoea': 'diarrhoea', 'diarhea': 'diarrhea', 'loose motion': 'diarrhea', 'loose motions': 'diarrhea', 'dast': 'diarrhea',
    'chest pain': 'chest pain', 'chhati dard': 'chest pain', 'seene me dard': 'chest pain', 'chest tightness': 'chest tightness',
    'shortness of breath': 'difficulty breathing', 'breathlessness': 'difficulty breathing', 'breathless': 'difficulty breathing', 'saans fulna': 'difficulty breathing',
    'dizziness': 'dizziness', 'dizzy': 'dizziness', 'vertigo': 'dizziness', 'chakkar': 'dizziness',
    'fatigue': 'fatigue', 'tired': 'fatigue', 'tiredness': 'fatigue', 'kamzori': 'muscle weakness', 'weakness': 'muscle weakness',
    'skin rash': 'red rash', 'rash': 'red rash', 'rashes': 'red rash', 'daane': 'red rash',
    'itching': 'itching', 'itchy': 'itching', 'itch': 'itching', 'khujli': 'itching',
    'sneeze': 'sneezing', 'sneezing': 'sneezing',
    'cold': 'feeling cold', 'chills': 'feeling cold', 'shivering': 'feeling cold',
    'constipation': 'constipation', 'constipated': 'constipation',
    'acidity': 'taste acid', 'acid reflux': 'taste acid', 'heartburn': 'taste acid',
    'joint pain': 'muscle joint pain', 'body pain': 'muscle joint pain', 'muscle pain': 'muscle joint pain', 'jodon ka dard': 'muscle joint pain', 'badan dard': 'muscle joint pain',
    'back pain': 'severe pain lower back abdomen', 'backache': 'severe pain lower back abdomen', 'kamar dard': 'severe pain lower back abdomen',
    'neck pain': 'neck stiffness', 'stiff neck': 'stiff neck',
    'weight loss': 'unexplained weight loss', 'weight lose': 'unexplained weight loss', 'weight gain': 'weight gain',
    'anxiety': 'anxiety', 'acne': 'acne', 'pimples': 'acne', 'pimple': 'acne',
    'digestive': 'abdominal cramp', 'indigestion': 'abdominal cramp', 'bloating': 'abdominal distention'
}

LRV2_SYNONYMS = {
    'high fever': 'high_fever', 'severe fever': 'high_fever', 'fever': 'high_fever', 'fevr': 'high_fever', 'feaver': 'high_fever', 'bukhar': 'high_fever', 'bukhaar': 'high_fever',
    'mild fever': 'mild_fever', 'low fever': 'mild_fever',
    'headache': 'headache', 'headche': 'headache', 'hedache': 'headache', 'heache': 'headache', 'sir dard': 'headache', 'sar dard': 'headache', 'migraine': 'headache',
    'cough': 'cough', 'coughing': 'cough', 'caugh': 'cough', 'khansi': 'cough',
    'sore throat': 'throat_irritation', 'throat pain': 'throat_irritation', 'throat irritation': 'throat_irritation', 'gale me dard': 'throat_irritation', 'gale me kharash': 'throat_irritation',
    'stomach pain': 'stomach_pain', 'stomach ache': 'stomach_pain', 'stomachache': 'stomach_pain', 'pet dard': 'stomach_pain',
    'abdominal pain': 'abdominal_pain', 'belly pain': 'belly_pain',
    'vomiting': 'vomiting', 'vomit': 'vomiting', 'vomitting': 'vomiting', 'ulti': 'vomiting',
    'nausea': 'nausea', 'queasy': 'nausea',
    'diarrhea': 'diarrhoea', 'diarrhoea': 'diarrhoea', 'diarhea': 'diarrhoea', 'loose motion': 'diarrhoea', 'loose motions': 'diarrhoea', 'dast': 'diarrhoea',
    'chest pain': 'chest_pain', 'chhati dard': 'chest_pain', 'seene me dard': 'chest_pain',
    'shortness of breath': 'breathlessness', 'difficulty breathing': 'breathlessness', 'breathlessness': 'breathlessness', 'breathless': 'breathlessness', 'saans fulna': 'breathlessness',
    'dizziness': 'dizziness', 'dizzy': 'dizziness', 'vertigo': 'spinning_movements', 'chakkar': 'dizziness',
    'fatigue': 'fatigue', 'tired': 'fatigue', 'tiredness': 'fatigue', 'weakness': 'muscle_weakness', 'kamzori': 'fatigue', 'lethargy': 'lethargy',
    'skin rash': 'skin_rash', 'rash': 'skin_rash', 'rashes': 'skin_rash', 'daane': 'skin_rash',
    'itching': 'itching', 'itchy': 'itching', 'itch': 'itching', 'khujli': 'itching',
    'sneeze': 'continuous_sneezing', 'sneezing': 'continuous_sneezing',
    'cold': 'runny_nose', 'runny nose': 'runny_nose', 'congestion': 'congestion', 'sardi': 'runny_nose', 'jukam': 'runny_nose',
    'chills': 'chills', 'shivering': 'shivering', 'sweating': 'sweating',
    'constipation': 'constipation', 'constipated': 'constipation',
    'acidity': 'acidity', 'acid reflux': 'acidity', 'heartburn': 'acidity',
    'indigestion': 'indigestion', 'digestive': 'indigestion', 'digestion': 'indigestion', 'gas': 'passage_of_gases', 'bloating': 'distention_of_abdomen',
    'joint pain': 'joint_pain', 'knee pain': 'knee_pain', 'hip pain': 'hip_joint_pain', 'jodon ka dard': 'joint_pain',
    'muscle pain': 'muscle_pain', 'body pain': 'muscle_pain', 'badan dard': 'muscle_pain',
    'back pain': 'back_pain', 'backache': 'back_pain', 'kamar dard': 'back_pain',
    'neck pain': 'neck_pain', 'stiff neck': 'stiff_neck',
    'weight loss': 'weight_loss', 'weight lose': 'weight_loss', 'weight gain': 'weight_gain',
    'loss of appetite': 'loss_of_appetite', 'dehydration': 'dehydration',
    'anxiety': 'anxiety', 'depression': 'depression',
    'blurred vision': 'blurred_and_distorted_vision', 'blurry vision': 'blurred_and_distorted_vision',
    'red eye': 'redness_of_eyes', 'red eyes': 'redness_of_eyes', 'watery eyes': 'watering_from_eyes',
    'pimples': 'pus_filled_pimples', 'pimple': 'pus_filled_pimples', 'acne': 'pus_filled_pimples',
    'phlegm': 'phlegm', 'palpitations': 'palpitations', 'dark urine': 'dark_urine', 'yellow eyes': 'yellowing_of_eyes', 'jaundice': 'yellowish_skin'
}


def extract_lrv1_features(text: str) -> list:
    """Maps input symptoms to LRv1's actual 489-feature vocabulary (word-boundary + verified synonyms)."""
    if not text or not symptom_features:
        return []
    clean = text.lower()
    feat_set = set(str(f) for f in symptom_features)
    matched = []
    seen = set()

    # 1. Exact word-boundary matches against LRv1's 489 features
    for f in symptom_features:
        f_str = str(f)
        f_clean = f_str.lower().replace('_', ' ').strip()
        if len(f_clean) >= 3 and re.search(r'\b' + re.escape(f_clean) + r'\b', clean):
            if f_str not in seen:
                seen.add(f_str)
                matched.append(f_str)

    # 2. Verified clinical synonym matches (only if target exists in LRv1's real features)
    for phrase, target_feat in LRV1_SYNONYMS.items():
        if target_feat in feat_set and target_feat not in seen:
            if re.search(r'\b' + re.escape(phrase) + r'\b', clean):
                seen.add(target_feat)
                matched.append(target_feat)

    return matched


def extract_lrv2_features(text: str) -> list:
    """Independently maps input symptoms to LRv2's actual 131 MultiLabelBinarizer features."""
    if not text or symptom_mlb is None:
        return []
    clean = text.lower()
    mlb_classes = list(symptom_mlb.classes_)
    mlb_set = set(str(c) for c in mlb_classes)
    matched = []
    seen = set()

    # 1. Exact word-boundary matches against LRv2's 131 MLB features
    for c in mlb_classes:
        c_str = str(c)
        c_clean = c_str.lower().replace('_', ' ').strip()
        if len(c_clean) >= 3 and re.search(r'\b' + re.escape(c_clean) + r'\b', clean):
            if c_str not in seen:
                seen.add(c_str)
                matched.append(c_str)

    # 2. Verified clinical synonym matches (only if target exists in LRv2's real MLB classes)
    for phrase, target_feat in LRV2_SYNONYMS.items():
        if target_feat in mlb_set and target_feat not in seen:
            if re.search(r'\b' + re.escape(phrase) + r'\b', clean):
                # Avoid matching both high_fever and mild_fever when user specifically said "mild fever"
                if target_feat == 'high_fever' and 'mild_fever' in seen:
                    continue
                seen.add(target_feat)
                matched.append(target_feat)

    return matched


def extract_symptoms_from_text(text: str) -> list:
    """Backwards-compatible alias returning LRv1 matched features."""
    return extract_lrv1_features(text)[:10]


# Display mapping dictionary for backwards compatibility
SYMPTOM_DISPLAY = {
    'headache': 'Headache (सिर दर्द)',
    'fever': 'Fever (बुखार)',
    'cough': 'Cough (खांसी)',
    'vomiting': 'Vomiting (उल्टी)',
    'diarrhea': 'Diarrhea (दस्त)',
    'fatigue': 'Fatigue / Weakness (कमज़ोरी)',
    'chest_pain': 'Chest Pain (सीने में दर्द)',
    'shortness_of_breath': 'Shortness of Breath (सांस फूलना)',
    'stomach_pain': 'Stomach Pain (पेट दर्द)'
}


def _format_disease_label(raw_name: str) -> str:
    """Formats lowercase CSV/model disease labels cleanly while preserving acronyms."""
    s = re.sub(r'\s+', ' ', str(raw_name or '')).strip()
    if not s:
        return s
    if s.islower():
        acronyms = {'aids': 'AIDS', 'gerd': 'GERD', 'uti': 'UTI', 'tb': 'TB'}
        words = []
        for w in s.split(' '):
            clean_w = w.strip('()')
            if clean_w in acronyms:
                words.append(w.replace(clean_w, acronyms[clean_w]))
            else:
                words.append(w.capitalize())
        return ' '.join(words)
    return s


def get_lrv1_prediction(query_text: str) -> dict:
    """
    LRv1 — Independent Logistic Regression Classifier (logistic_regression_model.pkl).
    Uses actual lr_model.predict_proba() over 261 disease classes and 489 features.
    NEVER fabricates probabilities.
    """
    if not query_text or not query_text.strip():
        return {
            'model': 'LRv1',
            'algorithm': 'Logistic Regression (489 features, 261 classes)',
            'inference_status': 'input_required',
            'predicted_disease': 'Input Required',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Please enter health symptoms to run LRv1 disease prediction.'
        }

    clean = query_text.strip()
    if not is_health_related(clean):
        return {
            'model': 'LRv1',
            'algorithm': 'Logistic Regression (489 features, 261 classes)',
            'inference_status': 'non_health',
            'predicted_disease': 'Non-Health Query',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Niramaya AI only processes medical and health symptoms. Please enter specific health symptoms to predict conditions.'
        }

    matched_features = extract_lrv1_features(clean)

    if lr_model is None or not symptom_features:
        return {
            'model': 'LRv1',
            'algorithm': 'Logistic Regression',
            'inference_status': 'model_unavailable',
            'predicted_disease': 'Model Unavailable',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': matched_features,
            'description': 'LRv1 trained model artifact (logistic_regression_model.pkl) could not be loaded.'
        }

    if not matched_features:
        return {
            'model': 'LRv1',
            'algorithm': f'Logistic Regression ({len(symptom_features)} features, {len(lr_model.classes_)} classes)',
            'inference_status': 'insufficient_features',
            'predicted_disease': 'Insufficient Matched Symptom Features',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': (
                f"No exact symptoms from '{clean}' matched LRv1's 489-feature vocabulary. "
                "Try listing specific clinical symptoms (e.g., fever, headache, coughing, vomiting, stomach pain, itching, red rash, dizziness)."
            )
        }

    matched_set = set(matched_features)
    vec = [1 if str(f) in matched_set else 0 for f in symptom_features]
    X_df = pd.DataFrame([vec], columns=symptom_features)
    probs = lr_model.predict_proba(X_df)[0]

    # Top 5 real probability predictions directly from predict_proba()
    top_idx = probs.argsort()[::-1][:5]
    top_predictions = [
        {
            'disease': _format_disease_label(lr_model.classes_[i]),
            'raw_class': str(lr_model.classes_[i]),
            'probability': round(float(probs[i]) * 100.0, 2)
        }
        for i in top_idx
    ]

    pred_disease = top_predictions[0]['disease']
    top_prob = top_predictions[0]['probability']
    top5_sum = round(sum(item['probability'] for item in top_predictions), 2)

    desc = _lookup_csv_description(top_predictions[0]['raw_class']) or (
        f"LRv1 (Logistic Regression) predicted '{pred_disease}' with {top_prob:.2f}% probability "
        f"based on {len(matched_features)} matched symptom feature(s)."
    )

    return {
        'model': 'LRv1',
        'algorithm': f'Logistic Regression ({len(symptom_features)} features, {len(lr_model.classes_)} classes)',
        'inference_status': 'success',
        'predicted_disease': pred_disease,
        'top_probability': top_prob,
        'top5_cumulative_probability': top5_sum,
        'top_predictions': top_predictions,
        'matched_symptoms': matched_features,
        'total_features': len(symptom_features),
        'total_classes': len(lr_model.classes_),
        'description': desc
    }


def get_lrv2_prediction(query_text: str) -> dict:
    """
    LRv2 — Independent Enhanced Random Forest Classifier (disease_prediction_model.pkl + symptom_mlb.pkl).
    Uses actual rf_model.predict_proba() over 41 disease classes and 131 MLB features,
    completely independent of LRv1! NEVER fabricates probabilities.
    """
    if not query_text or not query_text.strip():
        return {
            'model': 'LRv2',
            'algorithm': 'Random Forest Classifier (131 MLB features, 41 classes)',
            'inference_status': 'input_required',
            'predicted_disease': 'Input Required',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Please enter health symptoms to run LRv2 enhanced disease prediction.',
            'precautions': ['Enter symptom names like fever, headache, cough, vomiting, stomach pain']
        }

    clean = query_text.strip()
    if not is_health_related(clean):
        return {
            'model': 'LRv2',
            'algorithm': 'Random Forest Classifier (131 MLB features, 41 classes)',
            'inference_status': 'non_health',
            'predicted_disease': 'Non-Health Query',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Niramaya AI only processes medical and health symptoms. Please enter specific health symptoms to predict conditions.',
            'precautions': ['Please ask questions related to health symptoms, medical conditions, and care.']
        }

    matched_v2 = extract_lrv2_features(clean)

    if rf_model is None or symptom_mlb is None:
        return {
            'model': 'LRv2',
            'algorithm': 'Random Forest Classifier',
            'inference_status': 'model_unavailable',
            'predicted_disease': 'Model Unavailable',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': matched_v2,
            'description': 'LRv2 trained model artifact (disease_prediction_model.pkl) could not be loaded.',
            'precautions': ['Consult a certified physician for clinical evaluation.']
        }

    if not matched_v2:
        return {
            'model': 'LRv2',
            'algorithm': f'Random Forest Classifier ({len(symptom_mlb.classes_)} MLB features, {len(rf_model.classes_)} classes)',
            'inference_status': 'insufficient_features',
            'predicted_disease': 'Insufficient Matched Symptom Features',
            'top_probability': 0.0,
            'top5_cumulative_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': (
                f"No exact symptoms from '{clean}' matched LRv2's 131-feature vocabulary. "
                "Try entering specific symptoms (e.g., high fever, headache, cough, vomiting, stomach pain, skin rash, itching, acidity)."
            ),
            'precautions': [
                'Enter specific physical symptoms for ML probability prediction',
                'Stay hydrated, rest, and consult a healthcare professional if symptoms persist'
            ]
        }

    X_mlb = symptom_mlb.transform([matched_v2])
    probs = rf_model.predict_proba(X_mlb)[0]

    # Top 5 real probability predictions directly from RandomForest predict_proba()
    top_idx = probs.argsort()[::-1][:5]
    top_predictions = [
        {
            'disease': _format_disease_label(rf_model.classes_[i]),
            'raw_class': str(rf_model.classes_[i]),
            'probability': round(float(probs[i]) * 100.0, 2)
        }
        for i in top_idx
        if float(probs[i]) > 0.0
    ]

    pred_disease = top_predictions[0]['disease']
    top_prob = top_predictions[0]['probability']
    top5_sum = round(sum(item['probability'] for item in top_predictions), 2)

    desc = _lookup_csv_description(top_predictions[0]['raw_class']) or (
        f"LRv2 (Random Forest Classifier) independently predicted '{pred_disease}' with {top_prob:.2f}% probability "
        f"based on {len(matched_v2)} matched symptom feature(s)."
    )

    precautions = _lookup_csv_precautions(top_predictions[0]['raw_class'])
    if not precautions:
        # Fallback precautions from matching clinical profile if disease is not in Symptom_Precaution.csv
        prof_keys = _match_clinical_profiles(clean.lower())
        if prof_keys:
            precautions = list(CLINICAL_PROFILES[prof_keys[0]]['precautions'])
        else:
            precautions = [
                "Maintain adequate physical rest and stay well-hydrated throughout the day",
                "Monitor symptoms closely and track their severity and progression",
                "Avoid unprescribed self-medication and consult a licensed physician"
            ]

    pretty_matched = [m.replace('_', ' ') for m in matched_v2]

    return {
        'model': 'LRv2',
        'algorithm': f'Random Forest Classifier ({len(symptom_mlb.classes_)} MLB features, {len(rf_model.classes_)} classes)',
        'inference_status': 'success',
        'predicted_disease': pred_disease,
        'top_probability': top_prob,
        'top5_cumulative_probability': top5_sum,
        'top_predictions': top_predictions,
        'matched_symptoms': pretty_matched,
        'raw_matched_features': matched_v2,
        'total_features': len(symptom_mlb.classes_),
        'total_classes': len(rf_model.classes_),
        'description': desc,
        'precautions': precautions
    }


# ==============================================================================
# 5. Authentic LRv1 vs LRv2 Comparison Engine
# ==============================================================================

_DISEASE_CANONICAL_ALIASES = {
    'acquired immuno deficiency syndrome': 'aids',
    'chicken pox': 'chickenpox',
    'gastroesophageal reflux disease': 'gerd',
    'bronchial asthma': 'asthma',
    'common cold': 'common cold',
    'urinary tract infection': 'urinary tract infection',
    'peptic ulcer diseae': 'peptic ulcer disease',
    'dimorphic hemmorhoids(piles)': 'hemorrhoids',
    'piles': 'hemorrhoids',
    'osteocystitis': 'osteoarthritis',
    'paralysis (brain hemorrhage)': 'brain hemorrhage',
    '(vertigo) paroymsal  positional vertigo': 'vertigo',
}


def _canonical_disease(name: str) -> str:
    n = re.sub(r'\s+', ' ', str(name or '').lower()).strip()
    return _DISEASE_CANONICAL_ALIASES.get(n, n)


def compare_lrv1_and_lrv2(lrv1_res: dict, lrv2_res: dict) -> dict:
    """
    Compares actual independent outputs of LRv1 (Logistic Regression) and LRv2 (Random Forest):
    top predictions, probability distributions, overlapping diseases, and agreement/disagreement.
    Strictly derived from real model outputs — ZERO fabricated metrics.
    """
    v1_ok = lrv1_res.get('inference_status') == 'success' and bool(lrv1_res.get('top_predictions'))
    v2_ok = lrv2_res.get('inference_status') == 'success' and bool(lrv2_res.get('top_predictions'))

    v1_top = lrv1_res.get('predicted_disease', 'N/A')
    v2_top = lrv2_res.get('predicted_disease', 'N/A')
    v1_prob = float(lrv1_res.get('top_probability') or 0.0)
    v2_prob = float(lrv2_res.get('top_probability') or 0.0)
    v1_top5_sum = float(lrv1_res.get('top5_cumulative_probability') or 0.0)
    v2_top5_sum = float(lrv2_res.get('top5_cumulative_probability') or 0.0)

    if not v1_ok or not v2_ok:
        missing = []
        if not v1_ok:
            missing.append('LRv1')
        if not v2_ok:
            missing.append('LRv2')
        return {
            'agreement_status': 'Insufficient Features for Comparison',
            'agreement_code': 'insufficient',
            'top1_match': False,
            'lrv1_summary': {
                'algorithm': lrv1_res.get('algorithm', 'Logistic Regression'),
                'predicted_disease': v1_top,
                'top_probability': v1_prob,
                'top5_cumulative_probability': v1_top5_sum,
                'matched_feature_count': len(lrv1_res.get('matched_symptoms') or []),
                'total_classes': lrv1_res.get('total_classes', len(lr_model.classes_) if lr_model is not None else 0)
            },
            'lrv2_summary': {
                'algorithm': lrv2_res.get('algorithm', 'Random Forest Classifier'),
                'predicted_disease': v2_top,
                'top_probability': v2_prob,
                'top5_cumulative_probability': v2_top5_sum,
                'matched_feature_count': len(lrv2_res.get('matched_symptoms') or []),
                'total_classes': lrv2_res.get('total_classes', len(rf_model.classes_) if rf_model is not None else 0)
            },
            'overlapping_diseases': [],
            'probability_gap': round(abs(v2_prob - v1_prob), 2),
            'comparison_notes': (
                f"Direct comparison could not be completed because {', '.join(missing)} did not match enough symptom "
                "features from the input text. Enter more specific clinical symptoms to compare both ML classifiers."
            )
        }

    v1_canon_top = _canonical_disease(v1_top)
    v2_canon_top = _canonical_disease(v2_top)
    top1_match = (v1_canon_top == v2_canon_top) or (v1_canon_top in v2_canon_top) or (v2_canon_top in v1_canon_top)

    # Check overlapping diseases across both Top-5 lists
    v1_map = {_canonical_disease(p['disease']): p for p in lrv1_res.get('top_predictions', [])}
    v2_map = {_canonical_disease(p['disease']): p for p in lrv2_res.get('top_predictions', [])}

    overlapping = []
    for k1, p1 in v1_map.items():
        for k2, p2 in v2_map.items():
            if k1 == k2 or (len(k1) >= 5 and len(k2) >= 5 and (k1 in k2 or k2 in k1)):
                overlapping.append({
                    'disease': p1['disease'] if len(p1['disease']) >= len(p2['disease']) else p2['disease'],
                    'lrv1_probability': p1['probability'],
                    'lrv2_probability': p2['probability']
                })
                break

    if top1_match:
        agreement_status = 'Full Agreement'
        agreement_code = 'agree'
        agreement_summary = (
            f"Both models independently converged on the same top prediction ({v1_top} / {v2_top}). "
            f"LRv1 assigned {v1_prob:.2f}% (across {lrv1_res.get('total_classes', 261)} disease classes), "
            f"while LRv2 assigned {v2_prob:.2f}% (across {lrv2_res.get('total_classes', 41)} disease classes)."
        )
    elif overlapping:
        agreement_status = 'Partial Agreement'
        agreement_code = 'partial'
        overlap_names = ', '.join([o['disease'] for o in overlapping])
        agreement_summary = (
            f"LRv1's top prediction is {v1_top} ({v1_prob:.2f}%) whereas LRv2's top prediction is {v2_top} ({v2_prob:.2f}%), "
            f"but both models share overlapping candidate(s) in their Top-5 lists: {overlap_names}."
        )
    else:
        agreement_status = 'Disagreement'
        agreement_code = 'disagree'
        agreement_summary = (
            f"LRv1 predicted {v1_top} ({v1_prob:.2f}% across {lrv1_res.get('total_classes', 261)} classes) "
            f"while LRv2 predicted {v2_top} ({v2_prob:.2f}% across {lrv2_res.get('total_classes', 41)} classes) with no Top-5 overlap. "
            "Disagreement occurs because the two models use different algorithms (linear Logistic Regression vs non-linear Random Forest), "
            "different feature vocabularies (489 vs 131 symptoms), and different target disease sets (261 vs 41 diseases)."
        )

    prob_gap = round(abs(v2_prob - v1_prob), 2)
    dist_note = (
        f"Probability Concentration: LRv1's Top-5 classes account for {v1_top5_sum:.2f}% of total probability mass "
        f"(spread across {lrv1_res.get('total_classes', 261)} classes), whereas LRv2's Top-5 classes account for "
        f"{v2_top5_sum:.2f}% (concentrated across {lrv2_res.get('total_classes', 41)} classes). "
        "Lower raw percentages in LRv1 are mathematically expected from softmax over 261 classes vs 41 classes."
    )

    return {
        'agreement_status': agreement_status,
        'agreement_code': agreement_code,
        'top1_match': top1_match,
        'lrv1_summary': {
            'algorithm': lrv1_res.get('algorithm'),
            'predicted_disease': v1_top,
            'top_probability': v1_prob,
            'top5_cumulative_probability': v1_top5_sum,
            'matched_feature_count': len(lrv1_res.get('matched_symptoms') or []),
            'total_classes': lrv1_res.get('total_classes', 261)
        },
        'lrv2_summary': {
            'algorithm': lrv2_res.get('algorithm'),
            'predicted_disease': v2_top,
            'top_probability': v2_prob,
            'top5_cumulative_probability': v2_top5_sum,
            'matched_feature_count': len(lrv2_res.get('matched_symptoms') or []),
            'total_classes': lrv2_res.get('total_classes', 41)
        },
        'overlapping_diseases': overlapping,
        'probability_gap': prob_gap,
        'comparison_notes': f"{agreement_summary} {dist_note}"
    }

