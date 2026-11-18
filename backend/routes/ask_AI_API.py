from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
import re

# Import the Differentiated 4-Model Medical Intelligence Engine
from medical_engine import (
    generate_biogpt_response,
    generate_gemini_guidance,
    generate_clinical_response,
    get_lrv1_prediction,
    get_lrv2_prediction,
    compare_lrv1_and_lrv2,
    extract_symptoms_from_text,
    SYMPTOM_DISPLAY,
    is_health_related,
    get_non_health_refusal_message
)

# Create a Blueprint for AI model routes
AI_bp = Blueprint('health_AI', __name__)
CORS(AI_bp)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# BioGPT Local Transformer Generator (Lazy Loaded only if cached locally)
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


def run_biogpt_inference(question: str) -> dict:
    """Runs BioGPT unique responsibility: biomedical knowledge, medical explanation & disease context."""
    local_text = None
    gen = get_biogpt_generator()
    if gen is not None:
        try:
            prompt = f"Clinical biomedical context for symptoms ({question}):"
            out = gen(prompt, max_new_tokens=80, num_return_sequences=1, do_sample=False)
            if out and isinstance(out, list) and out[0].get("generated_text"):
                raw = out[0]["generated_text"].replace(prompt, "", 1).strip()
                if len(raw) > 20:
                    local_text = raw
        except Exception as e:
            print(f"BioGPT generation note: {e}")
    return generate_biogpt_response(question, local_biogpt_text=local_text)


def run_gemini_inference(question: str) -> dict:
    """
    Runs Gemini unique responsibility: natural-language AI health assistant
    providing understandable health guidance, general precautions, and follow-up questions.
    """
    if not is_health_related(question):
        return {
            "model": "Gemini",
            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
            "source": "Domain Guardrail",
            "follow_up_questions": [],
            "answer": get_non_health_refusal_message()
        }

    # Try live Google Gemini API when valid key is configured
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            assistant_prompt = (
                "You are Gemini inside Niramaya Health AI — acting strictly as a supportive AI Health Assistant "
                "(NOT a general ChatGPT chatbot and NOT a statistical disease classifier). "
                "RULES:\n"
                "1. ONLY answer genuine human health symptoms or medical concerns. Refuse non-health queries.\n"
                "2. Explain things in warm, clear, everyday language a patient can easily understand.\n"
                "3. Do NOT fabricate disease probability percentages.\n"
                "4. Structure your response with these EXACT headings:\n"
                "**Understanding Your Symptoms (Health Assistant Guidance):**\n"
                "**Practical Self-Care & Everyday Health Guidance:**\n"
                "**General Precautions:**\n"
                "**When to Seek Prompt Medical Care:**\n"
                "**Helpful Follow-Up Questions to Clarify Your Symptoms:** (list 3-4 specific follow-up questions)\n"
                "End with a brief italic disclaimer.\n\n"
                f"Patient Symptom Description: {question}"
            )
            for model_id in ('gemini-2.0-flash', 'gemini-1.5-flash'):
                try:
                    model = genai.GenerativeModel(model_id)
                    resp = model.generate_content(
                        assistant_prompt,
                        request_options={"timeout": 8.0}
                    )
                    if resp and getattr(resp, 'text', None):
                        text = resp.text.strip()
                        # Extract bullet follow-up questions if present
                        follow_ups = [
                            line.lstrip('-*• ').strip()
                            for line in text.splitlines()
                            if line.strip().endswith('?')
                        ][:4]
                        return {
                            "model": "Gemini",
                            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
                            "source": f"Google Gemini Live API ({model_id})",
                            "follow_up_questions": follow_ups,
                            "answer": text
                        }
                except Exception as inner_err:
                    print(f"Gemini model {model_id} fallback note: {inner_err}")
        except Exception as e:
            print(f"Gemini fast-fallback note: {e}")

    # Deterministic structured Health Assistant engine (distinct from BioGPT)
    return generate_gemini_guidance(question)


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
            'is_greeting': True,
            'predicted_disease': 'Niramaya AI Health Assistant',
            'matched_symptoms': [],
            'top_predictions': [],
            'top_probability': 0.0,
            'description': (
                'Hello! I am your Niramaya AI Health Assistant. I am specialized strictly in '
                'symptom checking, health assessment, and clinical precautions (not general chat). '
                'Please enter any health symptoms you are currently experiencing (e.g., fever, '
                'headache, cough, stomach pain, dizziness, weakness) to run all 4 specialized models.'
            ),
            'precautions': [
                'Enter specific health symptoms you are experiencing in detail',
                'Track symptom onset, intensity, and duration',
                'Stay well-hydrated with clean water and ensure adequate rest',
                'Seek prompt medical consultation for severe or persistent conditions'
            ],
            'answer': (
                'Hello! I am your **Niramaya AI Health Assistant** (Symptom Checker Only — not a general chatbot).\n\n'
                'Please describe the **health symptoms** you are experiencing (e.g., *fever, headache, cough, sore throat, stomach pain, rash, dizziness*) '
                'to receive specialized analysis from **BioGPT**, **Gemini**, **LRv1**, and **LRv2**.'
            )
        }
    return None


@AI_bp.route("/askbiogpt", methods=["POST"])
def ask_biogpt():
    """BioGPT: Biomedical knowledge, medical explanations, disease information & symptom context."""
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "model": "BioGPT",
            "role": "Biomedical Knowledge & Medical Explanations",
            "question": "",
            "answer": "Please enter your health symptoms (e.g., fever, headache, cough, stomach pain) for biomedical explanation and context."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"model": "BioGPT", "question": question, "answer": greet['answer']}), 200

    if not is_health_related(question):
        return jsonify({"model": "BioGPT", "question": question, "answer": get_non_health_refusal_message()}), 200

    result = run_biogpt_inference(question)
    result["question"] = question
    return jsonify(result), 200


@AI_bp.route("/askgemini", methods=["POST"])
def ask_gemini():
    """Gemini: Natural-language AI health assistant with guidance, general precautions & follow-up questions."""
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "model": "Gemini",
            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
            "question": "",
            "follow_up_questions": [],
            "answer": "Please describe your health symptoms so I can provide clear guidance, precautions, and follow-up questions."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({"model": "Gemini", "question": question, "answer": greet['answer']}), 200

    if not is_health_related(question):
        return jsonify({"model": "Gemini", "question": question, "answer": get_non_health_refusal_message()}), 200

    result = run_gemini_inference(question)
    result["question"] = question
    return jsonify(result), 200


@AI_bp.route('/asklrv1', methods=['POST'])
def askLRv1():
    """LRv1: Independent Logistic Regression disease predictions & real predict_proba() probabilities."""
    data = request.get_json(silent=True) or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'model': 'LRv1',
            'predicted_disease': 'Input Required',
            'top_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms (e.g. fever, headache, cough, vomiting) to run LRv1 disease prediction.'
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    if not is_health_related(symptom_text):
        return jsonify({
            'model': 'LRv1',
            'predicted_disease': 'Non-Health Query',
            'top_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': get_non_health_refusal_message()
        }), 200

    prediction = get_lrv1_prediction(symptom_text)
    return jsonify(prediction), 200


@AI_bp.route('/asklrv2', methods=['POST'])
def askLRv2():
    """LRv2: Independent Enhanced Random Forest disease predictions, real probabilities & precautions."""
    data = request.get_json(silent=True) or {}
    symptom_text = (data.get("symptoms") or data.get("question") or "").strip()
    if not symptom_text:
        return jsonify({
            'model': 'LRv2',
            'predicted_disease': 'Input Required',
            'top_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': 'Please enter your health symptoms to run LRv2 enhanced disease prediction and get precaution advice.',
            'precautions': ['Enter symptom names like fever, headache, body pain, nausea, loose motion']
        }), 200

    greet = check_greeting_response(symptom_text)
    if greet:
        return jsonify(greet), 200

    if not is_health_related(symptom_text):
        return jsonify({
            'model': 'LRv2',
            'predicted_disease': 'Non-Health Query',
            'top_probability': 0.0,
            'top_predictions': [],
            'matched_symptoms': [],
            'description': get_non_health_refusal_message(),
            'precautions': [
                'Please ask questions strictly related to human health, symptoms, and medical wellness.',
                'Consult a qualified medical practitioner for formal diagnosis.'
            ]
        }), 200

    prediction = get_lrv2_prediction(symptom_text)
    return jsonify(prediction), 200


@AI_bp.route('/askall', methods=['POST'])
def ask_all_models():
    """
    Runs ALL FOUR models independently (BioGPT, Gemini, LRv1, LRv2)
    plus the LRv1 vs LRv2 Comparison & Agreement Analysis.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("symptoms") or "").strip()
    if not question:
        return jsonify({
            "question": "",
            "is_health_related": False,
            "message": "Please enter your health symptoms (e.g., fever, headache, cough, vomiting, skin rash) to analyze across all four models."
        }), 200

    greet = check_greeting_response(question)
    if greet:
        return jsonify({
            "question": question,
            "is_greeting": True,
            "answer": greet["answer"]
        }), 200

    if not is_health_related(question):
        return jsonify({
            "question": question,
            "is_health_related": False,
            "answer": get_non_health_refusal_message()
        }), 200

    biogpt_res = run_biogpt_inference(question)
    gemini_res = run_gemini_inference(question)
    lrv1_res = get_lrv1_prediction(question)
    lrv2_res = get_lrv2_prediction(question)
    comparison_res = compare_lrv1_and_lrv2(lrv1_res, lrv2_res)

    return jsonify({
        "question": question,
        "is_health_related": True,
        "biogpt": biogpt_res,
        "gemini": gemini_res,
        "lrv1": lrv1_res,
        "lrv2": lrv2_res,
        "comparison": comparison_res
    }), 200
