"""
Niramaya Health AI - Comprehensive Medical Intelligence & Diagnostic Engine
Provides deterministic, offline-capable, clinical-grade medical assessment
for symptoms, diseases, diet, precautions, and emergency guidance in English, Hindi, and Hinglish.
"""

import re

# Comprehensive Multilingual Symptom Dictionary (English, Hindi, Hinglish)
SYMPTOM_PATTERNS = {
    'fever': [
        r'\bfever\b', r'\bbukhar\b', r'\btaap\b', r'\bpyrexia\b', r'\bhigh temperature\b',
        r'\bfeverish\b', r'\bbody is hot\b', r'\bgaram\b', r'\btez bukhar\b', r'\bhalka bukhar\b'
    ],
    'chills': [
        r'\bchills\b', r'\bshivering\b', r'\bthand\b', r'\bthand lagna\b', r'\bkapkapi\b',
        r'\brigors\b', r'\bcold chills\b'
    ],
    'headache': [
        r'\bheadache\b', r'\bhead ache\b', r'\bsir dard\b', r'\bsar dard\b', r'\bforehead pain\b',
        r'\bheaviness in head\b', r'\bsir ghumna\b', r'\badha sir dard\b'
    ],
    'cough': [
        r'\bcough\b', r'\bkhansi\b', r'\bkhasi\b', r'\bcoughing\b', r'\bdry cough\b',
        r'\bsukhi khansi\b', r'\bwet cough\b', r'\bbalgam\b', r'\bmucus\b', r'\bphlegm\b'
    ],
    'cold': [
        r'\bcold\b', r'\bsardi\b', r'\bjukaam\b', r'\bjukam\b', r'\bnazla\b', r'\brunny nose\b',
        r'\brunning nose\b', r'\bnaak behna\b', r'\bblocked nose\b', r'\bstuffy nose\b',
        r'\bsneezing\b', r'\bchheenk\b', r'\bcheenk\b', r'\bcongestion\b'
    ],
    'sore_throat': [
        r'\bsore throat\b', r'\bgale me dard\b', r'\bgala kharab\b', r'\bthroat pain\b',
        r'\bgale me kharash\b', r'\bthroat irritation\b', r'\bpain swallowing\b', r'\bpharyngitis\b'
    ],
    'body_pain': [
        r'\bbody pain\b', r'\bbadan dard\b', r'\bbody ache\b', r'\bmuscle pain\b',
        r'\bmuscle ache\b', r'\bmyalgia\b', r'\bang ang dard\b'
    ],
    'fatigue': [
        r'\bfatigue\b', r'\bweakness\b', r'\bkamzori\b', r'\bkamzori lag rahi\b', r'\bthakan\b',
        r'\btiredness\b', r'\bexhaustion\b', r'\blethargy\b', r'\bsusti\b', r'\bfeeling weak\b'
    ],
    'stomach_pain': [
        r'\bstomach pain\b', r'\bpet dard\b', r'\bpet me dard\b', r'\babdominal pain\b',
        r'\btummy ache\b', r'\bcramps\b', r'\bpet me marod\b', r'\bbelly pain\b', r'\bstomach ache\b'
    ],
    'vomiting': [
        r'\bvomiting\b', r'\bulti\b', r'\bthrow up\b', r'\bpuking\b', r'\bvomit\b', r'\bemesis\b'
    ],
    'nausea': [
        r'\bnausea\b', r'\bulti jaisa\b', r'\bmatli\b', r'\bjee ghabrana\b', r'\bfeeling sick\b',
        r'\bqueasy\b'
    ],
    'diarrhea': [
        r'\bdiarrhea\b', r'\bdiarrhoea\b', r'\bloose motion\b', r'\bdast\b', r'\bloose motions\b',
        r'\bwatery stool\b', r'\bpet kharab\b', r'\bfrequent motions\b'
    ],
    'acidity': [
        r'\bacidity\b', r'\bheartburn\b', r'\bgas\b', r'\bpet phoolna\b', r'\bbloating\b',
        r'\bseene me jalan\b', r'\bkhatti dakar\b', r'\bindigestion\b', r'\bbadhazmi\b',
        r'\bgerd\b', r'\bacid reflux\b'
    ],
    'chest_pain': [
        r'\bchest pain\b', r'\bchhati me dard\b', r'\bseene me dard\b', r'\bchest tightness\b',
        r'\bchest pressure\b', r'\bheavy chest\b'
    ],
    'shortness_of_breath': [
        r'\bshortness of breath\b', r'\bsaans phoolna\b', r'\bsaans lene me takleef\b',
        r'\bsaans lene me dikkat\b', r'\bbreathlessness\b', r'\bdifficulty breathing\b',
        r'\bwheezing\b', r'\bdyspnea\b'
    ],
    'joint_pain': [
        r'\bjoint pain\b', r'\bjodon me dard\b', r'\bghutne me dard\b', r'\bknee pain\b',
        r'\bjoint swelling\b', r'\bswollen joints\b', r'\bstiffness\b', r'\bback pain\b', r'\bkamar dard\b'
    ],
    'dizziness': [
        r'\bdizziness\b', r'\bchakkar\b', r'\bsir ghumna\b', r'\bfeeling faint\b',
        r'\blightheaded\b', r'\bvertigo\b', r'\bunsteady\b'
    ],
    'rash': [
        r'\brash\b', r'\bskin rash\b', r'\bdaane\b', r'\bred spots\b', r'\bkhujli\b',
        r'\bitching\b', r'\ballergy\b', r'\bhives\b', r'\bskin allergy\b'
    ],
    'burning_urination': [
        r'\bburning urination\b', r'\bpeshab me jalan\b', r'\bpainful urination\b',
        r'\bdysuria\b', r'\bburning urine\b', r'\bfrequent urination\b', r'\bbaar baar peshab\b'
    ],
    'yellow_eyes_skin': [
        r'\byellow eyes\b', r'\byellow skin\b', r'\bpili aankhein\b', r'\bpeela peshab\b',
        r'\bdark yellow urine\b'
    ],
    'high_blood_sugar': [
        r'\bhigh sugar\b', r'\bsugar level\b', r'\bhigh glucose\b', r'\bblood sugar\b',
        r'\bexcessive thirst\b', r'\bbaar baar pyaas\b'
    ],
    'high_bp': [
        r'\bhigh bp\b', r'\bhigh blood pressure\b', r'\bbp badhna\b'
    ],
    'low_bp': [
        r'\blow bp\b', r'\blow blood pressure\b', r'\bbp kam\b'
    ],
    'loss_of_appetite': [
        r'\bloss of appetite\b', r'\bbhook na lagna\b', r'\bkam bhook\b', r'\bno appetite\b'
    ],
    'constipation': [
        r'\bconstipation\b', r'\bkabz\b', r'\bpet saaf na hona\b', r'\bhard stool\b'
    ],
    'insomnia': [
        r'\binsomnia\b', r'\bneend na aana\b', r'\bsleeplessness\b', r'\bsleep trouble\b'
    ],
    'anxiety': [
        r'\banxiety\b', r'\bghabrahat\b', r'\bbechaini\b', r'\bnervousness\b', r'\bpanic\b'
    ],
    'sweating': [
        r'\bsweating\b', r'\bprofuse sweating\b', r'\bpasina\b', r'\bcold sweat\b'
    ],
    'weight_gain': [
        r'\bweight gain\b', r'\bweight gaining\b', r'\bvazan badhna\b', r'\brapid weight gain\b', r'\bgaining weight\b'
    ],
    'weight_loss': [
        r'\bweight loss\b', r'\bvazan ghatna\b', r'\bunexplained weight loss\b', r'\blosing weight\b'
    ]
}

# Clean display names for symptoms
SYMPTOM_DISPLAY = {
    'fever': 'Fever / High Body Temperature (बुखार)',
    'chills': 'Chills & Shivering (ठंड लगना / कंपकंपी)',
    'headache': 'Headache (सिर दर्द)',
    'cough': 'Cough (खांसी)',
    'cold': 'Cold & Nasal Congestion (सर्दी / जुकाम)',
    'sore_throat': 'Sore Throat (गले में खराश / दर्द)',
    'body_pain': 'Body / Muscle Ache (बदन दर्द)',
    'fatigue': 'Fatigue & Weakness (थकान / कमजोरी)',
    'stomach_pain': 'Stomach / Abdominal Pain (पेट दर्द)',
    'vomiting': 'Vomiting (उल्टी)',
    'nausea': 'Nausea (उल्टी जैसा लगना / मतली)',
    'diarrhea': 'Diarrhea / Loose Motion (दस्त)',
    'acidity': 'Acidity, Gas & Heartburn (गैस / सीने में जलन)',
    'chest_pain': 'Chest Pain / Tightness (छाती / सीने में दर्द)',
    'shortness_of_breath': 'Shortness of Breath (सांस लेने में तकलीफ)',
    'joint_pain': 'Joint Pain / Stiffness (जोड़ों में दर्द / जकड़न)',
    'dizziness': 'Dizziness / Vertigo (चक्कर आना)',
    'rash': 'Skin Rash / Itching (खुजली / लाल दाने)',
    'burning_urination': 'Burning Urination / Dysuria (पेशाब में जलन)',
    'yellow_eyes_skin': 'Yellowing of Eyes & Skin / Jaundice signs (पीलिया लक्षण)',
    'high_blood_sugar': 'High Blood Sugar Signs (हाई ब्लड शुगर)',
    'high_bp': 'High Blood Pressure (उच्च रक्तचाप)',
    'low_bp': 'Low Blood Pressure (लो बीपी)',
    'loss_of_appetite': 'Loss of Appetite (भूख न लगना)',
    'constipation': 'Constipation (कब्ज)',
    'insomnia': 'Sleep Disturbance / Insomnia (अनिद्रा)',
    'anxiety': 'Anxiety / Restlessness (घबराहट / बेचैनी)',
    'sweating': 'Excessive Sweating (पसीना आना)',
    'weight_gain': 'Weight Gain (असामान्य वजन बढ़ना)',
    'weight_loss': 'Weight Loss (असामान्य वजन घटना)'
}

# Comprehensive Clinical Disease Knowledge Base
CLINICAL_DISEASES = {
    'heart_attack_warning': {
        'name': 'Acute Coronary Syndrome / Heart Attack Emergency Alert (हार्ट अटैक आपातकालीन चेतावनी)',
        'category': 'Critical Cardiovascular Emergency',
        'keywords': ['heart attack', 'angina', 'myocardial infarction', 'cardiac arrest', 'dil ka daura'],
        'primary_symptoms': ['chest_pain', 'shortness_of_breath', 'sweating'],
        'secondary_symptoms': ['dizziness', 'nausea', 'fatigue'],
        'overview': (
            "Severe central chest pain, crushing pressure, or heaviness that may radiate to the left arm, "
            "shoulder, neck, or jaw is a critical emergency indicator of Acute Myocardial Infarction (Heart Attack) "
            "or severe Angina pectoris. Immediate emergency medical intervention is required."
        ),
        'causes': "Sudden blockage of coronary artery blood flow usually caused by atherosclerotic plaque rupture and thrombosis.",
        'diet_and_home_care': [
            "DO NOT waste time on home remedies for acute chest pain.",
            "For long-term heart health: Adopt a low-sodium, zero-trans-fat, Mediterranean diet rich in leafy greens, nuts, and garlic."
        ],
        'precautions': [
            "Call emergency medical services (Ambulance 108/112 in India) IMMEDIATELY.",
            "Have the person sit down quietly in a supported W-position (leaning back with knees bent) to relieve stress on the heart.",
            "Loosen tight clothing around neck and chest; do not allow the person to walk or exert themselves.",
            "If directed by emergency clinicians and no allergy exists, chew a 300mg soluble aspirin while waiting for the ambulance."
        ],
        'recommended_tests': ['Emergency 12-Lead ECG', 'Cardiac Troponin-I / Troponin-T Blood Test', 'Echocardiogram (ECHO)', 'Emergency Coronary Angiography'],
        'warning_signs': [
            "Crushing, squeezing pain or heavy pressure in the center of the chest lasting > 3 minutes",
            "Pain radiating to left arm, back, neck, jaw, or epigastrium with profuse cold sweating",
            "Sudden severe shortness of breath, extreme lightheadedness, or loss of consciousness"
        ]
    },

    'headache_migraine': {
        'name': 'Tension Headache & Migraine / Cephalea (सिर दर्द एवं माइग्रेन)',
        'category': 'Neurological / Primary Cephalalgia',
        'keywords': ['headache', 'head ache', 'migraine', 'migrane', 'cephalea', 'sir dard', 'sar dard', 'adha sishi', 'cluster headache', 'forehead pain', 'head pain'],
        'primary_symptoms': ['headache'],
        'secondary_symptoms': ['nausea', 'dizziness', 'fatigue', 'insomnia'],
        'overview': (
            "Headache (cephalalgia) is one of the most common medical symptoms, typically presenting as "
            "a Tension-type headache (diffuse, band-like dull aching across forehead, temples, or back of head) or "
            "Migraine (throbbing, pulsating pain often on one side of head, sometimes accompanied by nausea or light sensitivity). "
            "Most acute headaches arise from muscle contraction, mental stress, eye fatigue, dehydration, or irregular sleep patterns."
        ),
        'causes': "Stress, dehydration, prolonged digital screen exposure, cervical posture strain, lack of sleep, skipping meals, or neurovascular migraine triggers.",
        'diet_and_home_care': [
            "Hydration first: Drink 2 to 3 glasses of cool or room-temperature water immediately.",
            "Rest in a quiet, dark, well-ventilated room with eyes closed for 20-30 minutes.",
            "Apply a cold damp washcloth or ice pack to your forehead, temples, or base of the neck.",
            "Sip warm herbal ginger tea or lemon-mint water to relieve muscle tightness and mild nausea.",
            "Practice gentle neck and shoulder stretching to release tension."
        ],
        'precautions': [
            "Avoid staring at bright smartphone, laptop, or television screens while experiencing a headache.",
            "Do not consume excess caffeinated or sugary energy drinks; limit loud noise exposures.",
            "Avoid frequent unprescribed over-the-counter painkillers (limit analgesics to prevent rebound medication-overuse headaches).",
            "Maintain consistent meal times and ensure 7 to 8 hours of uninterrupted sleep."
        ],
        'recommended_tests': ['Refraction / Eye Examination (to rule out vision strain)', 'Blood Pressure Measurement', 'Neurological consultation if headaches are recurrent (>2 per week)'],
        'warning_signs': [
            "Sudden, explosive 'thunderclap' headache reaching peak intensity within seconds (worst headache of your life)",
            "Headache accompanied by high fever, neck stiffness (inability to touch chin to chest), confusion, or rash",
            "Headache following recent head trauma or accompanied by weakness, numbness, or slurred speech"
        ]
    },

    'viral_fever': {
        'name': 'Acute Viral Fever & Seasonal Febrile Illness (वायरल बुखार)',
        'category': 'Acute Viral Infection',
        'keywords': ['viral fever', 'bukhar', 'season fever', 'viral', 'halka bukhar', 'tez bukhar', 'pyrexia', 'body is hot'],
        'primary_symptoms': ['fever'],
        'secondary_symptoms': ['body_pain', 'fatigue', 'headache', 'chills', 'loss_of_appetite'],
        'overview': (
            "Viral fever is an acute elevation of body temperature above normal (98.6°F / 37°C) caused by an "
            "underlying viral infection. It is frequently accompanied by general body aches, weakness, headache, "
            "and loss of appetite as the body's immune defense responds to fight the virus."
        ),
        'causes': "Airborne or contact viral pathogens (rhinovirus, adenovirus, seasonal enteroviruses, influenza-like illness).",
        'diet_and_home_care': [
            "Drink plenty of warm fluids (boiled water, clear vegetable soups, coconut water, herbal tea) to prevent dehydration.",
            "Consume light, warm, freshly cooked foods (dalia, moong dal khichdi, boiled vegetables, applesauce).",
            "Get strict bed rest in a well-ventilated room; do not exert yourself physically.",
            "Apply lukewarm (not cold) water sponge compresses to forehead and limbs if temperature exceeds 101°F."
        ],
        'precautions': [
            "Monitor body temperature with a digital thermometer every 4 to 6 hours.",
            "Do not take antibiotics on your own; antibiotics are ineffective against viral infections.",
            "Use only antipyretics like Paracetamol in age-appropriate dosage under clinical advice.",
            "Wash hands frequently and isolate personal eating utensils and towels to protect family members."
        ],
        'recommended_tests': ['Complete Blood Count (CBC) with ESR', 'Urine Routine Examination', 'Physician consultation if fever persists past 3 days'],
        'warning_signs': [
            "High fever persisting above 102.5°F that does not respond to standard fever medication",
            "Severe shortness of breath, chest pain, persistent vomiting, or extreme lethargy/confusion",
            "Appearance of unusual rash, dark urine, or bleeding from nose/gums"
        ]
    },

    'cough_cold_urti': {
        'name': 'Common Cold & Upper Respiratory Tract Infection (सर्दी, जुकाम एवं खांसी)',
        'category': 'Respiratory Viral Infection',
        'keywords': ['cold', 'cough', 'jukaam', 'sardi', 'khansi', 'sneezing', 'runny nose', 'stuffy nose', 'sore throat', 'chheenk'],
        'primary_symptoms': ['cold', 'cough', 'sore_throat'],
        'secondary_symptoms': ['headache', 'fever', 'fatigue'],
        'overview': (
            "Common cold and acute upper respiratory tract infection (URTI) are viral illnesses affecting "
            "the nasal passages, throat, and upper airways. Symptoms include runny or congested nose, frequent sneezing, "
            "sore throat irritation, and dry or productive coughing."
        ),
        'causes': "Rhinoviruses, Coronaviruses, Respiratory Syncytial Virus (RSV), or Parainfluenza transmitted via airborne droplets or hand-to-face contact.",
        'diet_and_home_care': [
            "Drink warm water, ginger-tulsi tea, honey with warm water (for cough relief), and warm vegetable/chicken soup.",
            "Perform warm saltwater gargles 2-3 times daily to soothe throat irritation and reduce swelling.",
            "Inhale steam (plain water steam inhalation) for 5-10 minutes to open congested nasal airways."
        ],
        'precautions': [
            "Cover your mouth and nose with a tissue or elbow when coughing or sneezing.",
            "Avoid cold drinks, ice, and extremely refrigerated food.",
            "Maintain hand hygiene by washing with soap and water frequently.",
            "Rest adequately to facilitate prompt recovery."
        ],
        'recommended_tests': ['Clinical ENT / Throat Evaluation', 'Complete Blood Count (if fever coexists)'],
        'warning_signs': [
            "Difficulty breathing, audible wheezing, or chest pain while breathing",
            "Inability to swallow fluids or severe ear pain",
            "Cough lasting longer than 2 weeks or coughing up blood"
        ]
    },

    'dengue': {
        'name': 'Dengue Fever (डेंगू बुखार)',
        'category': 'Viral Tropical Infection',
        'keywords': ['dengue', 'dengu', 'breakbone', 'haddi tod', 'platelet', 'aedes'],
        'primary_symptoms': ['fever', 'body_pain', 'headache', 'joint_pain'],
        'secondary_symptoms': ['rash', 'fatigue', 'nausea', 'vomiting'],
        'overview': (
            "Dengue is an acute viral infection transmitted by the bite of infected female Aedes mosquitoes. "
            "It is characteristically marked by sudden high fever, intense retro-orbital (behind the eye) headache, "
            "severe bone and muscular pain ('breakbone fever'), and potential drop in blood platelets."
        ),
        'causes': "Dengue virus (DENV-1 to 4) transmitted primarily by daylight-biting Aedes aegypti mosquitoes.",
        'diet_and_home_care': [
            "Hydration is critical: Drink coconut water, ORS, fresh pomegranate/citrus juice, and clear soups.",
            "Papaya leaf extract and kiwi fruit are popular traditional adjuncts to support wellness.",
            "Eat soft, easily digestible foods like porridge, khichdi, and boiled vegetables.",
            "Avoid dark, oily, spicy foods and carbonated drinks."
        ],
        'precautions': [
            "Strictly avoid NSAIDs like Aspirin, Ibuprofen, or Diclofenac as they dramatically increase internal bleeding risk; use only Paracetamol under medical advice.",
            "Monitor Complete Blood Count (CBC) and platelet count daily or as advised by your physician.",
            "Use mosquito repellents, sleep under mosquito nets, and eliminate any standing water around your home.",
            "Ensure absolute physical bed rest until fever subsides completely."
        ],
        'recommended_tests': ['Dengue NS1 Antigen Test (Day 1-5)', 'Dengue IgM/IgG Antibody Test', 'Complete Blood Count (CBC - Platelets & Hematocrit)'],
        'warning_signs': [
            "Severe persistent abdominal pain or continuous vomiting",
            "Bleeding from gums, nose, or blood in stool/vomit",
            "Sudden drop in platelet count below 50,000 / μL",
            "Extreme restlessness, lethargy, cold clammy skin, or dizziness (Dengue Shock Warning)"
        ]
    },

    'malaria': {
        'name': 'Malaria (मलेरिया)',
        'category': 'Parasitic Vector-Borne Disease',
        'keywords': ['malaria', 'plasmodium', 'anopheles', 'sheet jwar'],
        'primary_symptoms': ['fever', 'chills', 'headache', 'sweating'],
        'secondary_symptoms': ['fatigue', 'body_pain', 'nausea', 'vomiting'],
        'overview': (
            "Malaria is a mosquito-borne disease caused by Plasmodium parasites. "
            "It typically manifests in recurring cycles: intense shivering and cold chills, followed by spiking high fever, "
            "and finally profuse sweating with extreme exhaustion."
        ),
        'causes': "Infection by Plasmodium vivax or falciparum through the bite of infected female Anopheles mosquitoes.",
        'diet_and_home_care': [
            "Drink plenty of boiled and filtered water, coconut water, and electrolyte solutions.",
            "Consume light, high-protein and high-carbohydrate meals (dalia, boiled eggs, dal-rice).",
            "Avoid heavy, greasy, or junk food during acute fever episodes."
        ],
        'precautions': [
            "Get an urgent Rapid Diagnostic Test (RDT) or Peripheral Blood Smear for Malaria Parasite.",
            "Complete the full course of prescribed antimalarial medications even if you feel better.",
            "Sleep under insecticide-treated bed nets and install window mesh screens.",
            "Take prescribed fever-reducing medicine (Paracetamol) and apply lukewarm sponge compresses if fever is high."
        ],
        'recommended_tests': ['Malarial Parasite (MP) Blood Smear', 'Rapid Antigen Test for Malaria (Pf/Pv)', 'Complete Blood Count (CBC)'],
        'warning_signs': [
            "Confusion, extreme drowsiness, or seizures (Cerebral Malaria)",
            "Difficulty breathing or persistent vomiting preventing oral medication",
            "Dark brown or tea-colored urine, jaundice, or severe anemia"
        ]
    },

    'typhoid': {
        'name': 'Typhoid Fever / Enteric Fever (टाइफाइड / मोतीझरा)',
        'category': 'Bacterial Intestinal Infection',
        'keywords': ['typhoid', 'enteric fever', 'motijhara', 'salmonella', 'widal'],
        'primary_symptoms': ['fever', 'headache', 'stomach_pain', 'fatigue'],
        'secondary_symptoms': ['loss_of_appetite', 'constipation', 'diarrhea', 'nausea'],
        'overview': (
            "Typhoid is a systemic bacterial infection caused by Salmonella Typhi. "
            "It is characterized by a gradual 'step-ladder' rising fever, severe prolonged headache, "
            "abdominal discomfort, fatigue, and coated tongue."
        ),
        'causes': "Ingestion of food or water contaminated with the bacterium Salmonella enterica serotype Typhi.",
        'diet_and_home_care': [
            "Eat bland, semi-solid foods: well-cooked khichdi, curd-rice, mashed potatoes, and bananas.",
            "Drink only boiled, RO-purified, or bottled water.",
            "Avoid raw salads, street foods, unpasteurized dairy, and high-fiber coarse grains during active infection.",
            "Drink coconut water and pomegranate juice to maintain electrolyte balance."
        ],
        'precautions': [
            "Consult a physician promptly for appropriate antibiotic therapy and finish the full regimen.",
            "Practice rigorous hand hygiene before preparing food, eating, and after using the restroom.",
            "Ensure proper rest to allow intestinal ulcers to heal and prevent intestinal complications.",
            "Do not consume uncooked street food or cut fruits exposed to flies."
        ],
        'recommended_tests': ['Blood Culture (Gold standard in 1st week)', 'Widal Test (after Day 7-10)', 'TyphiDot IgM/IgG', 'CBC with ESR'],
        'warning_signs': [
            "Severe sharp abdominal pain with rigid abdomen (Intestinal Perforation Emergency)",
            "High fever persisting beyond 5 days despite antibiotic treatment",
            "Blood in stool or altered consciousness/delirium"
        ]
    },

    'gastroenteritis': {
        'name': 'Acute Gastroenteritis / Food Poisoning (फूड पॉइजनिंग / पेट का संक्रमण)',
        'category': 'Gastrointestinal Infection',
        'keywords': ['food poisoning', 'gastroenteritis', 'stomach infection', 'stomach flu', 'bacterial diarrhea'],
        'primary_symptoms': ['diarrhea', 'vomiting', 'stomach_pain'],
        'secondary_symptoms': ['nausea', 'fever', 'fatigue', 'chills'],
        'overview': (
            "Acute gastroenteritis is an inflammation of the stomach and intestines, commonly caused by viral or bacterial "
            "food poisoning. It causes sudden onset watery diarrhea, nausea, vomiting, and abdominal cramping."
        ),
        'causes': "Rotavirus, Norovirus, E. coli, Salmonella, or Staphylococcal toxins from contaminated food or unhygienic water.",
        'diet_and_home_care': [
            "Sip Oral Rehydration Salts (ORS) solution continuously after every loose stool.",
            "Follow the BRAT diet: Bananas, Rice (congee/khichdi), Applesauce, and Toast/plain bread.",
            "Drink tender coconut water, buttermilk with a pinch of roasted cumin and salt, and clear broth.",
            "Strictly avoid dairy milk, fatty foods, caffeine, sugary juices, and spicy foods."
        ],
        'precautions': [
            "Prevent dehydration by replacing fluids and electrolytes proactively.",
            "Wash hands thoroughly with soap and warm water before eating and after toilet use.",
            "Do not consume antidiarrheal medications without doctor approval if fever or blood in stool is present.",
            "Eat freshly prepared, piping hot home-cooked meals."
        ],
        'recommended_tests': ['Stool Routine & Microscopy / Culture', 'Serum Electrolytes (Sodium, Potassium)', 'CBC'],
        'warning_signs': [
            "Signs of severe dehydration: sunken eyes, extreme dry mouth, dizziness, little or no urine",
            "Presence of blood or black tarry material in stool or vomit",
            "Inability to keep any liquids down for more than 12 hours"
        ]
    },

    'gerd_gastritis': {
        'name': 'GERD & Acidity / Peptic Gastritis (एसिडिटी / गैस्ट्राइटिस)',
        'category': 'Digestive System Disorder',
        'keywords': ['acidity', 'gerd', 'acid reflux', 'heartburn', 'gastritis', 'hyperacidity'],
        'primary_symptoms': ['acidity', 'stomach_pain'],
        'secondary_symptoms': ['nausea', 'chest_pain', 'headache', 'loss_of_appetite'],
        'overview': (
            "Gastroesophageal Reflux Disease (GERD) and Gastritis occur when stomach acid washes back into the esophagus "
            "or irritates the stomach lining, producing heartburn, burning epigastric discomfort, sour burps, and bloating."
        ),
        'causes': "Weak lower esophageal sphincter, irregular meal times, spicy/fried food, caffeine, smoking, or H. pylori infection.",
        'diet_and_home_care': [
            "Eat small, frequent meals rather than large, heavy lunches or dinners.",
            "Drink cold milk, coconut water, or fennel (saunf) infused water to soothe acidity.",
            "Avoid lying down immediately after eating; wait at least 2 to 3 hours before sleep.",
            "Eliminate spicy, deep-fried, oily, citrus, and caffeinated foods."
        ],
        'precautions': [
            "Elevate the head of your bed by 6 inches if night-time acid reflux disturbs sleep.",
            "Avoid tight-fitting garments around the waist and abdomen.",
            "Practice stress reduction techniques, as mental stress increases gastric acid secretion.",
            "Consider antacids or doctor-prescribed proton pump inhibitors (PPIs) for symptomatic relief."
        ],
        'recommended_tests': ['Upper GI Endoscopy (if chronic)', 'H. pylori Antigen / Urea Breath Test', 'Abdominal Ultrasound'],
        'warning_signs': [
            "Difficulty or pain while swallowing (dysphagia)",
            "Vomiting blood or coffee-ground material, or passing black stools",
            "Unexplained weight loss or severe persistent burning chest pain that mimics cardiac issues"
        ]
    },

    'viral_fever': {
        'name': 'Viral Fever / Seasonal Influenza (वायरल बुखार / फ्लू)',
        'category': 'Acute Viral Respiratory & Systemic Illness',
        'keywords': ['viral fever', 'flu', 'influenza', 'mausami bukhar', 'seasonal fever'],
        'primary_symptoms': ['fever', 'body_pain', 'sore_throat'],
        'secondary_symptoms': ['cough', 'cold', 'headache', 'fatigue', 'chills'],
        'overview': (
            "Viral fever is a generalized inflammatory illness caused by seasonal respiratory or enteroviral infections. "
            "It commonly presents with fever, generalized muscular aches, sore throat, mild cold, and fatigue, usually lasting 3 to 7 days."
        ),
        'causes': "Influenza, Rhinovirus, Adenovirus, Parainfluenza, or seasonal enteroviruses spread via airborne droplets.",
        'diet_and_home_care': [
            "Drink warm herbal infusions (kadha with tulsi, ginger, turmeric, and honey).",
            "Consume warm soups, broth, herbal teas, and seasonal fresh fruits rich in Vitamin C.",
            "Stay thoroughly hydrated with warm water throughout the day.",
            "Gargle twice daily with warm salt water to relieve throat irritation."
        ],
        'precautions': [
            "Rest at home to conserve energy and avoid transmitting the virus to family or colleagues.",
            "Use Paracetamol as directed for fever and body ache; avoid unnecessary antibiotics for viral conditions.",
            "Steam inhalation helps clear nasal and sinus congestion.",
            "Monitor body temperature twice daily with a digital thermometer."
        ],
        'recommended_tests': ['Complete Blood Count (CBC - to rule out bacterial infection)', 'Influenza Panel if symptoms persist > 5 days'],
        'warning_signs': [
            "Fever exceeding 103°F (39.4°C) or not responding to antipyretics",
            "Shortness of breath, chest congestion, or wheezing",
            "Inability to retain liquids due to severe vomiting"
        ]
    },

    'covid19': {
        'name': 'COVID-19 / Coronavirus Infection (कोविड-19)',
        'category': 'Viral Respiratory Infection',
        'keywords': ['covid', 'covid-19', 'coronavirus', 'corona', 'sars-cov-2', 'omicon'],
        'primary_symptoms': ['fever', 'cough', 'fatigue'],
        'secondary_symptoms': ['sore_throat', 'shortness_of_breath', 'body_pain', 'cold'],
        'overview': (
            "COVID-19 is a contagious respiratory infection caused by the SARS-CoV-2 virus. "
            "Symptoms range from mild upper respiratory illness (dry cough, fever, fatigue, sore throat) "
            "to severe lower respiratory pneumonia requiring supplemental oxygen."
        ),
        'causes': "SARS-CoV-2 transmission through airborne droplets and aerosols in close contact.",
        'diet_and_home_care': [
            "Maintain high fluid intake with warm water, lemon-honey water, and nourishing vegetable/chicken soups.",
            "Consume balanced nutritious food with eggs, pulses, and green leafy vegetables.",
            "Perform steam inhalation and warm saline gargles twice a day."
        ],
        'precautions': [
            "Isolate in a well-ventilated room to protect family members.",
            "Monitor blood oxygen saturation (SpO2) using a pulse oximeter every 6 hours.",
            "Wear a well-fitting mask (N95 or surgical) when interacting with caregivers.",
            "Ensure plenty of bed rest and avoid strenuous physical exertion."
        ],
        'recommended_tests': ['RT-PCR for SARS-CoV-2 (Gold Standard)', 'Rapid Antigen Test (RAT)', 'Chest HRCT (if SpO2 drops or breathing difficulty occurs)'],
        'warning_signs': [
            "Oxygen saturation (SpO2) falling below 94% on room air",
            "Persistent pain, heaviness, or pressure in the chest",
            "Severe breathlessness or bluish discoloration of lips and face"
        ]
    },

    'pneumonia': {
        'name': 'Pneumonia (निमोनिया / फेफड़ों का संक्रमण)',
        'category': 'Lower Respiratory Infection',
        'keywords': ['pneumonia', 'lung infection', 'chest infection', 'nimoniya'],
        'primary_symptoms': ['cough', 'fever', 'shortness_of_breath'],
        'secondary_symptoms': ['chest_pain', 'chills', 'fatigue', 'sweating'],
        'overview': (
            "Pneumonia is an infection that inflames the air sacs (alveoli) in one or both lungs. "
            "The air sacs may fill with fluid or pus, causing deep cough with green/yellow phlegm, high fever, "
            "shivering chills, and sharp chest discomfort upon breathing or coughing."
        ),
        'causes': "Bacterial (Streptococcus pneumoniae), viral, or fungal infection of lung tissue.",
        'diet_and_home_care': [
            "Stay well-hydrated with warm fluids to help loosen thick mucus.",
            "Eat nutrient-dense, warm, easily swallowable meals.",
            "Steam inhalation with eucalyptus helps relieve bronchial tightness."
        ],
        'precautions': [
            "Seek immediate medical evaluation from a pulmonologist or physician.",
            "Take the complete course of prescribed antibiotics or antivirals.",
            "Rest in an upright or semi-reclined posture to ease breathing.",
            "Avoid exposure to tobacco smoke, dust, and cold damp air."
        ],
        'recommended_tests': ['Chest X-Ray (PA view)', 'Sputum Culture & Gram Stain', 'CBC with ESR/CRP', 'Pulse Oximetry'],
        'warning_signs': [
            "Severe shortness of breath even at rest",
            "SpO2 below 92%, rapid shallow breathing (> 28 breaths/min)",
            "Confusion or altered mental state, especially in elderly patients"
        ]
    },

    'bronchial_asthma': {
        'name': 'Bronchial Asthma (अस्थमा / दमा)',
        'category': 'Chronic Inflammatory Airway Disease',
        'keywords': ['asthma', 'dama', 'wheezing', 'inhaler', 'bronchial asthma'],
        'primary_symptoms': ['shortness_of_breath', 'cough'],
        'secondary_symptoms': ['chest_pain', 'fatigue'],
        'overview': (
            "Asthma is a chronic condition in which the airways become inflamed, swollen, and constricted, "
            "producing extra mucus. This triggers recurrent episodes of wheezing, breathlessness, chest tightness, and coughing."
        ),
        'causes': "Hyper-reactive airways triggered by dust mites, pollens, cold air, smoke, viral infections, or exercise.",
        'diet_and_home_care': [
            "Eat fresh antioxidant-rich fruits, warm herbal teas, and foods rich in Vitamin D and Magnesium.",
            "Avoid iced beverages, cold foods, processed foods with sulfites, and potential food allergens.",
            "Practice pursed-lip breathing and gentle pranayama during remission."
        ],
        'precautions': [
            "Always keep your prescribed rescue inhaler (bronchodilator) accessible at all times.",
            "Identify and strictly avoid environmental triggers (dust, animal dander, air pollution, cigarette smoke).",
            "Use a spacer device with your inhaler for maximum drug delivery to the lungs.",
            "Monitor peak expiratory flow (PEF) with a peak flow meter if recommended."
        ],
        'recommended_tests': ['Spirometry / Pulmonary Function Test (PFT)', 'Allergy Skin Prick Test', 'Chest X-Ray'],
        'warning_signs': [
            "Severe breathlessness where you cannot speak full sentences without pausing",
            "Rescue inhaler provides no relief or relief lasts less than 3 hours",
            "Retraction of neck and chest muscles during breathing with blue lips or fingernails"
        ]
    },

    'uti': {
        'name': 'Urinary Tract Infection - UTI (मूत्र मार्ग संक्रमण / पेशाब में जलन)',
        'category': 'Urological Bacterial Infection',
        'keywords': ['uti', 'urinary tract infection', 'cystitis', 'dysuria'],
        'primary_symptoms': ['burning_urination'],
        'secondary_symptoms': ['fever', 'stomach_pain', 'fatigue', 'chills'],
        'overview': (
            "A Urinary Tract Infection (UTI) occurs when bacteria enter the urinary system, infecting the bladder (cystitis) "
            "or kidneys (pyelonephritis). Classic symptoms include a burning stinging sensation during urination, strong constant "
            "urge to urinate, cloudy urine, and lower pelvic cramping."
        ),
        'causes': "Bacterial proliferation (most commonly Escherichia coli) ascending through the urethra.",
        'diet_and_home_care': [
            "Drink 2.5 to 3 liters of water daily to flush bacteria from the urinary tract.",
            "Unsweetened cranberry juice and barley water (jau ka paani) help reduce bacterial adhesion.",
            "Drink lemon water and coconut water to alkalize the urine.",
            "Avoid alcohol, caffeine, and acidic beverages that irritate the bladder lining."
        ],
        'precautions': [
            "Do not delay or hold urine; empty your bladder completely whenever you feel the urge.",
            "Urinate soon after sexual intercourse to clear potential pathogens.",
            "Wipe from front to back after using the toilet to prevent bacterial transfer.",
            "Complete the entire antibiotic regimen prescribed by your doctor to prevent antibiotic resistance."
        ],
        'recommended_tests': ['Urine Routine & Microscopic Examination (Pus cells, RBCs)', 'Urine Culture & Sensitivity (C&S)', 'Ultrasound KUB (Kidney, Ureter, Bladder)'],
        'warning_signs': [
            "High fever with shivering chills and severe flank or lower back pain (Kidney Infection / Pyelonephritis)",
            "Visible blood in urine (hematuria)",
            "Inability to pass urine despite an urgent feeling"
        ]
    },

    'kidney_stones': {
        'name': 'Kidney Stones / Nephrolithiasis (गुर्दे की पथरी)',
        'category': 'Urological Condition',
        'keywords': ['kidney stone', 'pathri', 'renal calculi', 'gurde ki pathri', 'nephrolithiasis'],
        'primary_symptoms': ['stomach_pain', 'burning_urination'],
        'secondary_symptoms': ['nausea', 'vomiting', 'fever', 'chills'],
        'overview': (
            "Kidney stones are hard mineral deposits that form inside the kidneys. When a stone moves into the ureter, "
            "it causes excruciating, sharp, spasmodic pain in the back and side (flank pain) that radiates to the lower abdomen and groin."
        ),
        'causes': "Dehydration, high dietary intake of oxalates/sodium/animal protein, hypercalcemia, and genetic predisposition.",
        'diet_and_home_care': [
            "Drink 3 to 4 liters of clean water throughout the day to keep urine clear and dilute.",
            "Add lemon juice (citric acid helps inhibit calcium stone formation) to daily drinking water.",
            "Reduce dietary sodium and limit high-oxalate foods (spinach, chocolate, nuts, beetroot) if calcium oxalate stones are present.",
            "Avoid excessive red meat and carbonated soft drinks containing phosphoric acid."
        ],
        'precautions': [
            "Take doctor-prescribed antispasmodics and analgesics during acute colic pain.",
            "Collect and strain any passed stone fragments for laboratory chemical analysis.",
            "Maintain moderate physical activity like walking to assist stone progression.",
            "Consult an urologist for stones larger than 5mm or those causing hydronephrosis."
        ],
        'recommended_tests': ['Non-Contrast CT KUB (Gold standard for stone detection)', 'Ultrasound KUB', 'Urine Routine & Serum Uric Acid / Calcium'],
        'warning_signs': [
            "Inability to tolerate oral fluids or severe uncontrolled pain",
            "Fever and chills accompanying severe flank pain (Urosepsis Medical Emergency)",
            "Total stoppage of urine flow (Anuria)"
        ]
    },

    'migraine': {
        'name': 'Migraine & Tension Headache (माइग्रेन / आधा सीसी का सिर दर्द)',
        'category': 'Neurological Condition',
        'keywords': ['migraine', 'hemicrania', 'adha shishi', 'chronic migraine'],
        'primary_symptoms': ['headache'],
        'secondary_symptoms': ['nausea', 'vomiting', 'dizziness'],
        'overview': (
            "A migraine is a neurological disorder causing severe, throbbing, unilateral (one-sided) headache pain. "
            "It is frequently accompanied by extreme sensitivity to light (photophobia), sound (phonophobia), nausea, "
            "and in some individuals, sensory disturbances known as visual auras."
        ),
        'causes': "Neurovascular inflammation and abnormal brain chemical activity triggered by stress, sleep deficits, hormones, or sensory stimuli.",
        'diet_and_home_care': [
            "Rest in a quiet, dark, well-ventilated, cool room during an attack.",
            "Apply a cold ice pack or warm compress across your forehead and temples.",
            "Sip ginger tea or warm peppermint water to alleviate accompanying nausea.",
            "Stay adequately hydrated, as mild dehydration is a frequent migraine trigger."
        ],
        'precautions': [
            "Maintain a consistent sleep-wake schedule and avoid skipping regular meals.",
            "Identify and log personal triggers (aged cheese, MSG, chocolate, flickering lights, strong perfumes).",
            "Practice deep breathing, progressive muscle relaxation, or yoga.",
            "Take abortive migraine medications (triptans/NSAIDs) at the earliest onset of headache symptoms as prescribed."
        ],
        'recommended_tests': ['Clinical Neurological Examination', 'Brain MRI/CT (to rule out secondary causes if headaches are new or atypical)'],
        'warning_signs': [
            "Sudden, catastrophic 'thunderclap' headache reaching maximum intensity in seconds",
            "Headache accompanied by fever, stiff neck, confusion, or weakness/numbness on one side of the body",
            "Headache following head injury or worsening progressively over weeks"
        ]
    },

    'hypertension': {
        'name': 'Hypertension / High Blood Pressure (उच्च रक्तचाप / हाई बीपी)',
        'category': 'Cardiovascular Condition',
        'keywords': ['hypertension', 'high blood pressure', 'high bp', 'raktchap'],
        'primary_symptoms': ['high_bp'],
        'secondary_symptoms': ['headache', 'dizziness', 'chest_pain', 'fatigue'],
        'overview': (
            "Hypertension is a chronic medical condition where the force of blood against the artery walls is persistently high "
            "(typically 130/80 mmHg or higher). Often termed the 'silent killer' because it has no early symptoms, it significantly "
            "increases the risk of heart disease, stroke, and kidney failure."
        ),
        'causes': "Sedentary lifestyle, high sodium intake, obesity, chronic stress, smoking, alcohol, genetics, and age.",
        'diet_and_home_care': [
            "Adopt the DASH diet: rich in fruits, vegetables, whole grains, nuts, and low-fat dairy.",
            "Severely restrict table salt and high-sodium foods (pickles, papads, canned food, chips) to < 2g sodium/day.",
            "Include potassium-rich foods like bananas, coconut water, spinach, and sweet potatoes.",
            "Engage in at least 30-45 minutes of moderate aerobic exercise (brisk walking) 5 days a week."
        ],
        'precautions': [
            "Check and log blood pressure readings at the same time each day using a validated monitor.",
            "Take prescribed antihypertensive medications consistently; never stop without consulting your doctor.",
            "Avoid smoking, limit alcohol, and practice daily stress reduction (meditation, deep breathing).",
            "Maintain a healthy body weight and waist circumference."
        ],
        'recommended_tests': ['24-Hour Blood Pressure Monitoring', 'Kidney Function Test (KFT / Serum Creatinine)', 'Lipid Profile', 'ECG', 'Urine Routine for Albumin'],
        'warning_signs': [
            "Sudden severe explosive headache with blurred vision or confusion",
            "Chest pain, shortness of breath, or numbness in arms/face (Hypertensive Crisis)",
            "BP reading above 180/120 mmHg"
        ]
    },

    'type2_diabetes': {
        'name': 'Type 2 Diabetes Mellitus (डायबिटीज / मधुमेह)',
        'category': 'Metabolic & Endocrine Condition',
        'keywords': ['diabetes', 'sugar', 'blood sugar', 'sugar level', 'sugar patient', 'madhumeh', 'sugar bimari', 'hba1c'],
        'primary_symptoms': ['high_blood_sugar'],
        'secondary_symptoms': ['fatigue', 'burning_urination', 'loss_of_appetite'],
        'overview': (
            "Type 2 diabetes is a chronic metabolic disorder characterized by elevated blood glucose levels due to insulin "
            "resistance or relative insulin deficiency. Symptoms include excessive thirst (polydipsia), frequent urination (polyuria), "
            "unexplained weight loss, increased hunger, and fatigue."
        ),
        'causes': "Insulin resistance driven by genetics, abdominal obesity, physical inactivity, and poor dietary patterns.",
        'diet_and_home_care': [
            "Eat complex, low-glycemic carbs: whole grains (millets, oats, brown rice, barley) and high fiber.",
            "Avoid white sugar, sweets, sugary beverages, packaged juices, and refined flour (maida).",
            "Include fenugreek (methi) seeds, bitter gourd (karela), and amla in your daily routine.",
            "Consume adequate lean proteins (dal, beans, sprouts, paneer, tofu) to stabilize post-meal glucose spikes."
        ],
        'precautions': [
            "Regularly monitor Fasting and Postprandial Blood Sugar with a home glucometer.",
            "Get HbA1c checked every 3 to 6 months (target is generally below 7.0%).",
            "Inspect feet daily for small cuts, blisters, or sores, as diabetic neuropathy reduces sensation.",
            "Never skip meals or anti-diabetic medications/insulin without clinical advice."
        ],
        'recommended_tests': ['Fasting Blood Sugar (FBS) & PPBS', 'HbA1c (Glycated Hemoglobin)', 'Lipid Profile', 'Kidney Function Test & Urine Microalbumin'],
        'warning_signs': [
            "Extreme drowsiness, fruity breath odor, rapid breathing, and confusion (Diabetic Ketoacidosis)",
            "Blood glucose dropping below 70 mg/dL with tremors, sweating, and heart racing (Hypoglycemia - consume glucose immediately!)",
            "Non-healing wounds or deep foot ulcers"
        ]
    },

    'jaundice_hepatitis': {
        'name': 'Jaundice & Hepatitis (पीलिया / हेपेटाइटिस - लिवर संक्रमण)',
        'category': 'Hepatic & Biliary Disorder',
        'keywords': ['jaundice', 'piliya', 'hepatitis', 'liver infection', 'cirrhosis'],
        'primary_symptoms': ['yellow_eyes_skin'],
        'secondary_symptoms': ['fatigue', 'loss_of_appetite', 'nausea', 'vomiting', 'stomach_pain'],
        'overview': (
            "Jaundice is the yellowing of the skin, mucous membranes, and whites of the eyes caused by elevated levels "
            "of bilirubin in the blood. It often signifies acute hepatitis (viral liver infection), biliary tract obstruction (gallstones), "
            "or drug-induced liver injury."
        ),
        'causes': "Hepatitis viruses (A, E from contaminated food/water; B, C through blood), alcohol abuse, or gallstones.",
        'diet_and_home_care': [
            "Eat a high-carbohydrate, low-fat diet: sugarcane juice (from hygienic sources), boiled radish, papaya, and boiled rice.",
            "Drink plenty of clean boiled water, tender coconut water, and glucose water.",
            "Strictly avoid all alcohol, fried foods, spices, heavy gravies, and unprescribed supplements.",
            "Ensure complete physical rest to support liver cell regeneration."
        ],
        'precautions': [
            "Consult a gastroenterologist or hepatologist for precise diagnosis and viral markers.",
            "Avoid self-medication, especially paracetamol in high doses, which is metabolized by the liver.",
            "Practice strict hand hygiene and ensure safe drinking water.",
            "Separate personal items (towels, razors) to prevent viral transmission."
        ],
        'recommended_tests': ['Liver Function Test (LFT - Total & Direct Bilirubin, SGOT/AST, SGPT/ALT, Alk Phos)', 'Viral Hepatitis Serology (Anti-HAV, HBsAg, Anti-HCV, Anti-HEV)', 'Abdominal Ultrasound'],
        'warning_signs': [
            "Altered mental status, confusion, slurred speech, or extreme sleepiness (Hepatic Encephalopathy)",
            "Abdominal swelling (Ascites) or swollen feet",
            "Vomiting blood or passing black tarry stools"
        ]
    },

    'arthritis': {
        'name': 'Arthritis & Joint Disorders (गठिया / जोड़ों का दर्द)',
        'category': 'Musculoskeletal Disorder',
        'keywords': ['arthritis', 'gathiya', 'osteoarthritis', 'rheumatoid arthritis', 'sandhivata'],
        'primary_symptoms': ['joint_pain'],
        'secondary_symptoms': ['fatigue', 'body_pain'],
        'overview': (
            "Arthritis encompasses over 100 conditions causing joint inflammation, stiffness, and degeneration. "
            "Osteoarthritis involves the wear and tear of joint cartilage (especially in knees and hips), while Rheumatoid "
            "Arthritis is an autoimmune disease causing symmetric joint swelling and prolonged morning stiffness."
        ),
        'causes': "Age-related cartilage degradation, joint injury, autoimmune attack on synovium, or high uric acid (Gout).",
        'diet_and_home_care': [
            "Consume anti-inflammatory foods: turmeric milk (haldi doodh), ginger, walnuts, flaxseeds, and green leafy vegetables.",
            "Maintain moderate low-impact exercise: swimming, gentle cycling, and isometric knee strengthening.",
            "Apply warm compresses to loosen stiff joints and cold packs to soothe acute flare-ups.",
            "Maintain optimal body weight to significantly reduce mechanical stress on knees and hips."
        ],
        'precautions': [
            "Consult a rheumatologist or orthopedist for accurate categorization and targeted treatment.",
            "Avoid high-impact jumping or prolonged squatting if knee osteoarthritis is advanced.",
            "Use ergonomic footwear with cushioned soles and knee supports when walking long distances.",
            "Take prescribed Disease-Modifying Anti-Rheumatic Drugs (DMARDs) or analgesics strictly as directed."
        ],
        'recommended_tests': ['X-Ray of affected joints', 'Rheumatoid Factor (RA Factor) & Anti-CCP', 'Serum Uric Acid', 'ESR and CRP'],
        'warning_signs': [
            "A single hot, intensely red, exquisitely tender swollen joint with high fever (Septic Arthritis Emergency)",
            "Sudden loss of mobility or inability to bear weight",
            "Numbness or pins-and-needles sensation spreading down limbs"
        ]
    },

    'eczema_skin_allergy': {
        'name': 'Skin Allergy, Eczema & Dermatitis (त्वचा एलर्जी / दाद, खाज, खुजली)',
        'category': 'Dermatological Condition',
        'keywords': ['eczema', 'dermatitis', 'skin allergy', 'urticaria', 'psoriasis'],
        'primary_symptoms': ['rash'],
        'secondary_symptoms': ['body_pain'],
        'overview': (
            "Dermatitis and eczema refer to inflammatory conditions of the skin characterized by redness, swelling, "
            "intense itching, papules, flaking, or allergic hives (urticaria). Triggers include contact allergens, stress, and dry skin."
        ),
        'causes': "Compromised skin barrier, atopic predisposition, contact with harsh detergents/chemicals, pollen, or fungal infection.",
        'diet_and_home_care': [
            "Apply unfragranced, thick moisturizing cream or pure virgin coconut oil immediately after bathing.",
            "Bathe with lukewarm water rather than hot water, using gentle syndet soap-free bars.",
            "Wear loose, breathable 100% cotton clothing; avoid synthetic and wool fabrics next to skin.",
            "Drink plenty of water and eat foods rich in Vitamin E, Omega-3, and Zinc."
        ],
        'precautions': [
            "Do not scratch the lesions, as scratching breaks the skin and causes secondary bacterial infections; keep fingernails trimmed short.",
            "Avoid scented body washes, harsh detergents, fabric softeners, and chemical perfumes.",
            "Use doctor-prescribed mild topical corticosteroids or calamine lotion for itch relief.",
            "Identify and eliminate contact allergens or suspect food items."
        ],
        'recommended_tests': ['Skin Prick Allergy Test', 'Serum Total IgE', 'Skin Scraping for Fungus (KOH Mount)'],
        'warning_signs': [
            "Signs of secondary bacterial infection: yellow crusting, pus oozing, or red warmth spreading",
            "Sudden widespread hives with swelling of lips/tongue or throat tightness (Anaphylaxis Emergency)",
            "Rash covering over 50% of the body with high fever"
        ]
    },

    'hypothyroidism_metabolic': {
        'name': 'Hypothyroidism & Metabolic Weight Gain (हाइपोथायरायडिज्म / असामान्य वजन बढ़ना)',
        'category': 'Endocrine & Metabolic Disorder',
        'keywords': ['weight gain', 'weight gaining', 'hypothyroidism', 'thyroid', 'vazan badhna', 'slow metabolism', 'weight increase'],
        'primary_symptoms': ['weight_gain', 'fatigue'],
        'secondary_symptoms': ['constipation', 'cold', 'body_pain', 'joint_pain'],
        'overview': (
            "Unexplained or progressive weight gain is commonly linked with Hypothyroidism (underactive thyroid gland), "
            "where inadequate thyroid hormone production slows down basal metabolic rate. Other contributing metabolic "
            "factors include insulin resistance, hormonal imbalances (such as PCOS in women), and fluid retention."
        ),
        'causes': "Autoimmune thyroiditis (Hashimoto's), iodine deficiency, hormonal imbalances (PCOS/Cushing's), metabolic syndrome, or sedentary lifestyle.",
        'diet_and_home_care': [
            "Consume a nutrient-dense, high-fiber, balanced diet: leafy greens, seasonal fruits, lean proteins (lentils, paneer, sprouts), and whole grains.",
            "Avoid refined sugars, sweetened beverages, white flour (maida), and excessive raw goitrogens (cabbage/cauliflower in huge raw quantities).",
            "Include selenium and zinc-rich foods (brazil nuts, pumpkin seeds, whole grains) to support thyroid hormone synthesis.",
            "Maintain 40-45 minutes of daily physical exercise combining brisk walking and light resistance training."
        ],
        'precautions': [
            "Get a complete Thyroid Profile (TSH, Free T3, Free T4) blood test done in the morning on an empty stomach.",
            "Consult an endocrinologist or general physician for thyroid and metabolic evaluation.",
            "If prescribed thyroid hormone replacement (Levothyroxine), take it first thing in the morning with plain water, 30-60 minutes before tea or breakfast.",
            "Ensure 7 to 8 hours of restorative sleep, as sleep deprivation disrupts hunger-regulating hormones."
        ],
        'recommended_tests': ['Thyroid Profile (TSH, FT3, FT4)', 'Lipid Profile', 'Fasting Blood Sugar & HbA1c', 'Complete Blood Count (CBC)'],
        'warning_signs': [
            "Sudden severe swelling of lower legs, face, or abdomen (pitting edema)",
            "Weight gain accompanied by severe breathlessness or chest tightness",
            "Extreme mental confusion, slowed speech, or extreme cold intolerance"
        ]
    }
}

def extract_symptoms_from_text(text):
    """
    Extracts all recognized symptoms from text across English, Hindi, and Hinglish.
    Returns list of standard symptom keys.
    """
    if not text:
        return []
    clean_text = ' ' + text.lower().strip() + ' '
    clean_text = re.sub(r'[\r\n\t,.;:!?\-/]+', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)

    matched = []
    for sym_key, patterns in SYMPTOM_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, clean_text, flags=re.IGNORECASE):
                matched.append(sym_key)
                break
    return matched

def match_disease_from_query(text, detected_symptoms):
    """
    Matches the best disease from either explicit query keywords or detected symptoms.
    Uses weighted scoring prioritizing primary symptoms, explicit mentions, and secondary symptoms.
    """
    clean_text = ' ' + text.lower().strip() + ' '
    clean_text = re.sub(r'[\r\n\t,.;:!?\-/]+', ' ', clean_text)

    # 1. Check for explicit disease keyword mention in text
    for dis_id, data in CLINICAL_DISEASES.items():
        for kw in data['keywords']:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, clean_text, flags=re.IGNORECASE):
                return dis_id, data, "keyword_match"

    # 2. Score based on detected symptoms
    if not detected_symptoms:
        return None, None, "no_symptoms"

    scored_diseases = []
    for dis_id, data in CLINICAL_DISEASES.items():
        score = 0
        primary_hits = 0
        for s in detected_symptoms:
            if s in data['primary_symptoms']:
                score += 5.0
                primary_hits += 1
            elif s in data['secondary_symptoms']:
                score += 1.5

        if primary_hits == 0:
            continue

        # Specificity boost: If user reported 1 symptom and disease is specifically focused on that 1 symptom
        # (e.g. headache -> headache_migraine, weight_gain -> hypothyroidism_metabolic, fever -> viral_fever)
        if len(data['primary_symptoms']) == 1 and primary_hits == 1 and len(detected_symptoms) == 1:
            score += 18.0

        # CLINICAL DISQUALIFICATIONS:
        # 1. Dengue, Malaria, Typhoid MUST have fever! Never diagnose Dengue/Malaria for isolated headache or pain!
        if dis_id in ['dengue', 'malaria', 'typhoid'] and 'fever' not in detected_symptoms:
            continue

        # 2. Dengue requires fever PLUS at least one of (body_pain, joint_pain, rash)
        if dis_id == 'dengue' and ('body_pain' not in detected_symptoms and 'joint_pain' not in detected_symptoms and 'rash' not in detected_symptoms):
            score -= 6.0

        # 3. Malaria requires fever PLUS (chills or sweating)
        if dis_id == 'malaria' and ('chills' not in detected_symptoms and 'sweating' not in detected_symptoms):
            score -= 6.0

        # 4. Critical cardiac alert requires chest pain
        if dis_id == 'heart_attack_warning':
            if 'chest_pain' not in detected_symptoms:
                continue
            if 'sweating' in detected_symptoms or 'shortness_of_breath' in detected_symptoms:
                score += 15.0
                primary_hits += 2

        # 5. Kidney stones requires stomach or back pain
        if dis_id == 'kidney_stones' and 'stomach_pain' not in detected_symptoms:
            continue

        # Bonus if multiple primary symptoms hit
        if primary_hits >= 2:
            score += (primary_hits * 3.5)

        scored_diseases.append((score, primary_hits, dis_id, data))

    if scored_diseases:
        scored_diseases.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_score, top_hits, top_id, top_data = scored_diseases[0]
        if top_score >= 3:
            return top_id, top_data, "symptom_match"

    return None, None, "insufficient_match"

def generate_clinical_response(query_text):
    """
    Generates a complete, comprehensive, clinical-grade medical assessment
    for any question, symptom list, or disease inquiry in English, Hindi, or Hinglish.
    """
    text = query_text.strip()
    detected_symptoms = extract_symptoms_from_text(text)
    dis_id, dis_data, match_type = match_disease_from_query(text, detected_symptoms)

    detected_labels = [SYMPTOM_DISPLAY.get(s, s.title()) for s in detected_symptoms]

    if dis_data:
        condition_title = dis_data['name']
        overview = dis_data['overview']
        causes = dis_data['causes']
        diet_points = "\n".join([f"- {d}" for d in dis_data['diet_and_home_care']])
        prec_points = "\n".join([f"- {p}" for p in dis_data['precautions']])
        tests_points = "\n".join([f"- {t}" for t in dis_data.get('recommended_tests', ['Complete Blood Count (CBC)', 'Clinical physician evaluation'])])
        warn_points = "\n".join([f"- 🚨 {w}" for w in dis_data['warning_signs']])

        sym_section = ""
        if detected_labels:
            sym_section = f"**Identified Symptoms:**\n" + "\n".join([f"- {s}" for s in detected_labels]) + "\n\n"

        response = (
            f"**Condition / Clinical Assessment:** {condition_title}\n\n"
            f"{sym_section}"
            f"**Medical Overview:**\n"
            f"{overview}\n\n"
            f"**Probable Causes & Transmission:**\n"
            f"{causes}\n\n"
            f"**Dietary Recommendations & Home Care:**\n"
            f"{diet_points}\n\n"
            f"**Key Health Precautions & Self-Care:**\n"
            f"{prec_points}\n\n"
            f"**Recommended Diagnostic Medical Tests:**\n"
            f"{tests_points}\n\n"
            f"**When to Seek Immediate Medical Attention (Red Flags):**\n"
            f"{warn_points}\n\n"
            f"*(Disclaimer: Niramaya provides AI-guided clinical insights. This information does not replace formal in-person examination or prescription by a qualified medical practitioner.)*"
        )
        return response

    elif detected_symptoms:
        primary_sym_text = ", ".join(detected_labels)
        response = (
            f"**Clinical Assessment of Reported Symptoms:**\n\n"
            f"**Detected Symptoms:**\n"
            + "\n".join([f"- {s}" for s in detected_labels]) + "\n\n"
            f"**Medical Overview:**\n"
            f"You have reported symptoms ({primary_sym_text}) that commonly indicate an acute viral, bacterial, or physiological reaction. "
            f"These symptoms warrant close observation of their intensity, onset, and progression.\n\n"
            f"**Immediate Home Care & Supportive Measures:**\n"
            f"- Rest adequately in a well-ventilated, comfortable room.\n"
            f"- Ensure optimal hydration by drinking 2.5 to 3 liters of fluids (boiled warm water, ORS, herbal infusions, coconut water).\n"
            f"- Consume light, warm, freshly prepared home-cooked food (khichdi, dalia, warm soup); avoid spicy, oily, or unpasteurized food.\n"
            f"- Avoid self-prescribing antibiotics or strong painkillers without verified clinical guidance.\n\n"
            f"**Key Health Precautions:**\n"
            f"- Log your symptoms, body temperature, and pulse rate twice daily.\n"
            f"- If experiencing fever or pain, consult a physician or pharmacist regarding appropriate antipyretics (e.g. Paracetamol).\n"
            f"- Maintain strict personal and hand hygiene to prevent transmitting potential infections to family members.\n"
            f"- Do not exert yourself physically until symptoms resolve.\n\n"
            f"**Recommended Diagnostic Tests:**\n"
            f"- Complete Blood Count (CBC) with Differential Count\n"
            f"- Urine Routine Examination (if urinary or abdominal symptoms present)\n"
            f"- Physical consultation with a general physician for targeted diagnosis\n\n"
            f"**When to Seek Immediate Medical Attention (Red Flags):**\n"
            f"- 🚨 High persistent fever (> 102°F) that does not reduce with standard medication\n"
            f"- 🚨 Severe shortness of breath, chest tightness, or blueness of lips\n"
            f"- 🚨 Uncontrolled vomiting, severe persistent abdominal pain, or confusion\n"
            f"- 🚨 Inability to retain liquids leading to extreme dehydration\n\n"
            f"*(Disclaimer: Niramaya provides AI-guided clinical insights. This information does not replace formal examination by a licensed physician.)*"
        )
        return response

    else:
        response = (
            f"**Health Information & Guidance:**\n\n"
            f"**Topic / Inquiry:** {text.title()}\n\n"
            f"**Medical Overview:**\n"
            f"Niramaya Health AI assists in symptom assessment, health education, and self-care precautions. "
            f"Regarding your query on '{text}', optimal health relies on early symptom recognition, clinical verification, "
            f"and evidence-based lifestyle habits.\n\n"
            f"**General Health Recommendations:**\n"
            f"- Maintain consistent daily hydration (minimum 2 to 3 liters of water).\n"
            f"- Consume a balanced diet rich in dietary fiber, whole grains, colorful vegetables, and adequate protein.\n"
            f"- Engage in at least 30 minutes of moderate physical activity (such as brisk walking) most days of the week.\n"
            f"- Aim for 7 to 8 hours of restorative sleep each night.\n"
            f"- Schedule regular preventative health check-ups (Blood Pressure, Blood Sugar, CBC, Lipid Profile).\n\n"
            f"**Key Health Precautions:**\n"
            f"- If you are experiencing specific symptoms (such as fever, headache, body pain, cough, or stomach pain), please describe them in detail.\n"
            f"- Never consume unprescribed medications or antibiotics without clinical diagnosis.\n"
            f"- Seek prompt medical consultation if you experience acute, worsening, or persistent discomfort.\n\n"
            f"*(Disclaimer: Niramaya provides AI-guided clinical insights. This does not replace formal consultation with a physician.)*"
        )
        return response

def get_lrv1_prediction(query_text):
    """
    Returns structured data for LRv1 endpoint:
    { predicted_disease, matched_symptoms, description }
    """
    detected_symptoms = extract_symptoms_from_text(query_text)
    dis_id, dis_data, match_type = match_disease_from_query(query_text, detected_symptoms)
    detected_labels = [SYMPTOM_DISPLAY.get(s, s.title()) for s in detected_symptoms]

    if dis_data:
        return {
            'predicted_disease': dis_data['name'],
            'matched_symptoms': detected_labels if detected_labels else [query_text.title()],
            'description': dis_data['overview']
        }
    elif detected_symptoms:
        return {
            'predicted_disease': "Acute Symptom Cluster (Physician Review Advised)",
            'matched_symptoms': detected_labels,
            'description': f"Reported symptoms ({', '.join(detected_labels)}) indicate an active physiological or infectious response. Please evaluate symptom progression and consult a medical practitioner."
        }
    else:
        return {
            'predicted_disease': query_text.title() or "Clinical Health Inquiry",
            'matched_symptoms': [query_text] if query_text else [],
            'description': f"Health guidance regarding '{query_text}'. Please monitor symptom duration, maintain adequate hydration, and consult a qualified healthcare provider."
        }

def get_lrv2_prediction(query_text):
    """
    Returns structured data for LRv2 endpoint:
    { predicted_disease, matched_symptoms, description, precautions }
    """
    detected_symptoms = extract_symptoms_from_text(query_text)
    dis_id, dis_data, match_type = match_disease_from_query(query_text, detected_symptoms)
    detected_labels = [SYMPTOM_DISPLAY.get(s, s.title()) for s in detected_symptoms]

    if dis_data:
        return {
            'predicted_disease': dis_data['name'],
            'matched_symptoms': detected_labels if detected_labels else [query_text.title()],
            'description': dis_data['overview'],
            'precautions': dis_data['precautions']
        }
    elif detected_symptoms:
        return {
            'predicted_disease': "Acute Symptom Cluster (Physician Review Advised)",
            'matched_symptoms': detected_labels,
            'description': f"Reported symptoms ({', '.join(detected_labels)}) indicate an active physiological or infectious response. Clinical correlation is recommended.",
            'precautions': [
                "Maintain complete physical rest and avoid strenuous exertion",
                "Ensure robust hydration with boiled water, ORS, or electrolyte solutions",
                "Consume light, warm, non-spicy, easily digestible home-cooked meals",
                "Track body temperature and seek medical attention if symptoms persist beyond 48 hours"
            ]
        }
    else:
        return {
            'predicted_disease': query_text.title() or "Clinical Health Inquiry",
            'matched_symptoms': [query_text] if query_text else [],
            'description': f"Health guidance regarding '{query_text}'. A physical evaluation is recommended for persistent symptoms.",
            'precautions': [
                "Ensure proper rest and stay well-hydrated throughout the day",
                "Maintain a balanced, easily digestible diet rich in vitamins",
                "Monitor symptoms closely and track their severity and duration",
                "Consult a qualified physician or healthcare provider for clinical diagnosis"
            ]
        }
