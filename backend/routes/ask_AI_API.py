from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
import re
import json
import urllib.request
import urllib.parse
import joblib
import pandas as pd

# Create a Blueprint for disease predictor routes
AI_bp = Blueprint('health_AI', __name__)
CORS(AI_bp)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# BioGPT Generator (Lazy Loaded)
biogpt_generator = None
biogpt_attempted = False

def get_biogpt_generator():
    global biogpt_generator, biogpt_attempted
    if biogpt_generator is not None:
        return biogpt_generator
    if biogpt_attempted:
        return None
    biogpt_attempted = True
    try:
        from transformers import pipeline, BioGptTokenizer, BioGptForCausalLM
        model_name = "microsoft/biogpt"
        tokenizer = BioGptTokenizer.from_pretrained(model_name, local_files_only=True)
        biogpt_model = BioGptForCausalLM.from_pretrained(model_name, local_files_only=True)
        biogpt_generator = pipeline("text-generation", model=biogpt_model, tokenizer=tokenizer)
    except Exception as e:
        print(f"BioGPT local load note: {e}")
        return None
    return biogpt_generator

# LR (Logistic Regression Model Setup)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model_LR', 'logistic_regression_model.pkl')
SYMPTOM_FEATURES_PATH = os.path.join(BASE_DIR, 'model_LR', 'symptom_features.pkl')
DESC_PATH = os.path.join(BASE_DIR, 'model_LR', 'Symptom_Description.csv')
PRECAUTION_PATH = os.path.join(BASE_DIR, 'model_LR', 'Symptom_Precaution.csv')

lr_model = None
symptom_features = []
desc_df = pd.DataFrame()
prec_df = pd.DataFrame()
FEATURE_MAP = {}

def normalize_sym(text):
    return re.sub(r'[\s_\-]+', ' ', str(text).strip().lower())

try:
    if os.path.exists(MODEL_PATH):
        lr_model = joblib.load(MODEL_PATH)
    if os.path.exists(SYMPTOM_FEATURES_PATH):
        symptom_features = joblib.load(SYMPTOM_FEATURES_PATH)
        FEATURE_MAP = {normalize_sym(f): f for f in symptom_features}
    if os.path.exists(DESC_PATH):
        desc_df = pd.read_csv(DESC_PATH)
        desc_df['disease'] = desc_df['disease'].astype(str).str.lower().str.strip()
    if os.path.exists(PRECAUTION_PATH):
        prec_df = pd.read_csv(PRECAUTION_PATH)
        prec_df['disease'] = prec_df['disease'].astype(str).str.lower().str.strip()
except Exception as e:
    print(f"Error loading LR model data: {e}")

def parse_symptoms(symptom_text):
    """
    Parse user symptom input into a list of exact matching feature names.
    Supports comma-separated, space-separated, underscore-separated, and natural phrasing.
    """
    if not symptom_text:
        return []
    cleaned = symptom_text.lower()
    matched = set()

    parts = re.split(r'[,;\n|]+', cleaned)
    for part in parts:
        part_norm = normalize_sym(part)
        if part_norm in FEATURE_MAP:
            matched.add(FEATURE_MAP[part_norm])

    norm_text = normalize_sym(cleaned)
    for norm_feat, orig_feat in FEATURE_MAP.items():
        if len(norm_feat) >= 3:
            pattern = r'(?:\b|_)' + re.escape(norm_feat) + r'(?:\b|_)'
            if re.search(pattern, norm_text) or re.search(pattern, cleaned):
                matched.add(orig_feat)

    return list(matched)

def predict_disease_from_symptoms(symptoms_list):
    if not lr_model or len(symptom_features) == 0 or not symptoms_list:
        return None
    input_vector = [1 if symptom in symptoms_list else 0 for symptom in symptom_features]
    if sum(input_vector) == 0:
        return None
    input_df = pd.DataFrame([input_vector], columns=symptom_features)
    prediction = lr_model.predict(input_df)
    return prediction[0]

def fetch_medical_encyclopedia(query):
    """
    Dynamically fetches verified medical descriptions from medical encyclopedia API
    for ANY disease, symptom, or health condition without any fixed limitation.
    """
    q = query.strip()
    # Remove common conversational prefixes
    clean_q = re.sub(r'^(what is|tell me about|how to cure|how to treat|treatment for|symptoms of|cure for|causes of|precautions for|info about|can you explain)\s+', '', q, flags=re.I).strip()
    # Remove common conversational suffixes
    clean_q = re.sub(r'\s+(and what to eat|and precautions|and treatment|and cure|and diet|diet plan|home remedies|symptoms)\??$', '', clean_q, flags=re.I).strip()
    clean_q = re.sub(r'[\?\.\!]+$', '', clean_q).strip()
    if not clean_q:
        clean_q = q

    # 1. Direct Page Summary
    try:
        page_name = urllib.parse.quote(clean_q.replace(' ', '_'))
        url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_name}'
        req = urllib.request.Request(url, headers={'User-Agent': 'NiramayaHealthAI/2.0 (medical-assistant)'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('type') != 'disambiguation' and data.get('extract'):
                return data.get('title', clean_q.title()), data.get('extract')
    except Exception:
        pass

    # 2. Search Query API for fallback terms (e.g. "dengue", "chikungunya", "typhoid")
    try:
        search_term = urllib.parse.quote(clean_q)
        s_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json'
        req2 = urllib.request.Request(s_url, headers={'User-Agent': 'NiramayaHealthAI/2.0'})
        with urllib.request.urlopen(req2, timeout=3) as resp2:
            s_data = json.loads(resp2.read().decode('utf-8'))
            results = s_data.get('query', {}).get('search', [])
            if results:
                top_title = results[0]['title']
                u3 = f'https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_title.replace(" ", "_"))}'
                req3 = urllib.request.Request(u3, headers={'User-Agent': 'NiramayaHealthAI/2.0'})
                with urllib.request.urlopen(req3, timeout=3) as resp3:
                    d3 = json.loads(resp3.read().decode('utf-8'))
                    if d3.get('extract'):
                        return d3.get('title', top_title), d3.get('extract')
    except Exception:
        pass

    return clean_q.title(), None

def get_dynamic_precautions(condition_name, text_context=""):
    """
    Returns disease-specific precautions from CSV if available,
    otherwise dynamically synthesizes medically sound precautions for ANY condition.
    """
    c_lower = str(condition_name).lower().strip()
    if not prec_df.empty:
        prec_row = prec_df[prec_df['disease'] == c_lower]
        if not prec_row.empty:
            precautions = [v for k, v in prec_row.iloc[0].items() if k.startswith('precaution') and pd.notna(v)]
            if precautions:
                return precautions

    # Intelligent contextual precautions for any disease
    text_check = (c_lower + " " + text_context.lower())
    precautions = []
    if any(k in text_check for k in ['dengue', 'malaria', 'chikungunya', 'zika', 'mosquito']):
        precautions = [
            "Use mosquito repellents and sleep under mosquito nets",
            "Eliminate standing water around the home to prevent mosquito breeding",
            "Drink plenty of fluids (ORS, coconut water) to maintain platelet levels",
            "Avoid NSAIDs like aspirin or ibuprofen; use paracetamol strictly under medical guidance"
        ]
    elif any(k in text_check for k in ['covid', 'flu', 'influenza', 'cough', 'cold', 'pneumonia', 'fever', 'bronchitis']):
        precautions = [
            "Rest adequately and stay well-hydrated with warm liquids",
            "Isolate in a well-ventilated space to prevent spreading infection",
            "Monitor body temperature and blood oxygen saturation (SpO2)",
            "Wear a protective mask and practice frequent handwashing"
        ]
    elif any(k in text_check for k in ['typhoid', 'food poisoning', 'diarrhea', 'vomiting', 'stomach', 'cholera']):
        precautions = [
            "Drink boiled or purified drinking water only",
            "Eat freshly cooked, hot, and hygienic food; avoid raw street foods",
            "Use Oral Rehydration Salts (ORS) frequently to prevent dehydration",
            "Wash hands thoroughly with soap before eating and after using the restroom"
        ]
    elif any(k in text_check for k in ['migraine', 'headache', 'stress']):
        precautions = [
            "Rest in a quiet, dark, and cool room during acute episodes",
            "Maintain consistent sleep and meal schedules",
            "Identify and avoid sensory triggers (loud sounds, bright flashing lights, strong smells)",
            "Stay well-hydrated and practice deep breathing or relaxation techniques"
        ]
    elif any(k in text_check for k in ['diabetes', 'sugar']):
        precautions = [
            "Monitor blood glucose levels regularly as advised by your doctor",
            "Follow a balanced low-glycemic, fiber-rich diet with limited refined carbs",
            "Engage in at least 30 minutes of moderate physical activity daily",
            "Inspect feet daily for cuts or sores and take prescribed medications on time"
        ]
    elif any(k in text_check for k in ['hypertension', 'blood pressure', 'heart', 'cardiac']):
        precautions = [
            "Reduce dietary sodium (salt) intake and avoid processed foods",
            "Check and log blood pressure readings regularly",
            "Engage in doctor-approved cardiovascular exercise (e.g. brisk walking)",
            "Avoid tobacco, limit caffeine, and practice active stress reduction"
        ]
    elif any(k in text_check for k in ['joint', 'arthritis', 'knee', 'back', 'pain']):
        precautions = [
            "Apply warm or cold compresses to relieve localized inflammation and stiffness",
            "Maintain low-impact movement (swimming, gentle stretching, walking)",
            "Maintain an ergonomic posture and avoid lifting heavy objects suddenly",
            "Consult a physiotherapist or orthopedic specialist for targeted rehabilitation"
        ]
    else:
        precautions = [
            "Ensure proper rest and stay well-hydrated throughout the day",
            "Maintain a balanced, easily digestible diet rich in vitamins",
            "Monitor symptoms closely and track their severity and duration",
            "Consult a qualified physician or healthcare provider for clinical diagnosis"
        ]

    return precautions

def generate_any_health_response(prompt):
    """
    Answers ANY medical question or disease query dynamically.
    Combines live Gemini AI (if key is set) + Live Medical Encyclopedia + Clinical Database.
    """
    # 1. Try Gemini Generative AI if key is configured
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
            for m in models_to_try:
                try:
                    model = genai.GenerativeModel(m)
                    resp = model.generate_content(
                        f"You are Niramaya Health AI medical assistant. Provide a helpful, clear, empathetic medical response including condition overview, symptoms, precautions, and when to seek urgent care for: {prompt}"
                    )
                    if resp and resp.text:
                        return resp.text
                except Exception:
                    continue
        except Exception as e:
            print(f"Gemini error: {e}")

    # 2. Dynamic Medical Encyclopedia lookup (checks if user is asking about a specific disease/condition)
    condition_title, wiki_extract = fetch_medical_encyclopedia(prompt)

    # 3. Check if prompt matches symptoms in trained ML model
    matched_syms = parse_symptoms(prompt)
    ml_disease = None
    if matched_syms and (not wiki_extract or len(matched_syms) >= 2):
        ml_disease = predict_disease_from_symptoms(matched_syms)

    # Determine primary disease: prioritize explicit encyclopedia match if found, else ML prediction
    if wiki_extract and condition_title.lower() not in ['fever', 'headache', 'cough', 'vomiting']:
        primary_condition = condition_title
        desc = wiki_extract
    elif ml_disease:
        primary_condition = ml_disease
        desc = None
        if not desc_df.empty:
            row = desc_df[desc_df['disease'] == str(ml_disease).lower()]
            if not row.empty:
                desc = row['description'].values[0]
        if not desc:
            desc = wiki_extract or f"{primary_condition} is a medical condition associated with your reported symptoms."
    else:
        primary_condition = condition_title or prompt.title()
        desc = wiki_extract or f"Guidance regarding {primary_condition}: Please evaluate symptom progression and speak with a clinician."

    precautions = get_dynamic_precautions(primary_condition, prompt)
    prec_text = "\n".join([f"- {p}" for p in precautions])

    matched_text = f"\n*Detected Symptoms:* {', '.join(matched_syms)}\n" if matched_syms else ""

    response = (
        f"**Condition / Topic:** {primary_condition}\n"
        f"{matched_text}\n"
        f"**Medical Overview:**\n"
        f"{desc}\n\n"
        f"**Key Health Precautions & Self-Care:**\n"
        f"{prec_text}\n\n"
        f"**When to Seek Immediate Medical Attention:**\n"
        f"- High persistent fever that doesn't reduce with medication\n"
        f"- Shortness of breath, chest tightness, or severe dizziness\n"
        f"- Uncontrolled vomiting, acute localized pain, or dehydration\n\n"
        f"*(Disclaimer: Niramaya provides AI-guided health insights. This does not replace formal clinical diagnosis or physician consultation.)*"
    )
    return response

GREETINGS_LIST = {'hi', 'hello', 'hey', 'greetings', 'namaste', 'good morning', 'good afternoon', 'good evening', 'help', 'who are you', 'test'}

def check_greeting_response(text):
    if not text:
        return None
    clean = text.strip().lower().rstrip('?!.')
    if clean in GREETINGS_LIST or any(clean.startswith(g + ' ') for g in ['hi', 'hello', 'hey', 'namaste']):
        return {
            'predicted_disease': 'Niramaya AI Health Assistant',
            'matched_symptoms': [],
            'description': 'Hello! I am your Niramaya AI Health Assistant. Please describe any symptoms you are experiencing (e.g., fever, headache, cough, fatigue, skin rash) or ask any health question to receive clinical insights and precautions.',
            'precautions': [
                'List all specific symptoms you are experiencing',
                'Track symptom onset, severity, and progression',
                'Stay well-hydrated and ensure adequate physical rest',
                'Seek prompt medical consultation for severe or persistent conditions'
            ],
            'answer': 'Hello! I am your Niramaya AI Health Assistant. Please describe any symptoms you are experiencing (e.g., fever, headache, cough, rash) or ask any medical question to receive instant AI guidance.'
        }
    return None

@AI_bp.route("/askbiogpt", methods=["POST"])
def ask_biogpt():
    """Handles medical questions using BioGPT with dynamic knowledge fallback."""
    data = request.get_json() or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "question": "",
            "answer": "Please enter your health symptoms or a question to receive AI guidance."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"question": question, "answer": greet['answer']}), 200

    # Try local BioGPT if cached
    generator = get_biogpt_generator()
    if generator is not None:
        try:
            responses = generator(question, max_length=400, num_return_sequences=1, do_sample=True)
            ans = " ".join([r.get("generated_text", "") for r in responses if r.get("generated_text")])
            if ans:
                return jsonify({"question": question, "answer": ans})
        except Exception as e:
            print(f"BioGPT generate error: {e}")

    # Dynamic medical answer for any query
    ans = generate_any_health_response(question)
    return jsonify({"question": question, "answer": ans}), 200

@AI_bp.route("/askgemini", methods=["POST"])
def ask_gemini():
    """Handles user medical questions and generates answers using Gemini API or Dynamic AI."""
    data = request.get_json() or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "question": "",
            "answer": "Please enter your health symptoms or a question to receive AI guidance."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"question": question, "answer": greet['answer']}), 200

    answer = generate_any_health_response(question)
    return jsonify({"question": question, "answer": answer}), 200

@AI_bp.route('/asklrv1', methods=['POST'])
def askLRv1():
    data = request.get_json() or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms (e.g. fever, headache, cough) to run disease prediction.'
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    # 1. Check if user entered symptom list for ML model
    symptoms_list = parse_symptoms(symptom_text)
    predicted_disease = predict_disease_from_symptoms(symptoms_list)

    if predicted_disease:
        desc_row = desc_df[desc_df['disease'] == str(predicted_disease).lower()]
        description = desc_row['description'].values[0] if not desc_row.empty else 'Please consult a healthcare professional for clinical diagnosis.'
        return jsonify({
            'predicted_disease': str(predicted_disease),
            'matched_symptoms': symptoms_list,
            'description': description
        }), 200

    cond_title, wiki_desc = fetch_medical_encyclopedia(symptom_text)
    desc = wiki_desc or f"Health guidance regarding '{symptom_text}'. Please monitor symptom duration and consult a physician."
    return jsonify({
        'predicted_disease': cond_title or symptom_text.title(),
        'matched_symptoms': [symptom_text],
        'description': desc
    }), 200

@AI_bp.route('/asklrv2', methods=['POST'])
def askLRv2():
    data = request.get_json() or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms to run disease prediction and get precaution advice.',
            'precautions': ['Enter symptom names like fever, headache, body pain, nausea']
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    # 1. Check if user entered symptom list for ML model
    symptoms_list = parse_symptoms(symptom_text)
    predicted_disease = predict_disease_from_symptoms(symptoms_list)

    if predicted_disease:
        desc_row = desc_df[desc_df['disease'] == str(predicted_disease).lower()]
        description = desc_row['description'].values[0] if not desc_row.empty else 'Please consult a healthcare professional for clinical diagnosis.'
        precautions = get_dynamic_precautions(predicted_disease, symptom_text)
        return jsonify({
            'predicted_disease': str(predicted_disease),
            'matched_symptoms': symptoms_list,
            'description': description,
            'precautions': precautions
        }), 200

    cond_title, wiki_desc = fetch_medical_encyclopedia(symptom_text)
    desc = wiki_desc or f"Health guidance regarding '{symptom_text}'. Clinical evaluation is recommended."
    precautions = get_dynamic_precautions(cond_title, symptom_text)

    return jsonify({
        'predicted_disease': cond_title or symptom_text.title(),
        'matched_symptoms': [symptom_text],
        'description': desc,
        'precautions': precautions
    }), 200
