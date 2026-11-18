from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
import re
import json
import urllib.request
import urllib.error

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


def _reload_ai_dotenv():
    """Reloads .env dynamically so newly added GEMINI_API_KEY / HF_API_KEY work immediately."""
    routes_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(routes_dir)
    project_root = os.path.dirname(backend_dir)
    for env_path in (os.path.join(project_root, ".env"), os.path.join(backend_dir, ".env")):
        if not os.path.isfile(env_path):
            continue
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k in ("GEMINI_API_KEY", "HF_API_KEY", "HF_TOKEN", "HUGGINGFACE_API_KEY") and v:
                        os.environ[k] = v
        except Exception:
            pass


def _call_gemini_rest(prompt_text: str, api_key: str):
    """Calls Google Gemini official REST v1beta API directly over HTTPS (works with modern Gemini 2.0/2.5 keys)."""
    for model_id in ("gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
            body = json.dumps({
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 900}
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "NiramayaHealthAI/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if 200 <= resp.status < 300:
                    payload = json.loads(resp.read().decode("utf-8"))
                    cands = payload.get("candidates") or []
                    if cands:
                        parts = (cands[0].get("content") or {}).get("parts") or []
                        text = "".join(p.get("text", "") for p in parts).strip()
                        if text:
                            return text, model_id
        except Exception as e:
            print(f"Gemini REST ({model_id}) note: {e}")
    return None, None


def _call_hf_biogpt(question: str, hf_token: str):
    """Calls Hugging Face Inference API for microsoft/biogpt over HTTPS."""
    try:
        url = "https://router.huggingface.co/hf-inference/models/microsoft/biogpt"
        prompt = f"Clinical biomedical pathophysiology and disease context for {question}:"
        body = json.dumps({
            "inputs": prompt,
            "parameters": {"max_new_tokens": 110, "return_full_text": False}
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json",
                "User-Agent": "NiramayaHealthAI/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            if 200 <= resp.status < 300:
                payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, list) and payload and payload[0].get("generated_text"):
                    txt = payload[0]["generated_text"].strip()
                    if len(txt) > 15:
                        return txt
    except Exception as e:
        print(f"HuggingFace BioGPT API note: {e}")
    return None


def run_biogpt_inference(question: str) -> dict:
    """Runs BioGPT unique responsibility: biomedical knowledge, medical explanation & disease context."""
    _reload_ai_dotenv()
    local_text = None

    # 1. Try Hugging Face Inference API for microsoft/biogpt if HF token is configured
    hf_token = (os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY") or "").strip()
    if hf_token:
        hf_text = _call_hf_biogpt(question, hf_token)
        if hf_text:
            res = generate_biogpt_response(question, local_biogpt_text=hf_text)
            res["source"] = "Microsoft BioGPT (Hugging Face Live API) + Clinical Reference Corpus"
            return res

    # 2. Try local cached microsoft/biogpt weights if installed
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

    if local_text:
        return generate_biogpt_response(question, local_biogpt_text=local_text)

    # 3. If live GEMINI_API_KEY is configured, generate live biomedical pathophysiology (strictly biomedical role, distinct from Gemini Health Assistant!)
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
        bio_prompt = (
            "Act strictly as BioGPT — a PubMed biomedical literature and clinical pathophysiology reference engine. "
            "Do NOT write conversational chat, home tips, or follow-up questions. "
            "Provide concise, accurate medical-textbook style biomedical knowledge ONLY with these exact headings:\n"
            "**Condition / Clinical Assessment (Biomedical):**\n"
            "**Organ System & Symptom-Related Context:**\n"
            "**Pathophysiology & Medical Explanation:**\n"
            "**Disease Information (Reference Medical Knowledge):**\n"
            "**Biomedical Etiology & Underlying Mechanisms:**\n"
            "End with a short italic medical reference disclaimer.\n\n"
            f"Clinical Symptoms / Query: {question}"
        )
        live_bio, model_id = _call_gemini_rest(bio_prompt, api_key)
        if live_bio:
            return {
                "model": "BioGPT",
                "role": "Biomedical Knowledge & Medical Explanations",
                "source": f"Live Biomedical LLM Engine ({model_id})",
                "answer": live_bio
            }

    return generate_biogpt_response(question)


def run_gemini_inference(question: str) -> dict:
    """
    Runs Gemini unique responsibility: natural-language AI health assistant
    providing understandable health guidance, general precautions, and follow-up questions.
    """
    _reload_ai_dotenv()
    if not is_health_related(question):
        return {
            "model": "Gemini",
            "role": "AI Health Assistant — Guidance, Precautions & Follow-Up Questions",
            "source": "Domain Guardrail",
            "follow_up_questions": [],
            "answer": get_non_health_refusal_message()
        }

    # Try live Google Gemini REST API directly when valid GEMINI_API_KEY is configured
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
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
        text, model_id = _call_gemini_rest(assistant_prompt, api_key)
        if text:
            follow_ups = [
                line.lstrip('-*• 0123456789.)').strip()
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

    # Deterministic structured Health Assistant engine (distinct from BioGPT)
    return generate_gemini_guidance(question)


@AI_bp.route("/api/models/status", methods=["GET"])
def models_status():
    """Diagnostic status of all 4 AI/ML models and database engine (no secrets exposed)."""
    _reload_ai_dotenv()
    from medical_engine import lr_model, rf_model, symptom_features, symptom_mlb
    from db_config import get_db_connection
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    hf_key = (os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY") or "").strip()
    db_type = "unknown"
    try:
        c = get_db_connection()
        db_type = "sqlite_ephemeral" if c.__class__.__name__ == "SQLiteConnWrapper" else "postgresql_persistent"
        c.close()
    except Exception:
        pass
    return jsonify({
        "gemini_live_api_configured": bool(api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20),
        "biogpt_hf_api_configured": bool(hf_key),
        "lrv1_loaded": lr_model is not None,
        "lrv1_features": len(symptom_features),
        "lrv2_loaded": rf_model is not None,
        "lrv2_features": len(symptom_mlb.classes_) if symptom_mlb is not None else 0,
        "database_engine": db_type
    }), 200


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
