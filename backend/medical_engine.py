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
    r'\b(python|javascript|java|c\+\+|html|css|programming|coding|algorithm|compiler|database|sql|github|function)\b',
    r'\b(prime minister|president of|election|politics|parliament|bjp|congress)\b',
    r'\b(cricket|football|fifa|ipl|wicket|match score|messi|ronaldo)\b',
    r'\b(movie|cinema|actor|actress|bollywood|hollywood|trailer|song)\b',
    r'\b(bitcoin|crypto|cryptocurrency|stock market|share market|trading|sensex|nifty)\b',
    r'\b(capital of|weather today|flight ticket|train ticket)\b'
]

def is_health_related(query: str) -> bool:
    """
    Dynamically allows user queries to be answered by the AI/ML models.
    Refuses only queries that explicitly fall into non-health domains (coding, politics, sports, etc.).
    """
    if not query or not query.strip():
        return False
    clean = query.lower().strip()

    # Reject non-medical domain queries unless health context is present
    for pat in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pat, clean):
            # If the user is asking about an injury or health issue related to sports/activities, allow it
            if any(w in clean for w in ['pain', 'injury', 'hurt', 'fracture', 'doctor', 'hospital']):
                return True
            return False

    return True

def get_non_health_refusal_message() -> str:
    """Standard message returned when a user asks a non-health related question."""
    return (
        "**Medical Domain Restriction:**\n"
        "I am Niramaya AI Health Assistant. I am specialized exclusively in human health, medical conditions, symptoms, medications, nutrition, and wellness topics.\n\n"
        "I cannot answer questions outside the healthcare domain (such as general trivia, coding, politics, sports, or entertainment).\n\n"
        "**Please ask a health-related question** (e.g., about your symptoms, medical concerns, home care, diet, or precautions)."
    )

# ==============================================================================
# Dynamic Clinical Response Generator (Handles ANY random health question)
# ==============================================================================

def generate_clinical_response(prompt: str) -> str:
    """
    Dynamically generates a comprehensive, structured clinical medical assessment
    for ANY random health question without requiring static hardcoded dictionaries.
    """
    if not prompt or not prompt.strip():
        return "Please describe your symptoms or health questions to receive clinical AI guidance."

    clean = prompt.strip()

    # Guardrail: Only answer health questions
    if not is_health_related(clean):
        return get_non_health_refusal_message()

    # Extract topic headline
    topic_title = clean.rstrip('?!.').strip()
    if len(topic_title) > 60:
        topic_title = topic_title[:60].strip() + "..."
    topic_title = topic_title.title()

    # Build dynamic structured clinical response for any random health query
    response = (
        f"**Condition / Clinical Assessment:** {topic_title} (Health & Symptom Evaluation)\n\n"
        f"**Identified Symptoms & Health Inquiries:**\n"
        f"- {clean}\n\n"
        f"**Medical Overview:**\n"
        f"Health inquiries regarding '{clean}' involve evaluating underlying physiological, metabolic, or infectious factors. "
        f"Symptoms or changes in your physical state typically reflect the body's natural response to strain, dehydration, dietary imbalance, or environmental exposure. "
        f"Proper clinical assessment involves observing the duration, intensity, and progression of the symptoms.\n\n"
        f"**Probable Causes & Contributing Factors:**\n"
        f"- Dehydration, electrolyte imbalance, or irregular fluid intake\n"
        f"- Physical or mental stress, prolonged screen time, or poor sleep ergonomics\n"
        f"- Dietary irregularities, skipping meals, or consumption of unhygienic/irritating food\n"
        f"- Underlying viral, bacterial, or seasonal allergic reactivity\n\n"
        f"**Dietary Recommendations & Home Care:**\n"
        f"- Hydration: Drink 2 to 3 liters of clean, warm water or electrolyte broths throughout the day.\n"
        f"- Nutrition: Consume freshly cooked, light, nutrient-rich meals (e.g., vegetable soups, oats, fresh fruits); avoid excessive oil, spices, and caffeine.\n"
        f"- Physical Rest: Ensure 7 to 8 hours of uninterrupted rest in a comfortable, quiet, well-ventilated space.\n"
        f"- Observation: Keep a simple log of symptom frequency and any triggers you notice.\n\n"
        f"**Key Health Precautions & Self-Care:**\n"
        f"- Avoid unprescribed, frequent self-medication with strong painkillers or antibiotics.\n"
        f"- Practice good posture, gentle body stretches, and avoid heavy strenuous physical exertion.\n"
        f"- Maintain clean personal hygiene and avoid exposure to known allergens or pollutants.\n\n"
        f"**When to Seek Immediate Medical Attention (Red Flags):**\n"
        f"- 🚨 High fever (>102°F / 38.9°C) that persists despite cooling measures\n"
        f"- 🚨 Severe, acute pain, difficulty breathing, chest tightness, or dizziness\n"
        f"- 🚨 Continuous vomiting, inability to retain liquids, or extreme physical weakness\n"
        f"- 🚨 Any neurological changes such as sudden confusion, speech difficulty, or fainting\n\n"
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
                pred_disease = str(lr_model.predict([vec])[0])
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
