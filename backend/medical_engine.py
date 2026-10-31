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
MODEL_PATH = os.path.join(MODEL_DIR, 'logistic_regression_model.pkl')
FEATURES_PATH = os.path.join(MODEL_DIR, 'symptom_features.pkl')
DESC_PATH = os.path.join(MODEL_DIR, 'Symptom_Description.csv')
PREC_PATH = os.path.join(MODEL_DIR, 'Symptom_Precaution.csv')

lr_model = None
symptom_features = []
df_desc = pd.DataFrame()
df_prec = pd.DataFrame()

try:
    if os.path.exists(MODEL_PATH):
        lr_model = joblib.load(MODEL_PATH)
    if os.path.exists(FEATURES_PATH):
        symptom_features = joblib.load(FEATURES_PATH)
    if os.path.exists(DESC_PATH):
        df_desc = pd.read_csv(DESC_PATH)
    if os.path.exists(PREC_PATH):
        df_prec = pd.read_csv(PREC_PATH)
except Exception as e:
    print(f"Medical engine ML load notice: {e}")

# ==============================================================================
# Health Domain Guardrail (Dynamic Model Filter)
# ==============================================================================

# Obvious non-health domains to prevent non-medical queries
OUT_OF_DOMAIN_PATTERNS = [
    r'\b(python|javascript|java|c\+\+|html|css|programming|coding|algorithm|compiler|database|sql|github|function|developer|debug|syntax|script|api key|software)\b',
    r'\b(prime minister|president of|election|politics|parliament|bjp|congress|politician|government policy|democracy|minister)\b',
    r'\b(cricket|football|fifa|ipl|wicket|match score|messi|ronaldo|ipl score|champions trophy|batting|bowling|tennis|badminton|olympics)\b',
    r'\b(movie|cinema|actor|actress|bollywood|hollywood|trailer|song|music|lyrics|director|film|album|singer)\b',
    r'\b(bitcoin|crypto|cryptocurrency|stock market|share market|trading|sensex|nifty|mutual fund|forex|bank account|rupee rate)\b',
    r'\b(capital of|weather today|flight ticket|train ticket|hotel booking|railway|irctc|geography of|tallest mountain|river)\b',
    r'\b(tell me a joke|write a poem|write a story|sing a song|solve math|calculate|essay on|riddle|funny story)\b',
    r'\b(how to cook|recipe for|bake a cake|car repair|bike repair|engine|mechanic|iphone|android phone|laptop)\b'
]

# Comprehensive vocabulary of human health symptoms, medical conditions, and clinical queries
HEALTH_SYMPTOM_TERMS = {
    # Physical symptoms & sensory
    'fever', 'pyrexia', 'temperature', 'chills', 'shivering', 'sweat', 'sweating', 'night sweats',
    'headache', 'migraine', 'head ache', 'head pain', 'cephalalgia',
    'cough', 'coughing', 'phlegm', 'sputum', 'mucus', 'wheez', 'bronchitis', 'bronchial',
    'cold', 'flu', 'influenza', 'sneeze', 'sneezing', 'congestion', 'runny nose', 'blocked nose', 'sinus', 'sinusitis',
    'throat', 'sore throat', 'tonsil', 'tonsillitis', 'pharyngitis', 'laryngitis',
    'pain', 'ache', 'hurts', 'hurting', 'sore', 'cramp', 'cramps', 'tender', 'tenderness', 'stiff', 'stiffness',
    
    # Digestive, Gastrointestinal & Gut
    'digest', 'digestive', 'digestion', 'digestive issues', 'digestive problem', 'digestive system',
    'gut', 'gut health', 'gut issue', 'gut problem', 'stomach', 'abdomen', 'abdominal', 'belly',
    'gastric', 'gastritis', 'acidity', 'gas', 'bloat', 'bloating', 'indigestion', 'heartburn', 'gerd',
    'reflux', 'acid reflux', 'constipation', 'constipated', 'bowel', 'bowels', 'stool', 'stools',
    'vomit', 'vomiting', 'nausea', 'queasy', 'diarrhea', 'diarrhoea', 'loose motion', 'motions', 'dysentery',
    'flatulence', 'belching', 'burping', 'food poisoning', 'colitis', 'colon', 'ibs',
    'liver', 'gallbladder', 'pancreas', 'appendix', 'appendicitis', 'piles', 'hemorrhoid', 'hemorrhoids',
    'fistula', 'fissure', 'hernia',

    # Cardiovascular & Respiratory
    'chest', 'chest pain', 'angina', 'heart', 'cardiac', 'cardiovascular', 'palpitation', 'palpitations',
    'tachycardia', 'bradycardia', 'pulse', 'circulation', 'breath', 'breathing', 'breathless',
    'breathlessness', 'shortness of breath', 'dyspnea', 'suffocation', 'asthma', 'lungs', 'copd',

    # Neurological, Sleep & Psychological
    'dizzy', 'dizziness', 'vertigo', 'lightheaded', 'faint', 'fainting', 'syncope', 'blackout',
    'fatigue', 'tired', 'tiredness', 'weak', 'weakness', 'lethargy', 'lethargic', 'exhaustion', 'malaise',
    'numb', 'numbness', 'tingling', 'paralysis', 'tremor', 'tremors', 'seizure', 'convulsion',
    'insomnia', 'sleepless', 'anxiety', 'anxious', 'depression', 'depressed', 'panic attack', 'stress',

    # Dermatology, Skin & Hair
    'rash', 'skin rash', 'skin', 'itch', 'itching', 'pruritus', 'allergy', 'allergic', 'hives', 'urticaria',
    'swell', 'swelling', 'swollen', 'edema', 'oedema', 'inflammation', 'inflamed', 'puffy',
    'acne', 'pimple', 'pimples', 'eczema', 'psoriasis', 'dandruff', 'hair loss', 'hairfall', 'alopecia',
    'bleed', 'bleeding', 'blood', 'hemorrhage', 'bruise', 'bruising', 'hematoma',
    'burn', 'burning', 'burning sensation', 'ulcer', 'ulcers', 'wound', 'injury', 'cut', 'pus', 'boil', 'blister',

    # Endocrine, Metabolic & Renal
    'appetite', 'loss of appetite', 'weight loss', 'weight gain', 'dehydration', 'dehydrated', 'thirst',
    'urine', 'urinary', 'micturition', 'bladder', 'kidney', 'kidneys', 'kidney stone', 'uti', 'renal',
    'diabetes', 'diabetic', 'sugar level', 'blood sugar', 'glucose', 'insulin', 'blood pressure', 'bp',
    'hypertension', 'hypotension', 'thyroid', 'cholesterol', 'anemia', 'anaemic', 'platelet', 'platelets',

    # Musculoskeletal & Joints
    'joint', 'joints', 'knee', 'hip', 'shoulder', 'elbow', 'wrist', 'ankle', 'arthritis', 'osteoarthritis',
    'back', 'backache', 'back pain', 'spine', 'spinal', 'neck', 'neck pain', 'muscle', 'muscles', 'myalgia',
    'bone', 'bones', 'gout', 'sciatica', 'sprain', 'strain', 'fracture',

    # Sensory Organs (Eyes, Ears, Oral)
    'vision', 'blur', 'blurred', 'eye', 'eyes', 'red eye', 'conjunctivitis',
    'ear', 'earache', 'ear pain', 'hearing', 'tinnitus',
    'mouth', 'tongue', 'tooth', 'toothache', 'gum', 'gums', 'dental', 'teeth',

    # Clinical, Diagnosis & Medication
    'infection', 'infectious', 'viral', 'virus', 'bacterial', 'bacteria', 'fungal', 'fungus',
    'disease', 'illness', 'sickness', 'syndrome', 'disorder', 'condition', 'issue', 'issues', 'problem', 'problems',
    'dengue', 'malaria', 'typhoid', 'cholera', 'jaundice', 'hepatitis', 'tuberculosis', 'tb', 'pneumonia',
    'stroke', 'tumor', 'cancer',
    'medicine', 'medication', 'drug', 'pill', 'tablet', 'capsule', 'syrup', 'dosage', 'prescription',
    'doctor', 'physician', 'specialist', 'hospital', 'clinic', 'treatment', 'therapy', 'cure', 'remedy',
    'precaution', 'precautions', 'diagnosis', 'prognosis', 'patient', 'health', 'medical', 'wellness',

    # Hindi / Hinglish symptom terms
    'bukhar', 'bukhaar', 'sir dard', 'sar dard', 'dard', 'peeda', 'peedha',
    'khansi', 'khaansi', 'sardi', 'jukam', 'jukaam', 'zukaam', 'nazla',
    'ulti', 'ultiyan', 'ubkai', 'dast', 'pet dard', 'pet kharab', 'pet me dard',
    'chhati dard', 'chhati me dard', 'seene me dard', 'jalan', 'pet me jalan',
    'chakkar', 'chakkar aana', 'kamzori', 'kamzori lag rahi', 'thakan', 'thakawaat',
    'sujan', 'soojan', 'khujli', 'khujli hona', 'daane', 'lal daane', 'foda', 'funsi',
    'khoon', 'khoon aana', 'saans fulna', 'saans lene me dikkat', 'saans me taklif',
    'gala dard', 'gale me dard', 'gale me kharash', 'khich khich',
    'badan dard', 'body dard', 'kamar dard', 'peeth dard', 'jism dard',
    'guthno me dard', 'ghutna dard', 'jod dard', 'jodon ka dard',
    'dawa', 'dawae', 'dawai', 'ilaj', 'ilaaj', 'bimari', 'bimaar', 'tabiyat',
    'upchar', 'gharelu nuskhe', 'perhez', 'savdhani'
}

def is_health_related(query: str) -> bool:
    """
    Strict Symptom & Medical Domain Guardrail:
    - ONLY allows queries describing health symptoms, medical conditions, body organs, or clinical care.
    - STRICTLY refuses non-medical questions (coding, politics, sports, entertainment, tech, etc.).
    """
    if not query or not query.strip():
        return False
    clean = query.lower().strip()

    # 1. Reject explicit non-medical domain queries
    for pat in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pat, clean):
            # Allow only if physical injury or clinical emergency context is present
            if any(w in clean for w in ['pain', 'injury', 'hurt', 'fracture', 'doctor', 'hospital', 'bleeding']):
                return True
            return False

    # 2. Match against trained symptom features
    if len(symptom_features) > 0:
        for f in symptom_features:
            f_clean = str(f).lower().replace('_', ' ').strip()
            if f_clean and f_clean in clean:
                return True

    # 3. Match against symptom & health vocabulary
    words = re.findall(r'[a-zA-Z]+', clean)
    for term in HEALTH_SYMPTOM_TERMS:
        if ' ' in term:
            if term in clean:
                return True
        else:
            if term in words or any(w.startswith(term) or term in w for w in words):
                return True

    # 4. Match anatomical / organ systems combined with health indicators or inquiries
    body_organs = {
        'digest', 'digestive', 'digestion', 'gut', 'stomach', 'belly', 'abdomen', 'abdominal',
        'liver', 'heart', 'cardiac', 'lung', 'lungs', 'chest', 'throat', 'head', 'brain', 'skin',
        'eye', 'eyes', 'ear', 'ears', 'mouth', 'teeth', 'tooth', 'gum', 'bone', 'bones', 'joint',
        'joints', 'knee', 'back', 'neck', 'shoulder', 'muscle', 'muscles', 'nerve', 'nerves',
        'kidney', 'kidneys', 'urine', 'urinary', 'blood', 'hair', 'spine', 'bowel', 'colon',
        'rectum', 'esophagus'
    }
    if any(b in clean for b in body_organs):
        return True

    # 5. If none matched, it is outside healthcare domain -> refuse
    return False

def get_non_health_refusal_message() -> str:
    """Standard message returned when a user asks a general non-symptom question."""
    return (
        "⚠️ **Medical & Symptom Checker Domain Restriction:**\n\n"
        "I am your **Niramaya AI Health Assistant**. I am specialized **exclusively in health symptoms, medical conditions, and clinical precautions**.\n\n"
        "I do not answer questions outside the healthcare domain (such as general knowledge, coding, politics, sports, recipes, or entertainment).\n\n"
        "👉 **Please describe your health symptoms** (e.g., *fever, headache, cough, body pain, dizziness, stomach ache, rash*) to receive clinical assessment, home care, and precautions."
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
# Dynamic Clinical Response Generator (Multi-Symptom Intelligent Engine)
# ==============================================================================

def generate_clinical_response(prompt: str) -> str:
    """
    Dynamically generates a deeply customized, symptom-specific clinical medical assessment.
    When users enter multiple symptoms, it detects all symptom clusters and produces a
    tailored condition evaluation, causes, home remedies, dietary care, and targeted red flags.
    """
    if not prompt or not prompt.strip():
        return "Please describe your symptoms or health questions to receive clinical AI guidance."

    clean = prompt.strip()

    # Guardrail: Only answer health questions
    if not is_health_related(clean):
        return get_non_health_refusal_message()

    clean_lower = clean.lower()

    # Detect all matching clinical profiles from the user's manual symptoms
    matched_keys = []
    for key, prof in CLINICAL_PROFILES.items():
        if any(kw in clean_lower for kw in prof['keywords']):
            matched_keys.append(key)

    # Clean display title
    topic_title = clean.rstrip('?!.').strip()
    if len(topic_title) > 60:
        topic_title = topic_title[:60].strip() + "..."
    topic_title = topic_title.title()

    # If single clinical profile matched:
    if len(matched_keys) == 1:
        prof = CLINICAL_PROFILES[matched_keys[0]]
        condition_title = prof['condition']
        overview_text = prof['overview']
        causes_list = prof['causes']
        care_list = prof['home_care']
        precautions_list = prof['precautions']
        red_flags_list = prof['red_flags']
        symptoms_display = [f"{clean.title()} ({prof['name']})"]

    # If multiple clinical profiles matched (e.g. fever + cough + sore throat):
    elif len(matched_keys) > 1:
        matched_profs = [CLINICAL_PROFILES[k] for k in matched_keys]
        prof_names = " + ".join([p['name'].split('(')[0].strip() for p in matched_profs])
        condition_title = f"Multi-Symptom Complex: {prof_names} (संयुक्त लक्षण मूल्यांकन)"
        overview_text = (
            f"You have presented with multiple concurrent symptoms involving {prof_names}. "
            "When multiple symptoms coincide, physiological systems often interact synergistically—such as an infectious viral agent "
            "triggering upper respiratory congestion, fever, and digestive sensitivity simultaneously. A comprehensive clinical approach "
            "addresses both the primary trigger and symptomatic comfort across each affected organ system."
        )
        symptoms_display = []
        for k in matched_keys:
            p = CLINICAL_PROFILES[k]
            # Find the specific keywords from this profile that matched
            matched_kws = [kw for kw in p['keywords'] if kw in clean_lower][:2]
            kw_str = ", ".join(matched_kws).title() if matched_kws else p['name']
            symptoms_display.append(f"{kw_str} — {p['condition']}")

        # Interleave top causes from each matched profile
        causes_list = []
        for p in matched_profs:
            causes_list.extend(p['causes'][:2])

        # Interleave top care items from each matched profile
        care_list = []
        for p in matched_profs:
            care_list.extend(p['home_care'][:2])

        # Interleave precautions
        precautions_list = []
        for p in matched_profs:
            precautions_list.extend(p['precautions'][:2])

        # Interleave red flags
        red_flags_list = []
        for p in matched_profs:
            red_flags_list.extend(p['red_flags'][:2])

    # Fallback for generic health queries that didn't match a specific cluster:
    else:
        condition_title = f"{topic_title} (Clinical Health Evaluation)"
        overview_text = (
            f"Health inquiry regarding '{clean}' involves evaluating underlying physiological, metabolic, or infectious factors. "
            "Symptoms typically reflect your body's immune or compensatory response to strain, dehydration, or environmental exposure."
        )
        symptoms_display = [f"{clean.title()} (Reported Health Symptom)"]
        causes_list = [
            "Physiological immune or metabolic adaptation to recent fatigue, strain, or dietary changes",
            "Transient viral, bacterial, or seasonal allergic reactivity affecting general vitality",
            "Hydration deficit, irregular sleep ergonomics, or heightened situational stress"
        ]
        care_list = [
            "Hydration: Drink 2.5 to 3 liters of warm water, oral electrolytes, and clear herbal teas",
            "Nutritional Rest: Consume freshly cooked, light, balanced meals (steamed vegetables, oats, soups)",
            "Physical Rest: Ensure 7 to 8 hours of uninterrupted rest in a comfortable, quiet environment"
        ]
        precautions_list = [
            "Avoid unprescribed self-medication with strong analgesics or antibiotics",
            "Maintain clean personal hygiene and avoid exposure to sudden temperature extremes",
            "Track symptom progression and record duration, intensity, or any aggravating factors"
        ]
        red_flags_list = [
            "🚨 High fever (>102°F / 38.9°C) that persists despite cooling measures",
            "🚨 Severe acute pain, difficulty breathing, or sudden dizziness",
            "🚨 Inability to retain oral liquids or profound physical weakness"
        ]

    # Format into beautiful Markdown response
    symptoms_text = "\n".join([f"- {s}" for s in symptoms_display])
    causes_text = "\n".join([f"- {c}" for c in causes_list])
    care_text = "\n".join([f"- {h}" for h in care_list])
    precautions_text = "\n".join([f"- {p}" for p in precautions_list])
    red_flags_text = "\n".join([f"- {r}" for r in red_flags_list])

    response = (
        f"**Condition / Clinical Assessment:** {condition_title}\n\n"
        f"**Identified Symptoms & Health Inquiries:**\n"
        f"{symptoms_text}\n\n"
        f"**Medical Overview:**\n"
        f"{overview_text}\n\n"
        f"**Probable Causes & Contributing Factors:**\n"
        f"{causes_text}\n\n"
        f"**Dietary Recommendations & Home Care:**\n"
        f"{care_text}\n\n"
        f"**Key Health Precautions & Self-Care:**\n"
        f"{precautions_text}\n\n"
        f"**When to Seek Immediate Medical Attention (Red Flags):**\n"
        f"{red_flags_text}\n\n"
        f"*(Disclaimer: Niramaya provides AI-guided informational health insights. This does not replace formal examination, laboratory diagnosis, or prescription by a licensed medical practitioner.)*"
    )
    return response

# ==============================================================================
# Machine Learning Disease Prediction (LRv1 and LRv2)
# ==============================================================================

def extract_symptoms_from_text(text: str) -> list:
    """Extracts symptom features from text matching trained ML features."""
    if not text:
        return []
    clean = text.lower()
    matched = []
    if len(symptom_features) > 0:
        for f in symptom_features:
            f_clean = str(f).lower().replace('_', ' ').strip()
            if f_clean in clean:
                matched.append(str(f))
    return matched[:10]

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

def get_lrv1_prediction(query_text: str) -> dict:
    """
    Returns structured data for LRv1 endpoint:
    { predicted_disease, matched_symptoms, description }
    Strictly verifies health relevance.
    """
    if not query_text or not query_text.strip():
        return {
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter health symptoms to run disease prediction.'
        }

    clean = query_text.strip()
    if not is_health_related(clean):
        return {
            'predicted_disease': 'Non-Health Query',
            'matched_symptoms': [],
            'description': 'Niramaya AI only processes medical and health symptoms. Please enter specific health symptoms to predict conditions.'
        }

    # Match against ML features
    matched_features = extract_symptoms_from_text(clean)
    pred_disease = clean.title()

    if lr_model is not None and len(symptom_features) > 0:
        try:
            vec = [0] * len(symptom_features)
            for i, f in enumerate(symptom_features):
                f_clean = str(f).lower().replace('_', ' ').strip()
                if f_clean in clean.lower():
                    vec[i] = 1
            if sum(vec) > 0:
                X_df = pd.DataFrame([vec], columns=list(symptom_features))
                pred_disease = str(lr_model.predict(X_df)[0])
        except Exception:
            pass

    # Lookup description from CSV
    desc = f"Clinical evaluation regarding '{clean}'. Please monitor symptom duration, maintain adequate hydration, and consult a doctor."
    if not df_desc.empty and 'disease' in df_desc.columns and 'description' in df_desc.columns:
        match = df_desc[df_desc['disease'].str.lower() == pred_disease.lower()]
        if not match.empty:
            desc = match['description'].values[0]

    return {
        'predicted_disease': pred_disease,
        'matched_symptoms': matched_features if matched_features else [clean.title()],
        'description': desc
    }

def get_lrv2_prediction(query_text: str) -> dict:
    """
    Returns structured data for LRv2 endpoint:
    { predicted_disease, matched_symptoms, description, precautions }
    Strictly verifies health relevance.
    """
    if not query_text or not query_text.strip():
        return {
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter health symptoms to run disease prediction.',
            'precautions': ['Enter symptom names like fever, headache, body pain']
        }

    clean = query_text.strip()
    if not is_health_related(clean):
        return {
            'predicted_disease': 'Non-Health Query',
            'matched_symptoms': [],
            'description': 'Niramaya AI only processes medical and health symptoms. Please enter specific health symptoms to predict conditions.',
            'precautions': ['Please ask questions related to health symptoms, medical conditions, and care.']
        }

    # Predict via LRv1
    res = get_lrv1_prediction(clean)
    pred_disease = res['predicted_disease']

    # Lookup precautions from CSV
    precautions = [
        "Maintain adequate physical rest and stay well-hydrated throughout the day",
        "Consume freshly prepared, easily digestible meals and avoid physical overexertion",
        "Monitor symptoms closely and track their severity and progression",
        "Consult a certified physician or healthcare professional for clinical examination"
    ]

    if not df_prec.empty and 'disease' in df_prec.columns:
        match = df_prec[df_prec['disease'].str.lower() == pred_disease.lower()]
        if not match.empty:
            cols = [c for c in df_prec.columns if 'precaution' in c.lower()]
            found = [str(match[c].values[0]).strip() for c in cols if pd.notna(match[c].values[0]) and str(match[c].values[0]).strip()]
            if found:
                precautions = found

    return {
        'predicted_disease': pred_disease,
        'matched_symptoms': res['matched_symptoms'],
        'description': res['description'],
        'precautions': precautions
    }
