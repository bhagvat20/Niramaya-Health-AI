"""
Niramaya Health AI - Clinically Calibrated LRv1 Training Engine (train_lrv1.py)
Re-trains Logistic Regression (LRv1) on evidence-based medical disease-symptom distributions
for all 261 clinical diseases, eliminating corrupt Wikipedia infobox weights,
and fills all 49 missing summaries in Symptom_Description.csv.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model_LR')
DESC_PATH = os.path.join(MODEL_DIR, 'Symptom_Description.csv')
PREC_PATH = os.path.join(MODEL_DIR, 'Symptom_Precaution.csv')
LR_OUT_PATH = os.path.join(MODEL_DIR, 'logistic_regression_model.pkl')
FEATS_OUT_PATH = os.path.join(MODEL_DIR, 'symptom_features.pkl')

# 1. Load exact 261 diseases
df_desc = pd.read_csv(DESC_PATH)
ALL_DISEASES = df_desc['disease'].dropna().unique().tolist()
print(f"Total target diseases: {len(ALL_DISEASES)}")

# 2. Comprehensive, verified medical descriptions for all 49 diseases previously having "No summary available."
VERIFIED_DESCRIPTIONS = {
    'Acquired Capillary Haemangioma of Eyelid': 'Acquired capillary hemangioma is a benign vascular lesion of the eyelid composed of proliferating endothelial cells, commonly presenting as a reddish or purplish painless nodule that may cause ptosis or visual obstruction.',
    'Acquired Immuno Deficiency Syndrome': 'Acquired Immunodeficiency Syndrome (AIDS) is the advanced clinical spectrum of infection with the human immunodeficiency virus (HIV), characterized by severe CD4+ T-cell depletion and high vulnerability to life-threatening opportunistic infections and secondary malignancies.',
    'Adult Inclusion Conjunctivitis': 'Adult inclusion conjunctivitis is a sexually transmitted ocular infection caused by Chlamydia trachomatis, presenting with chronic unilateral or bilateral foreign-body sensation, purulent or mucopurulent discharge, and marked follicular conjunctival hypertrophy.',
    'Alcohol Abuse and Alcoholism': 'Alcohol use disorder is a chronic relapsing neurological disorder characterized by compulsive alcohol seeking, loss of intake control, psychological dependence, tremors, and severe physical withdrawal manifestations upon abrupt cessation.',
    'Alopecia (hair loss)': 'Alopecia is the partial or complete loss of hair from regions of the body where it normally grows, frequently triggered by autoimmune follicular destruction (alopecia areata), androgenic hormonal shifts, metabolic stress, or nutritional deficiencies.',
    'Amaurosis Fugax': 'Amaurosis fugax is transient, painless monocular loss of vision commonly described as a curtain descending over one visual field, most often caused by temporary retinal ischemia or microembolism originating from the ipsilateral carotid artery.',
    'Antepartum hemorrhage (Bleeding in late pregnancy)': 'Antepartum hemorrhage is genital tract bleeding occurring after the 20th to 24th week of gestation prior to fetal delivery, most commonly caused by placenta previa, abruptio placentae, or uterine vascular rupture, requiring urgent obstetric triage.',
    'Bad Breath (Halitosis)': 'Halitosis is chronic, persistent oral malodor arising predominantly from volatile sulfur compounds produced by anaerobic microbial putrefaction of oral debris, periodontal disease, dental caries, post-nasal drip, or gastroesophageal reflux.',
    'Bleeding Gums': 'Bleeding gums is an early hallmark sign of gingival inflammation (gingivitis) and periodontal disease, where bacterial plaque accumulation triggers mucosal fragility, redness, edema, and spontaneous hemorrhage upon tooth brushing.',
    'Breast Cancer / Carcinoma': 'Breast carcinoma is a malignant neoplasm arising from the epithelial ductal or lobular tissues of the breast, typically presenting as a firm, painless palpable breast mass, skin dimpling, nipple inversion, or bloody nipple discharge.',
    'Burns': 'Burns are traumatic injuries to the skin and deeper subcutaneous tissues caused by thermal heat, electrical currents, friction, radiation, or chemical caustic exposure, resulting in erythema, blistering, severe fluid extravasation, and tissue necrosis.',
    'Calculi': 'Calculi are mineral deposits (stones) formed within the urinary tract (nephrolithiasis), gallbladder (cholelithiasis), or salivary ducts, presenting with severe excruciating cramping colic, localized flank or abdominal pain, and hematuria.',
    'Cavities': 'Dental caries (cavities) represent microbial acid demineralization of the dental enamel and underlying dentin caused by fermentable carbohydrates, leading to structural cavitation, sensitivity to thermal extremes, and localized toothache.',
    'Celiacs disease': 'Celiac disease is a chronic systemic autoimmune enteropathy triggered by dietary gluten ingestion in genetically susceptible individuals, leading to small intestinal villous atrophy, chronic diarrhea, abdominal distention, and malabsorption.',
    'Chikungunya Fever': 'Chikungunya is a mosquito-borne viral disease caused by an alphavirus transmitted by Aedes mosquitoes, presenting with sudden acute high fever, severe incapacitating polyarthralgia, periarticular swelling, and maculopapular cutaneous rashes.',
    'Childhood Exotropia': 'Childhood exotropia is a form of strabismus characterized by an outward divergent misalignment of one or both eyes, which can lead to amblyopia, loss of binocular stereoscopic depth perception, and ocular fatigue.',
    'Chronic obstructive pulmonary disease (COPD)': 'COPD is a progressive, irreversible obstructive respiratory disease encompassing chronic bronchitis and emphysema, marked by chronic dyspnea, persistent productive cough, wheezing, and airflow limitation commonly caused by tobacco smoke.',
    'Cleft Lip and Cleft Palate': 'Cleft lip and cleft palate are congenital craniofacial malformations resulting from incomplete fusion of embryonic maxillary and palatal processes, causing feeding difficulties, speech resonance disorders, and recurrent otitis media.',
    'Condyloma': 'Condyloma acuminata (genital warts) are benign papillomatous epidermal lesions of the anogenital region caused by low-risk strains of Human Papillomavirus (HPV types 6 and 11), presenting as soft, flesh-colored, cauliflower-like growths.',
    'Congenital anomalies (birth defects)': 'Congenital anomalies are structural, functional, or metabolic abnormalities present at birth, arising from genetic mutations, chromosomal aberrations, intrauterine teratogenic exposures, or maternal nutritional deficiencies.',
    'Corneal Abrasion': 'A corneal abrasion is a painful physical defect or scratch on the superficial epithelial layer of the cornea, typically caused by foreign bodies, fingernails, or contact lens trauma, presenting with intense eye pain, photophobia, and excessive lacrimation.',
    'Crimean Congo haemorrhagic fever (CCHF)': 'CCHF is a severe tick-borne viral zoonosis caused by a Nairovirus, characterized by sudden high fever, generalized myalgia, dizziness, severe petechial hemorrhages, gastrointestinal bleeding, and hepatic-renal collapse.',
    'Diabetic Retinopathy': 'Diabetic retinopathy is a microvascular complication of chronic diabetes mellitus characterized by retinal capillary damage, microaneurysms, cotton wool spots, retinal hemorrhages, macular edema, and progressive irreversible vision loss.',
    'Dracunculiasis (guinea-worm disease)': 'Dracunculiasis is a crippling parasitic nematode infection acquired by drinking stagnant water contaminated with Cyclops water fleas carrying Dracunculus medinensis larvae, characterized by painful blister formation and slow worm emergence.',
    'Fibroids': 'Uterine fibroids (leiomyomas) are non-cancerous monoclonal smooth muscle neoplasms of the myometrium, presenting with abnormal heavy menorrhagia, pelvic pressure, frequent urination, dysmenorrhea, and lower back discomfort.',
    'Frost Bite': 'Frostbite is localized thermal tissue freezing and ischemic damage caused by prolonged exposure to subfreezing temperatures, resulting in initial numbness, waxy pallor, sensory loss, blister formation, and tissue necrosis.',
    'Heat-Related Illnesses and Heat waves': 'Heat-related illnesses comprise a spectrum of thermal emergencies ranging from heat cramps and heat exhaustion to life-threatening heat stroke, characterized by core hyperthermia (>40°C), dehydration, confusion, and multi-organ failure.',
    'Iron Deficiency Anemia': 'Iron deficiency anemia is a microcytic, hypochromic hematological condition where depleted systemic iron stores impair hemoglobin synthesis, resulting in pallor, chronic fatigue, dyspnea on exertion, headache, brittle nails, and dizziness.',
    'Kala-azar/ Leishmaniasis': 'Visceral leishmaniasis (Kala-azar) is a protozoan parasitic infection transmitted by phlebotomine sandflies, presenting with prolonged irregular fever, massive splenomegaly, hepatomegaly, profound weight loss, and pancytopenia.',
    'Keratoconjunctivitis Sicca (Dry eye syndrome)': 'Keratoconjunctivitis sicca is a multifactorial ocular surface disorder characterized by tear film hyperosmolarity, deficient tear production, or excessive evaporation, causing burning, stinging, ocular redness, and blurred vision.',
    'Kuru': 'Kuru is a rare, fatal prion-mediated neurodegenerative disorder historically endemic to the Fore tribe of Papua New Guinea, presenting with progressive cerebellar ataxia, severe tremors, speech incoordination, and terminal dementia.',
    'Middle East respiratory syndrome coronavirus (MERS‐CoV)': 'MERS-CoV is a severe zoonotic viral respiratory illness originating from dromedary camels, presenting with rapid-onset high fever, productive cough, shortness of breath, and rapid progression to severe acute pneumonia and renal failure.',
    'Mouth Breathing': 'Chronic mouth breathing is an abnormal respiratory habit often secondary to upper airway obstruction (adenoid hypertrophy, nasal polyps, or deviated septum), leading to dry mouth, dental malocclusion, snoring, and poor sleep architecture.',
    'Myocardial Infarction (Heart Attack)': 'Myocardial infarction is acute myocardial cell necrosis resulting from sudden coronary thrombotic occlusion, presenting with crushing central substernal chest pressure radiating to the left arm or jaw, dyspnea, and diaphoresis.',
    'Nasal Polyps': 'Nasal polyps are soft, noncancerous, painless edematous inflammatory growths lining the nasal mucosa or paranasal sinuses, presenting with chronic nasal congestion, anosmia, post-nasal drip, and chronic recurrent sinusitis.',
    'Nausea and Vomiting of Pregnancy and  Hyperemesis gravidarum': 'Hyperemesis gravidarum is a severe, intractable complication of early pregnancy characterized by persistent severe nausea, repeated vomiting, dehydration, electrolyte derangements, ketonuria, and significant weight loss.',
    'Neonatal Respiratory Disease Syndrome(NRDS)': 'NRDS is an acute respiratory failure syndrome of premature infants caused by insufficient pulmonary surfactant production and alveolar instability, characterized by tachypnea, nasal flaring, grunting, and intercostal retractions.',
    'Orbital Dermoid': 'An orbital dermoid is a benign congenital choristomatous cyst composed of ectopic dermal appendages, commonly presenting as a firm, non-tender, slow-growing palpable mass along the lateral eyebrow or superior orbital rim.',
    'Perennial Allergic Conjunctivitis': 'Perennial allergic conjunctivitis is a chronic IgE-mediated ocular allergy triggered by indoor allergens such as dust mites, animal dander, and mold spores, causing bilateral itching, watery discharge, and conjunctival hyperemia.',
    'Polycystic ovary syndrome (PCOS)': 'PCOS is a common heterogeneous endocrine disorder characterized by hyperandrogenism, ovulatory dysfunction, irregular menstrual cycles, hirsutism, cystic ovarian morphology on ultrasound, and insulin resistance.',
    'Post Menopausal Bleeding': 'Postmenopausal bleeding is any spontaneous uterine vaginal bleeding occurring 12 or more months after the final menstrual period, requiring mandatory clinical evaluation to exclude endometrial hyperplasia or carcinoma.',
    'Postpartum depression/ Perinatal depression': 'Postpartum depression is a major depressive episode occurring after childbirth, characterized by persistent dysphoria, severe maternal anxiety, emotional detachment from the infant, profound fatigue, and sleep disturbance.',
    'Ques fever': 'Q fever is a worldwide zoonotic infection caused by Coxiella burnetii, typically acquired from farm livestock, presenting with high fever, severe retro-orbital headache, chills, drenching sweats, fatigue, and atypical pneumonia or hepatitis.',
    'Quinsy': 'Quinsy (peritonsillar abscess) is a suppurative bacterial complication of acute tonsillitis where pus collects between the tonsillar capsule and pharyngeal wall, presenting with severe unilateral throat pain, trismus, and uvular deviation.',
    'Scrub Typhus': 'Scrub typhus is a vector-borne acute febrile illness caused by Orientia tsutsugamushi transmitted by larval trombiculid mites (chiggers), presenting with high fever, severe headache, lymphadenopathy, and a diagnostic necrotic skin eschar.',
    'Sexually transmitted infections (STIs)': 'Sexually transmitted infections encompass contagious pathogens transmitted through sexual contact, presenting with urethral or vaginal discharge, genital ulcers, dysuria, pelvic pain, or asymptomatic systemic progression.',
    'Sub-conjunctival Haemorrhage': 'A subconjunctival hemorrhage is an acute, harmless accumulation of blood under the transparent bulbar conjunctiva resulting from ruptured fragile microvessels, presenting as a bright red, painless scleral patch.',
    'Taeniasis/cysticercosis': 'Taeniasis is intestinal tapeworm infection caused by adult Taenia solium or saginata, while cysticercosis occurs when ingested eggs develop into larval oncospheres in systemic tissues, notably causing seizures in neurocysticercosis.',
    'Warkany syndrome': 'Warkany syndrome (Trisomy 8 mosaicism) is a rare chromosomal disorder characterized by developmental delay, characteristic deep plantar and palmar furrows, craniofacial dysmorphism, joint contractures, and cardiac anomalies.'
}

for idx, row in df_desc.iterrows():
    d = str(row['disease']).strip()
    if d in VERIFIED_DESCRIPTIONS:
        df_desc.at[idx, 'description'] = VERIFIED_DESCRIPTIONS[d]

df_desc.to_csv(DESC_PATH, index=False)
print("Updated all missing descriptions in Symptom_Description.csv.")

# 3. Clean, Authentic Clinical Symptom Vocabulary
CORE_SYMPTOM_VOCAB = [
    'headache', 'fever', 'high fever', 'mild fever', 'chills', 'shivering', 'sweating', 'night sweats',
    'fatigue', 'feeling tired', 'muscle weakness', 'dizziness', 'lightheadedness',
    'loss of appetite', 'weight loss', 'dehydration',
    'coughing', 'dry cough', 'barky cough', 'phlegm', 'sore throat', 'throat irritation', 'runny nose',
    'nasal congestion', 'sneezing', 'difficulty breathing', 'shortness breath', 'rapid breathing', 'wheezing',
    'chest tightness', 'chest pain', 'chest pressure', 'loss of smell', 'hoarseness', 'swollen lymph node',
    'nausea', 'vomiting', 'diarrhea', 'bloody diarrhea', 'stomach pain', 'abdominal pain', 'abdominal cramp',
    'abdominal distention', 'bloating', 'indigestion', 'acidity', 'heartburn', 'constipation', 'belching',
    'blood stool', 'jaundice', 'yellow skin', 'yellowing of eyes', 'dark urine',
    'fast heart rate', 'palpitations', 'leg swelling',
    'joint pain', 'muscle pain', 'muscle joint pain', 'neck stiffness', 'stiff neck', 'back pain',
    'swelling', 'decreased range motion', 'joint bone pain', 'cramps',
    'skin rash', 'red rash', 'itching', 'blister', 'redness', 'skin peeling', 'pus', 'boil', 'bruising',
    'confusion', 'numbness', 'tingling', 'tremor', 'seizure', 'blurred vision',
    'photophobia', 'light sensitivity', 'sensitivity sound', 'sleep disturbance',
    'burning urination', 'frequent urination', 'blood urine', 'pelvic pain', 'vaginal discharge'
]

FEATURES = []
for f in CORE_SYMPTOM_VOCAB:
    if f not in FEATURES:
        FEATURES.append(f)

feat_index = {f: i for i, f in enumerate(FEATURES)}
num_feats = len(FEATURES)
print(f"Total features in vocabulary: {num_feats}")

# 4. Clinically Grounded Disease Symptom Profiles
CLINICAL_PROFILES = {
    # Headache & Neurological
    'Migraine': {'primary': ['headache', 'light sensitivity', 'nausea', 'sensitivity sound'], 'secondary': ['vomiting', 'dizziness']},
    'Astigmatism': {'primary': ['headache', 'blurred vision'], 'secondary': ['fatigue']},
    'Acute encephalitis syndrome': {'primary': ['headache', 'fever', 'stiff neck', 'confusion'], 'secondary': ['vomiting', 'seizure']},
    'Aseptic meningitis': {'primary': ['headache', 'fever', 'neck stiffness'], 'secondary': ['photophobia', 'nausea']},
    'Brain Tumour': {'primary': ['seizure', 'blurred vision', 'confusion', 'muscle weakness'], 'secondary': ['headache', 'vomiting']},
    'Stroke': {'primary': ['muscle weakness', 'numbness', 'confusion'], 'secondary': ['headache', 'dizziness']},
    'Neuralgia': {'primary': ['tingling', 'neck stiffness'], 'secondary': ['headache']},
    'Insomnia': {'primary': ['sleep disturbance', 'fatigue'], 'secondary': ['headache']},
    'Alzheimer': {'primary': ['confusion', 'sleep disturbance'], 'secondary': ['fatigue']},

    # Respiratory & Pulmonary
    'Common cold': {'primary': ['runny nose', 'sneezing', 'sore throat', 'coughing'], 'secondary': ['mild fever', 'headache', 'nasal congestion', 'feeling tired']},
    'Influenza': {'primary': ['fever', 'high fever', 'coughing', 'headache', 'muscle joint pain', 'chills'], 'secondary': ['fatigue', 'sore throat', 'runny nose', 'sweating']},
    'Bronchitis': {'primary': ['coughing', 'phlegm', 'chest tightness'], 'secondary': ['mild fever', 'shortness breath', 'fatigue']},
    'Asthma': {'primary': ['wheezing', 'shortness breath', 'coughing', 'chest tightness'], 'secondary': ['difficulty breathing', 'rapid breathing']},
    'Pneumonia': {'primary': ['coughing', 'fever', 'high fever', 'shortness breath', 'chest pain'], 'secondary': ['chills', 'phlegm', 'sweating', 'fatigue']},
    'Chronic obstructive pulmonary disease (COPD)': {'primary': ['shortness breath', 'coughing', 'wheezing', 'phlegm'], 'secondary': ['chest tightness', 'fatigue']},
    'Coronavirus disease 2019 (COVID-19)': {'primary': ['fever', 'coughing', 'loss of smell', 'fatigue'], 'secondary': ['sore throat', 'headache', 'shortness breath']},
    'Tuberculosis': {'primary': ['coughing', 'night sweats', 'weight loss', 'fever'], 'secondary': ['chest pain', 'fatigue', 'phlegm']},
    'Laryngitis': {'primary': ['hoarseness', 'sore throat', 'dry cough'], 'secondary': ['throat irritation', 'mild fever']},
    'Tonsillitis': {'primary': ['sore throat', 'fever', 'swollen lymph node'], 'secondary': ['headache']},
    'Strep throat': {'primary': ['sore throat', 'fever', 'swollen lymph node'], 'secondary': ['headache', 'chills']},
    'Quinsy': {'primary': ['sore throat', 'fever', 'swollen lymph node'], 'secondary': ['headache']},
    'Cough': {'primary': ['coughing', 'throat irritation'], 'secondary': ['phlegm', 'chest tightness']},
    'Whooping cough': {'primary': ['coughing', 'barky cough', 'runny nose'], 'secondary': ['vomiting']},

    # Gastrointestinal & Abdominal
    'Gastroenteritis': {'primary': ['diarrhea', 'vomiting', 'nausea', 'stomach pain'], 'secondary': ['fever', 'abdominal cramp', 'dehydration']},
    'Food Poisoning': {'primary': ['nausea', 'vomiting', 'abdominal cramp', 'diarrhea'], 'secondary': ['fever', 'headache', 'dehydration']},
    'GERD': {'primary': ['acidity', 'heartburn', 'belching', 'stomach pain'], 'secondary': ['nausea', 'throat irritation']},
    'Stomach ulcers': {'primary': ['stomach pain', 'abdominal pain', 'indigestion', 'nausea'], 'secondary': ['bloating', 'vomiting', 'loss of appetite']},
    'Appendicitis': {'primary': ['abdominal pain', 'stomach pain', 'nausea', 'vomiting'], 'secondary': ['fever', 'loss of appetite']},
    'Irritable bowel syndrome': {'primary': ['abdominal cramp', 'bloating', 'diarrhea', 'constipation'], 'secondary': ['abdominal distention']},
    'Colitis': {'primary': ['diarrhea', 'bloody diarrhea', 'abdominal pain'], 'secondary': ['fever', 'weight loss']},
    'Diarrhea': {'primary': ['diarrhea', 'abdominal cramp', 'dehydration'], 'secondary': ['nausea', 'stomach pain']},
    'Dysentery': {'primary': ['bloody diarrhea', 'abdominal pain', 'fever'], 'secondary': ['nausea', 'dehydration']},
    'Cholera': {'primary': ['diarrhea', 'dehydration', 'vomiting'], 'secondary': ['muscle weakness']},
    'Amoebiasis': {'primary': ['bloody diarrhea', 'stomach pain', 'fever'], 'secondary': ['fatigue']},
    'Jaundice': {'primary': ['yellow skin', 'yellowing of eyes', 'dark urine'], 'secondary': ['fatigue', 'loss of appetite']},
    'Hepatitis A': {'primary': ['jaundice', 'yellow skin', 'fatigue', 'nausea'], 'secondary': ['fever', 'abdominal pain']},
    'Hepatitis B': {'primary': ['jaundice', 'yellowing of eyes', 'dark urine', 'fatigue'], 'secondary': ['abdominal pain']},
    'Hepatitis C': {'primary': ['fatigue', 'jaundice', 'dark urine'], 'secondary': ['abdominal pain']},
    'Dehydration': {'primary': ['dehydration', 'dizziness', 'lightheadedness'], 'secondary': ['headache', 'fatigue']},

    # Febrile & Tropical Infections
    'Malaria': {'primary': ['fever', 'high fever', 'chills', 'shivering', 'sweating'], 'secondary': ['headache', 'nausea', 'vomiting', 'muscle joint pain']},
    'Dengue': {'primary': ['high fever', 'headache', 'joint bone pain', 'skin rash'], 'secondary': ['muscle joint pain', 'nausea', 'vomiting']},
    'Typhoid': {'primary': ['fever', 'high fever', 'headache', 'stomach pain'], 'secondary': ['constipation', 'diarrhea', 'fatigue']},
    'Paratyphoid fever': {'primary': ['fever', 'headache', 'stomach pain', 'chills'], 'secondary': ['loss of appetite']},
    'Chikungunya Fever': {'primary': ['joint bone pain', 'fever', 'skin rash', 'swelling'], 'secondary': ['headache', 'muscle pain']},
    'Chickenpox': {'primary': ['blister', 'skin rash', 'fever', 'itching'], 'secondary': ['fatigue', 'headache']},
    'Measles': {'primary': ['fever', 'red rash', 'coughing', 'runny nose'], 'secondary': ['sore throat']},
    'Mumps': {'primary': ['swelling', 'fever', 'headache', 'muscle pain'], 'secondary': ['loss of appetite']},
    'Rubella': {'primary': ['red rash', 'mild fever', 'swollen lymph node', 'joint pain'], 'secondary': ['headache']},
    'Brucellosis': {'primary': ['fever', 'sweating', 'joint pain', 'fatigue'], 'secondary': ['muscle pain', 'loss of appetite']},
    'Zika virus disease': {'primary': ['fever', 'red rash', 'joint pain', 'redness'], 'secondary': ['headache', 'muscle pain']},
    'Hand, Foot and Mouth Disease': {'primary': ['fever', 'blister', 'skin rash', 'sore throat'], 'secondary': ['loss of appetite']},
    'Scarlet fever': {'primary': ['fever', 'sore throat', 'red rash', 'swollen lymph node'], 'secondary': ['headache', 'vomiting']},
    'Yellow Fever': {'primary': ['fever', 'chills', 'yellow skin', 'nausea'], 'secondary': ['headache', 'vomiting']},
    'Tularemia': {'primary': ['fever', 'swollen lymph node', 'fatigue'], 'secondary': ['chills', 'headache']},

    # Cardiovascular
    'Myocardial Infarction (Heart Attack)': {'primary': ['chest pain', 'chest pressure', 'shortness breath', 'sweating'], 'secondary': ['nausea', 'dizziness', 'fast heart rate']},
    'Coronary Heart Disease': {'primary': ['chest pain', 'chest tightness', 'shortness breath'], 'secondary': ['fatigue', 'dizziness']},
    'Congestive heart disease': {'primary': ['shortness breath', 'fatigue', 'leg swelling'], 'secondary': ['rapid breathing']},
    'High blood pressure': {'primary': ['headache', 'dizziness'], 'secondary': ['blurred vision', 'fatigue']},
    'Pericarditis': {'primary': ['chest pain', 'fever'], 'secondary': ['shortness breath']},

    # Musculoskeletal
    'Arthritis': {'primary': ['joint pain', 'swelling', 'decreased range motion'], 'secondary': ['redness', 'muscle weakness']},
    'Osteoarthritis': {'primary': ['joint pain', 'decreased range motion'], 'secondary': ['swelling']},
    'Rheumatoid arthritis': {'primary': ['joint pain', 'swelling', 'fatigue'], 'secondary': ['fever', 'redness']},
    'Rheumatism': {'primary': ['joint pain', 'muscle pain', 'swelling'], 'secondary': ['fatigue']},
    'Rheumatic fever': {'primary': ['joint bone pain', 'fever', 'fast heart rate'], 'secondary': ['swelling']},
    'Gout': {'primary': ['joint pain', 'redness', 'swelling'], 'secondary': ['fever']},
    'Sciatica': {'primary': ['back pain', 'numbness', 'tingling', 'muscle weakness'], 'secondary': ['cramps']},

    # Dermatological
    'Urticaria': {'primary': ['skin rash', 'red rash', 'itching', 'swelling'], 'secondary': ['redness']},
    'Eczema': {'primary': ['skin rash', 'itching', 'redness', 'skin peeling'], 'secondary': ['swelling']},
    'Psoriasis': {'primary': ['skin rash', 'red rash', 'skin peeling', 'itching'], 'secondary': ['joint pain']},
    'Impetigo': {'primary': ['blister', 'pus', 'skin rash'], 'secondary': ['itching', 'redness']},
    'Fungal infection': {'primary': ['itching', 'skin rash', 'redness'], 'secondary': ['skin peeling']},
    'Scabies': {'primary': ['itching', 'skin rash', 'blister'], 'secondary': ['redness']},

    # Urological & Hematological
    'Urinary tract infection': {'primary': ['burning urination', 'frequent urination', 'pelvic pain'], 'secondary': ['fever', 'blood urine']},
    'Calculi': {'primary': ['stomach pain', 'abdominal pain', 'blood urine', 'burning urination'], 'secondary': ['nausea', 'vomiting']},
    'Anaemia': {'primary': ['fatigue', 'feeling tired', 'muscle weakness', 'shortness breath', 'dizziness'], 'secondary': ['headache']},
    'Iron Deficiency Anemia': {'primary': ['fatigue', 'feeling tired', 'muscle weakness', 'dizziness'], 'secondary': ['headache']},
    'Diabetes Mellitus': {'primary': ['frequent urination', 'weight loss', 'fatigue'], 'secondary': ['blurred vision']},

    # Rare conditions (Never triggered by single common symptoms)
    'Lead poisoning': {'primary': ['confusion', 'muscle weakness', 'abdominal cramp', 'tingling'], 'secondary': ['constipation']},
    'Carbon monoxide poisoning': {'primary': ['confusion', 'dizziness', 'chest pain', 'nausea'], 'secondary': ['headache']},
    'Heat-Related Illnesses and Heat waves': {'primary': ['dehydration', 'high fever', 'dizziness', 'sweating'], 'secondary': ['headache']},
    'Rabies': {'primary': ['confusion', 'seizure', 'muscle weakness'], 'secondary': ['fever']},
    'Porphyria': {'primary': ['abdominal pain', 'confusion', 'seizure'], 'secondary': ['vomiting']},
    'Anthrax': {'primary': ['blister', 'swelling', 'chest pain'], 'secondary': ['fever']},
    'Ebola': {'primary': ['high fever', 'fatigue', 'muscle joint pain', 'bloody diarrhea'], 'secondary': ['vomiting']}
}

# 5. Core Single-Symptom Calibration Mapping
# Ensures common standalone symptoms point directly to everyday clinical entities, not rare ones.
SINGLE_SYMPTOM_DISEASES = {
    'headache': [('Migraine', 40), ('Common cold', 20), ('Influenza', 18), ('Astigmatism', 15), ('High blood pressure', 10)],
    'fever': [('Common cold', 25), ('Influenza', 25), ('Coronavirus disease 2019 (COVID-19)', 22), ('Malaria', 20), ('Dengue', 18), ('Typhoid', 15)],
    'coughing': [('Common cold', 25), ('Cough', 25), ('Influenza', 20), ('Bronchitis', 20), ('Asthma', 18), ('Pneumonia', 15)],
    'dry cough': [('Common cold', 25), ('Laryngitis', 20), ('Asthma', 18), ('Bronchitis', 18)],
    'sore throat': [('Common cold', 25), ('Strep throat', 25), ('Tonsillitis', 22), ('Laryngitis', 18), ('Quinsy', 12)],
    'runny nose': [('Common cold', 30), ('Influenza', 20), ('Coronavirus disease 2019 (COVID-19)', 18)],
    'sneezing': [('Common cold', 30)],
    'vomiting': [('Gastroenteritis', 25), ('Food Poisoning', 25), ('Stomach ulcers', 20), ('GERD', 18), ('Appendicitis', 15), ('Migraine', 15)],
    'nausea': [('Food Poisoning', 25), ('Gastroenteritis', 25), ('GERD', 20), ('Stomach ulcers', 18), ('Migraine', 18)],
    'diarrhea': [('Diarrhea', 30), ('Gastroenteritis', 25), ('Food Poisoning', 22), ('Dysentery', 18), ('Colitis', 15)],
    'stomach pain': [('Stomach ulcers', 25), ('Gastroenteritis', 25), ('Food Poisoning', 22), ('GERD', 20), ('Appendicitis', 18)],
    'abdominal pain': [('Appendicitis', 25), ('Stomach ulcers', 22), ('Gastroenteritis', 22), ('Calculi', 18), ('Colitis', 15)],
    'acidity': [('GERD', 35), ('Stomach ulcers', 20)],
    'heartburn': [('GERD', 35), ('Stomach ulcers', 20)],
    'chest pain': [('Myocardial Infarction (Heart Attack)', 35), ('Coronary Heart Disease', 25), ('Pericarditis', 18), ('Pneumonia', 15), ('GERD', 12)],
    'chest pressure': [('Myocardial Infarction (Heart Attack)', 40), ('Coronary Heart Disease', 30)],
    'chest tightness': [('Asthma', 30), ('Bronchitis', 25), ('Coronary Heart Disease', 20)],
    'shortness breath': [('Asthma', 25), ('Pneumonia', 25), ('Chronic obstructive pulmonary disease (COPD)', 20), ('Congestive heart disease', 20), ('Myocardial Infarction (Heart Attack)', 18)],
    'difficulty breathing': [('Asthma', 25), ('Pneumonia', 25), ('Myocardial Infarction (Heart Attack)', 20)],
    'skin rash': [('Urticaria', 25), ('Eczema', 25), ('Psoriasis', 20), ('Chickenpox', 18), ('Impetigo', 15), ('Scabies', 15)],
    'itching': [('Urticaria', 25), ('Eczema', 25), ('Fungal infection', 22), ('Scabies', 18), ('Chickenpox', 15)],
    'joint pain': [('Osteoarthritis', 30), ('Arthritis', 25), ('Rheumatism', 22), ('Rheumatic fever', 18), ('Gout', 15), ('Chikungunya Fever', 15)],
    'back pain': [('Sciatica', 30), ('Osteoarthritis', 20)],
    'fatigue': [('Anaemia', 25), ('Iron Deficiency Anemia', 25), ('Common cold', 20), ('Influenza', 20), ('Diabetes Mellitus', 15)],
    'dizziness': [('Anaemia', 25), ('Dehydration', 25), ('High blood pressure', 20), ('Migraine', 18)],
    'burning urination': [('Urinary tract infection', 35), ('Calculi', 20)],
    'yellow skin': [('Jaundice', 35), ('Hepatitis A', 22), ('Hepatitis B', 20)]
}

# 6. Generate Training Samples
print("Building balanced clinical training samples...")
np.random.seed(42)
X_records = []
y_records = []

for dis in ALL_DISEASES:
    prof = CLINICAL_PROFILES.get(dis)
    if not prof:
        desc_text = str(df_desc[df_desc['disease'] == dis]['description'].values[0]).lower()
        matched = [f for f in FEATURES if f in desc_text]
        if not matched:
            matched = ['fatigue', 'mild fever']
        prof = {'primary': matched[:3], 'secondary': matched[3:5]}

    prim = [s for s in prof.get('primary', []) if s in feat_index]
    sec = [s for s in prof.get('secondary', []) if s in feat_index]
    if not prim and not sec:
        prim = ['fatigue']

    # 40 multi-symptom permutations per disease
    for _ in range(40):
        vec = np.zeros(num_feats, dtype=float)
        # Primary symptoms present with 85% probability
        for p in prim:
            if np.random.rand() < 0.85:
                vec[feat_index[p]] = 1.0
        # Secondary symptoms present with 45% probability
        for s in sec:
            if np.random.rand() < 0.45:
                vec[feat_index[s]] = 1.0
    # Ensure at least 2 symptoms are present in general multi-symptom training
    if vec.sum() < 2:
        pool = prim + sec
        if len(pool) >= 2:
            vec[feat_index[pool[0]]] = 1.0
            vec[feat_index[pool[1]]] = 1.0
        elif pool:
            vec[feat_index[pool[0]]] = 1.0
            vec[feat_index['fatigue']] = 1.0
        else:
            vec[feat_index['fatigue']] = 1.0
            vec[feat_index['mild fever']] = 1.0
    X_records.append(vec)
    y_records.append(dis)

# 7. Add Calibrated Single-Symptom Presentations for Core Diseases
for sym, target_list in SINGLE_SYMPTOM_DISEASES.items():
    if sym not in feat_index:
        continue
    s_idx = feat_index[sym]
    for d_item in target_list:
        d, n_reps = d_item if isinstance(d_item, tuple) else (d_item, 25)
        if d in ALL_DISEASES:
            for _ in range(n_reps):
                vec = np.zeros(num_feats, dtype=float)
                vec[s_idx] = 1.0
                X_records.append(vec)
                y_records.append(d)

X_train_df = pd.DataFrame(X_records, columns=FEATURES)
y_train = np.array(y_records)
print(f"Total training records: {len(X_train_df)} across {len(np.unique(y_train))} classes.")

# 8. Train Logistic Regression
print("Fitting Multinomial Logistic Regression model...")
lr = LogisticRegression(
    C=1.2,
    solver='lbfgs',
    max_iter=1200,
    random_state=42
)
lr.fit(X_train_df, y_train)

# 9. Save Artifacts
joblib.dump(lr, LR_OUT_PATH)
joblib.dump(FEATURES, FEATS_OUT_PATH)
print("Saved retrained logistic_regression_model.pkl and symptom_features.pkl")

# 10. Verification Tests
print("\n=== VERIFICATION OF CLINICAL ACCURACY ===")
checks = [
    ('headache', ['headache']),
    ('fever', ['fever']),
    ('cough', ['coughing']),
    ('vomiting', ['vomiting']),
    ('stomach pain', ['stomach pain']),
    ('chest pain', ['chest pain']),
    ('skin rash', ['skin rash']),
    ('joint pain', ['joint pain']),
    ('fever, headache, cough', ['fever', 'headache', 'coughing']),
    ('vomiting, diarrhea, stomach pain', ['vomiting', 'diarrhea', 'stomach pain']),
    ('chest pain, shortness of breath', ['chest pain', 'shortness breath'])
]

for label, syms in checks:
    v = np.zeros(num_feats)
    for s in syms:
        if s in feat_index:
            v[feat_index[s]] = 1.0
    probs = lr.predict_proba([v])[0]
    top_idx = probs.argsort()[::-1][:4]
    print(f"\nQuery: '{label}'")
    for i in top_idx:
        print(f"  -> {lr.classes_[i]}: {probs[i]*100:.2f}%")
