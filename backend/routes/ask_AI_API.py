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
                    if k in ("GEMINI_API_KEY", "GROQ_API_KEY", "HF_API_KEY", "HF_TOKEN", "HUGGINGFACE_API_KEY") and v:
                        os.environ[k] = v
        except Exception:
            pass


# Cache when HF free serverless rejects legacy microsoft/biogpt (HTTP 400/404/410) so we don't waste latency
_hf_biogpt_unsupported = False


def _call_groq_biogpt(prompt_text: str, groq_key: str):
    """Calls Groq Live API (100% free tier, ultra-fast ~1s) for dedicated BioGPT biomedical inference."""
    for model_id in ("qwen/qwen3.8-27b", "allam-2-7b"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            body = json.dumps({
                "model": model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are BioGPT — a PubMed biomedical literature and clinical pathophysiology reference engine. "
                            "Write strictly objective medical-textbook pathophysiology and disease context. "
                            "Do NOT write conversational chat, home tips, or follow-up questions."
                        )
                    },
                    {"role": "user", "content": prompt_text}
                ],
                "temperature": 0.3,
                "max_tokens": 900
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "NiramayaHealthAI/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=14) as resp:
                if 200 <= resp.status < 300:
                    payload = json.loads(resp.read().decode("utf-8"))
                    choices = payload.get("choices") or []
                    if choices:
                        text = ((choices[0].get("message") or {}).get("content") or "").strip()
                        if text:
                            return text, model_id
        except urllib.error.HTTPError as he:
            err_snippet = ""
            try:
                err_snippet = he.read().decode("utf-8", errors="ignore")[:180]
            except Exception:
                pass
            print(f"Groq BioGPT ({model_id}) HTTP {he.code}: {err_snippet}")
            if he.code in (401, 403):
                break
        except Exception as e:
            print(f"Groq BioGPT ({model_id}) note: {e}")
    return None, None


def _fetch_live_pubmed_references(query_text: str, max_results: int = 2) -> list:
    """Fetches real live peer-reviewed PubMed citations from NCBI E-Utilities REST API (100% free, no key needed)."""
    import urllib.parse
    try:
        clean_q = re.sub(r"[^a-zA-Z0-9\s,-]", " ", query_text or "").strip()[:80]
        if not clean_q:
            return []
        term = urllib.parse.quote(f"({clean_q}) AND (pathophysiology OR clinical review)")
        esearch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={term}&retmax={max_results}&retmode=json&sort=relevance"
        req1 = urllib.request.Request(esearch, headers={"User-Agent": "NiramayaHealthAI/1.0"})
        with urllib.request.urlopen(req1, timeout=6) as r1:
            ids = json.loads(r1.read().decode("utf-8")).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        esummary = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
        req2 = urllib.request.Request(esummary, headers={"User-Agent": "NiramayaHealthAI/1.0"})
        with urllib.request.urlopen(req2, timeout=6) as r2:
            res = json.loads(r2.read().decode("utf-8")).get("result", {})
        refs = []
        for pmid in ids:
            item = res.get(pmid)
            if item and item.get("title"):
                title = item["title"].strip().rstrip(".")
                journal = item.get("fulljournalname") or item.get("source") or "PubMed"
                pubdate = item.get("pubdate") or ""
                refs.append(f"{title} — *{journal}* ({pubdate}, PMID: {pmid})")
        return refs
    except Exception as e:
        print(f"PubMed E-Utilities note: {e}")
        return []


def _call_gemini_rest(prompt_text: str, api_key: str, preferred_models=None, max_total_seconds: float = 18.0):
    """Calls Google Gemini official REST v1beta API over HTTPS with quick 503 retry & strict time budget."""
    import time
    deadline = time.monotonic() + max_total_seconds
    models_to_try = preferred_models or (
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
    )
    for model_id in models_to_try:
        for attempt in range(2):
            remaining = deadline - time.monotonic()
            if remaining < 3.0:
                return None, None
            per_call_timeout = min(10.0, remaining)
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
                body = json.dumps({
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "generationConfig": {"temperature": 0.35, "maxOutputTokens": 950}
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json", "User-Agent": "NiramayaHealthAI/1.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=per_call_timeout) as resp:
                    if 200 <= resp.status < 300:
                        payload = json.loads(resp.read().decode("utf-8"))
                        cands = payload.get("candidates") or []
                        if cands:
                            parts = (cands[0].get("content") or {}).get("parts") or []
                            text = "".join(p.get("text", "") for p in parts).strip()
                            if text:
                                return text, model_id
                break
            except urllib.error.HTTPError as he:
                err_snippet = ""
                try:
                    err_snippet = he.read().decode("utf-8", errors="ignore")[:180]
                except Exception:
                    pass
                print(f"Gemini REST ({model_id}) HTTP {he.code}: {err_snippet}")
                if he.code == 503 and attempt == 0 and (deadline - time.monotonic()) > 6.0:
                    time.sleep(1.2)
                    continue
                if he.code == 429:
                    return None, None
                break
            except Exception as e:
                print(f"Gemini REST ({model_id}) note: {e}")
                break
    return None, None


def _call_hf_biogpt(question: str, hf_token: str):
    """Calls Hugging Face Inference API for microsoft/biogpt over HTTPS."""
    global _hf_biogpt_unsupported
    if _hf_biogpt_unsupported:
        return None
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, list) and payload and payload[0].get("generated_text"):
                    txt = payload[0]["generated_text"].strip()
                    if len(txt) > 15:
                        return txt
    except urllib.error.HTTPError as he:
        err_body = ""
        try:
            err_body = he.read().decode("utf-8", errors="ignore")[:180]
        except Exception:
            pass
        if he.code in (400, 404, 410):
            _hf_biogpt_unsupported = True
        print(f"HuggingFace BioGPT API HTTP {he.code}: {err_body}")
    except Exception as e:
        print(f"HuggingFace BioGPT API note: {e}")
    return None


def run_biogpt_inference(question: str) -> dict:
    """Runs BioGPT unique responsibility: biomedical knowledge, medical explanation & disease context."""
    _reload_ai_dotenv()

    bio_prompt = (
        "Act strictly as BioGPT — a PubMed biomedical literature and clinical pathophysiology reference engine. "
        "Do NOT write conversational chat, home tips, lifestyle advice, or follow-up questions. "
        "Provide concise, medically accurate textbook-style biomedical knowledge ONLY with these exact headings:\n"
        "**Condition / Clinical Assessment (Biomedical):**\n"
        "**Organ System & Symptom-Related Context:**\n"
        "**Pathophysiology & Medical Explanation:**\n"
        "**Disease Information (Reference Medical Knowledge):** (discuss 2-3 clinically relevant conditions associated with these symptoms)\n"
        "**Biomedical Etiology & Underlying Mechanisms:** (3-4 bullet points starting with '- ')\n"
        "End with a short italic medical reference disclaimer wrapped in *(...)*.\n\n"
        f"Clinical Symptoms / Query: {question}"
    )

    # 1. Dedicated ultra-fast Groq Live API (100% free tier, completely separate from Google Gemini) if GROQ_API_KEY is set
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if groq_key:
        groq_bio, groq_model = _call_groq_biogpt(bio_prompt, groq_key)
        if groq_bio:
            return {
                "model": "BioGPT",
                "role": "Biomedical Knowledge & Medical Explanations",
                "source": f"BioGPT Biomedical Engine — Live Groq API ({groq_model})",
                "answer": groq_bio
            }

    # 2. Live Biomedical AI API via Google Gemini (with quick 503 retry, skipping dead HF free microsoft/biogpt endpoint)
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if api_key and not api_key.startswith("AIzaSyCxcCXwbFRd") and len(api_key) > 20:
        live_bio, model_id = _call_gemini_rest(
            bio_prompt,
            api_key,
            preferred_models=("gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest")
        )
        if live_bio:
            return {
                "model": "BioGPT",
                "role": "Biomedical Knowledge & Medical Explanations",
                "source": f"BioGPT Biomedical Mode — Live AI API ({model_id})",
                "answer": live_bio
            }

    # 3. Try local cached microsoft/biogpt weights if installed
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

    if local_text:
        return generate_biogpt_response(question, local_biogpt_text=local_text)

    # 4. Online PubMed NCBI Live Biomedical API enrichment (100% free, no API key needed) + Clinical Corpus
    fallback_res = generate_biogpt_response(question)
    pubmed_refs = _fetch_live_pubmed_references(question, max_results=2)
    if pubmed_refs:
        refs_md = "\n".join(f"- {r}" for r in pubmed_refs)
        fallback_res["answer"] = fallback_res["answer"].replace(
            "\n\n*(Biomedical Reference Notice:",
            f"\n\n**Live PubMed Literature References (NCBI Online API):**\n{refs_md}\n\n*(Biomedical Reference Notice:"
        )
        fallback_res["source"] = "PubMed Live Biomedical API (NCBI) + Clinical Reference Corpus"
    return fallback_res


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
    groq_key = (os.environ.get("GROQ_API_KEY") or "").strip()
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
        "biogpt_groq_api_configured": bool(groq_key),
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
