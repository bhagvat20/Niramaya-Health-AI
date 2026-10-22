from flask import Blueprint, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
import joblib
import os
import pandas as pd

# Create a Blueprint for disease predictor routes
AI_bp = Blueprint('health_AI', __name__)
CORS(AI_bp)

# Lazy loading BioGPT Model and Tokenizer to avoid startup delays or scope collision
biogpt_generator = None

def get_biogpt_generator():
    global biogpt_generator
    if biogpt_generator is None:
        from transformers import pipeline, BioGptTokenizer, BioGptForCausalLM
        model_name = "microsoft/biogpt"
        tokenizer = BioGptTokenizer.from_pretrained(model_name)
        biogpt_model = BioGptForCausalLM.from_pretrained(model_name)
        biogpt_generator = pipeline("text-generation", model=biogpt_model, tokenizer=tokenizer)
    return biogpt_generator

def generate_medical_response(prompt, max_length=1000):
    """Generates a long medical response using BioGPT pipeline, matching Colab."""
    generator = get_biogpt_generator()
    responses = generator(
        prompt,
        max_length=max_length,
        num_return_sequences=1,
        do_sample=True
    )
    full_response = " ".join([resp["generated_text"] for resp in responses])
    return full_response

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCxcCXwbFRdEz6f92mXlVd1dBw7fqCQWew"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

def generate_gemini_response(prompt):
    """Generates a response using the Gemini API."""
    try:
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return str(e)

@AI_bp.route("/askbiogpt", methods=["POST"])
def ask_biogpt():
    """Handles user medical questions and generates answers using BioGPT."""
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "The 'question' field is required."}), 400

    try:
        answer = generate_medical_response(question)
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@AI_bp.route("/askgemini", methods=["POST"])
def ask_gemini():
    """Handles user medical questions and generates answers using Gemini API."""
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "The 'question' field is required."}), 400

    try:
        answer = generate_gemini_response(question)
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LR (Logistic Regression Model Setup)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model_LR', 'logistic_regression_model.pkl')
SYMPTOM_FEATURES_PATH = os.path.join(BASE_DIR, 'model_LR', 'symptom_features.pkl')
DESC_PATH = os.path.join(BASE_DIR, 'model_LR', 'Symptom_Description.csv')
PRECAUTION_PATH = os.path.join(BASE_DIR, 'model_LR', 'Symptom_Precaution.csv')

# Load model and symptom features
lr_model = joblib.load(MODEL_PATH)
symptom_features = joblib.load(SYMPTOM_FEATURES_PATH)
desc_df = pd.read_csv(DESC_PATH)
prec_df = pd.read_csv(PRECAUTION_PATH)

# Normalize disease values in description and precaution dataframes
desc_df['disease'] = desc_df['disease'].astype(str).str.lower().str.strip()
prec_df['disease'] = prec_df['disease'].astype(str).str.lower().str.strip()

def predict_disease_from_symptoms(symptoms_list):
    # Clean user input
    symptoms_list = [sym.strip().lower().replace(' ', '_') for sym in symptoms_list]

    # Create binary input vector
    input_vector = [1 if symptom in symptoms_list else 0 for symptom in symptom_features]

    # Convert to DataFrame with correct feature names
    input_df = pd.DataFrame([input_vector], columns=symptom_features)

    # Predict using the model
    prediction = lr_model.predict(input_df)
    return prediction[0]

@AI_bp.route('/asklrv1', methods=['POST'])
def askLRv1():
    data = request.get_json() or {}
    symptom_text = data.get("symptoms", "")

    if not symptom_text or not isinstance(symptom_text, str):
        return jsonify({'error': 'Please provide symptoms as a string.'}), 400

    # Convert to list
    symptoms_list = symptom_text.strip().lower().split()
    
    predicted_disease = predict_disease_from_symptoms(symptoms_list)
    description_row = desc_df[desc_df['disease'].str.lower() == str(predicted_disease).lower()]
    description = description_row['description'].values[0] if not description_row.empty else 'No description found.'
    return jsonify({
        'predicted_disease': predicted_disease,
        'description': description
    })

# API route for lrv2
@AI_bp.route('/asklrv2', methods=['POST'])
def askLRv2():
    data = request.get_json() or {}
    symptom_text = data.get("symptoms", "")

    if not symptom_text or not isinstance(symptom_text, str):
        return jsonify({'error': 'Please provide symptoms as a string.'}), 400

    # Convert to list
    symptoms_list = symptom_text.strip().lower().split()
    
    predicted_disease = predict_disease_from_symptoms(symptoms_list)
    description_row = desc_df[desc_df['disease'].str.lower() == str(predicted_disease).lower()]
    description = description_row['description'].values[0] if not description_row.empty else 'No description found.'
    precaution_row = prec_df[prec_df['disease'].str.lower() == str(predicted_disease).lower()]
    precautions = []
    if not precaution_row.empty:
        row = precaution_row.iloc[0]
        precautions = [v for k, v in row.items() if k.startswith('precaution') and pd.notna(v)]
    
    return jsonify({
        'predicted_disease': predicted_disease,
        'description': description,
        'precautions': precautions
    })


