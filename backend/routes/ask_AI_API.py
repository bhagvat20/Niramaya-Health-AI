from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
import re
import joblib
import pandas as pd

# Import the Clinical Medical Intelligence Engine
from medical_engine import (
    generate_clinical_response,
    get_lrv1_prediction,
    get_lrv2_prediction,
    extract_symptoms_from_text,
    SYMPTOM_DISPLAY,
    is_health_related,
    get_non_health_refusal_message
)

# Create a Blueprint for disease predictor routes
AI_bp = Blueprint('health_AI', __name__)
CORS(AI_bp)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# BioGPT Generator (Lazy Loaded if installed locally)
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

GREETINGS_EXACT = {
    'hi', 'hello', 'hey', 'greetings', 'namaste', 'good morning', 'good afternoon',
    'good evening', 'help', 'hi there', 'hello there', 'hey there', 'hi niramaya',
    'hello niramaya', 'namaste niramaya'
}


def check_greeting_response(text):
    """
    Matches ONLY pure short greetings so users are guided to enter health symptoms.
    Never swallows messages containing actual symptoms (e.g. 'hi I have fever')
    or non-health prompts (e.g. 'hi write python code').
    """
    if not text:
        return None
    clean = re.sub(r'[?!.,]+$', '', text.strip().lower()).strip()
    if clean in GREETINGS_EXACT:
        return {
            'predicted_disease': 'Niramaya AI Health Assistant',
            'matched_symptoms': [],
            'description': (
                'Hello! I am your Niramaya AI Health Assistant. I am specialized strictly in '
                'symptom checking, health assessment, and clinical precautions (not general chat). '
                'Please enter any health symptoms you are currently experiencing (e.g., fever, '
                'headache, cough, stomach pain, dizziness, weakness) to receive clinical insights.'
            ),
            'precautions': [
                'Enter specific health symptoms you are experiencing in detail',
                'Track symptom onset, intensity, and duration',
                'Stay well-hydrated with clean water and ensure adequate rest',
                'Seek prompt medical consultation for severe or persistent conditions'
            ],
            'answer': (
                'Hello! I am your **Niramaya AI Health Assistant** (Symptom Checker Only — not a general chatbot).\n\n'
                'Please describe the **health symptoms** you are experiencing (e.g., *fever, headache, cough, sore throat, stomach pain, digestive issues, rash, dizziness*) to receive instant clinical guidance, home care, and precautions.'
            )
        }
    return None


def generate_any_health_response(prompt):
    """
    Answers ONLY medical symptom & health queries for Gemini endpoint.
    Enforces strict symptom-only domain restriction (never general ChatGPT chat).
    Uses live Gemini AI (if valid API key is configured) with Clinical Medical Engine fallback.
    """
    if not is_health_related(prompt):
        return get_non_health_refusal_message()

    # 1. Try Gemini Generative AI if a valid API key is configured
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            strict_prompt = (
                "You are Niramaya Health AI — a STRICT medical symptom checker, NOT a general-purpose chatbot like ChatGPT. "
                "RULES:\n"
                "1. ONLY respond to genuine human health symptoms, medical conditions, or clinical care.\n"
                "2. If the user's input is NOT a health symptom or medical condition, reply ONLY with: "
                "'⚠️ **Medical & Symptom Checker Domain Restriction:** I only analyze health symptoms and medical conditions. Please enter your health symptoms.'\n"
                "3. Never engage in casual conversation, coding, trivia, essays, jokes, or non-medical chat.\n"
                "4. Format your symptom analysis in clear structured markdown with these exact headings:\n"
                "**Condition / Clinical Assessment:**\n"
                "**Identified Symptoms & Health Inquiries:**\n"
                "**Medical Overview:**\n"
                "**Probable Causes & Contributing Factors:**\n"
                "**Dietary Recommendations & Home Care:**\n"
                "**Key Health Precautions & Self-Care:**\n"
                "**When to Seek Immediate Medical Attention (Red Flags):**\n"
                "End with an italic medical disclaimer.\n\n"
                f"User Symptom Input: {prompt}"
            )
            for model_id in ('gemini-2.0-flash', 'gemini-1.5-flash'):
                try:
                    model = genai.GenerativeModel(model_id)
                    resp = model.generate_content(
                        strict_prompt,
                        request_options={"timeout": 8.0}
                    )
                    if resp and getattr(resp, 'text', None):
                        return resp.text.strip()
                except Exception as inner_err:
                    print(f"Gemini model {model_id} fallback note: {inner_err}")
        except Exception as e:
            print(f"Gemini fast-fallback note: {e}")

    # 2. Clinical Medical Intelligence Engine (Deterministic, offline-capable, comprehensive)
    return generate_clinical_response(prompt)


@AI_bp.route("/askbiogpt", methods=["POST"])
def ask_biogpt():
    """Handles medical symptom assessment ONLY using BioGPT / Clinical Engine."""
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "question": "",
            "answer": "Please enter your health symptoms (e.g., fever, headache, cough, stomach pain) to receive clinical AI guidance."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"question": question, "answer": greet['answer']}), 200

    if not is_health_related(question):
        return jsonify({"question": question, "answer": get_non_health_refusal_message()}), 200

    # Strict clinical medical symptom answer
    ans = generate_clinical_response(question)
    return jsonify({"question": question, "answer": ans}), 200


@AI_bp.route("/askgemini", methods=["POST"])
def ask_gemini():
    """Handles medical symptom assessment ONLY using Gemini API / Clinical Medical Engine."""
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "question": "",
            "answer": "Please enter your health symptoms (e.g., fever, headache, cough, stomach pain) to receive clinical AI guidance."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"question": question, "answer": greet['answer']}), 200

    if not is_health_related(question):
        return jsonify({"question": question, "answer": get_non_health_refusal_message()}), 200

    answer = generate_any_health_response(question)
    return jsonify({"question": question, "answer": answer}), 200


@AI_bp.route('/asklrv1', methods=['POST'])
def askLRv1():
    """Handles disease prediction from symptoms ONLY (LRv1 endpoint)."""
    data = request.get_json(silent=True) or {}
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

    if not is_health_related(symptom_text):
        return jsonify({
            'predicted_disease': 'Non-Health Query',
            'matched_symptoms': [],
            'description': get_non_health_refusal_message()
        }), 200

    prediction = get_lrv1_prediction(symptom_text)
    return jsonify(prediction), 200


@AI_bp.route('/asklrv2', methods=['POST'])
def askLRv2():
    """Handles disease prediction from symptoms ONLY with precautions (LRv2 endpoint)."""
    data = request.get_json(silent=True) or {}
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

    if not is_health_related(symptom_text):
        return jsonify({
            'predicted_disease': 'Non-Health Query',
            'matched_symptoms': [],
            'description': get_non_health_refusal_message(),
            'precautions': [
                'Please ask questions strictly related to human health, symptoms, and medical wellness.',
                'Consult a qualified medical practitioner for formal diagnosis.'
            ]
        }), 200

    prediction = get_lrv2_prediction(symptom_text)
    return jsonify(prediction), 200
