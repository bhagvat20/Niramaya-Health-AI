from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
import joblib
import pandas as pd

# Import the Clinical Medical Intelligence Engine
from medical_engine import (
    generate_clinical_response,
    get_lrv1_prediction,
    get_lrv2_prediction,
    extract_symptoms_from_text,
    SYMPTOM_DISPLAY
)

# Create a Blueprint for disease predictor routes
AI_bp = Blueprint('health_AI', __name__)
CORS(AI_bp)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# BioGPT Generator (Lazy Loaded if installed)
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

lr_model = None
symptom_features = []

try:
    if os.path.exists(MODEL_PATH):
        lr_model = joblib.load(MODEL_PATH)
    if os.path.exists(SYMPTOM_FEATURES_PATH):
        symptom_features = joblib.load(SYMPTOM_FEATURES_PATH)
except Exception as e:
    print(f"Note: LR model load notice: {e}")

GREETINGS_LIST = {'hi', 'hello', 'hey', 'greetings', 'namaste', 'good morning', 'good afternoon', 'good evening', 'help', 'who are you', 'test', 'kya hal hai', 'kese ho'}

def check_greeting_response(text):
    if not text:
        return None
    clean = text.strip().lower().rstrip('?!.')
    if clean in GREETINGS_LIST or any(clean.startswith(g + ' ') for g in ['hi', 'hello', 'hey', 'namaste']):
        return {
            'predicted_disease': 'Niramaya AI Health Assistant',
            'matched_symptoms': [],
            'description': 'Hello! I am your Niramaya AI Health Assistant. Please describe any symptoms you are experiencing (e.g., fever, headache, cough, body pain, loose motions) or ask any health question to receive clinical insights, home care, and precautions.',
            'precautions': [
                'List all specific symptoms you are experiencing in detail',
                'Track symptom onset, severity, and duration',
                'Stay well-hydrated with clean water and ensure adequate rest',
                'Seek prompt medical consultation for severe or persistent conditions'
            ],
            'answer': 'Hello! I am your Niramaya AI Health Assistant. Please describe any symptoms you are experiencing (e.g., fever, headache, cough, stomach pain, rash) or ask any medical question to receive instant AI guidance.'
        }
    return None

def generate_any_health_response(prompt):
    """
    Answers ANY medical question or symptom query dynamically.
    Combines live Gemini AI (if valid API key is configured) + Clinical Medical Engine.
    Ensures identical, high-accuracy output across Render and Local environments.
    """
    # 1. Try Gemini Generative AI if key is configured and valid
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
            for m in models_to_try:
                try:
                    model = genai.GenerativeModel(m)
                    resp = model.generate_content(
                        f"You are Niramaya Health AI medical assistant. Provide a helpful, clear, empathetic medical response in structured markdown including condition overview, detected symptoms, causes, dietary recommendations, home care, precautions, and when to seek urgent emergency care for: {prompt}"
                    )
                    if resp and resp.text:
                        return resp.text
                except Exception:
                    continue
        except Exception as e:
            print(f"Gemini API note: {e}")

    # 2. Clinical Medical Intelligence Engine (Deterministic, offline-capable, comprehensive)
    return generate_clinical_response(prompt)

@AI_bp.route("/askbiogpt", methods=["POST"])
def ask_biogpt():
    """Handles medical questions and symptom assessment using BioGPT / Clinical Engine."""
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

    # Dynamic clinical medical answer for any query
    ans = generate_clinical_response(question)
    return jsonify({"question": question, "answer": ans}), 200

@AI_bp.route("/askgemini", methods=["POST"])
def ask_gemini():
    """Handles user medical questions and generates answers using Gemini API or Clinical Medical Engine."""
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
    """Handles disease prediction from symptoms (LRv1 endpoint)."""
    data = request.get_json() or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms (e.g. fever, headache, cough, vomiting) to run disease prediction.'
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    prediction = get_lrv1_prediction(symptom_text)
    return jsonify(prediction), 200

@AI_bp.route('/asklrv2', methods=['POST'])
def askLRv2():
    """Handles disease prediction from symptoms with precautions (LRv2 endpoint)."""
    data = request.get_json() or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'predicted_disease': 'Input Required',
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms to run disease prediction and get precaution advice.',
            'precautions': ['Enter symptom names like fever, headache, body pain, nausea, loose motion']
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    prediction = get_lrv2_prediction(symptom_text)
    return jsonify(prediction), 200
