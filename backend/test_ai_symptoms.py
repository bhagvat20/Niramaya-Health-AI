import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ai_general_questions_are_strictly_rejected(client):
    """Verifies that non-health/general ChatGPT-style questions are strictly refused across all AI endpoints."""
    non_health_queries = [
        "what is the capital of France",
        "how to write python code",
        "tell me a funny joke",
        "who is the prime minister of india",
        "how to bake a chocolate cake",
        "what is the score in cricket match",
        "can you solve 25 times 40",
        "what year is it",
        "tell me about spain",
        "how to learn english",
        "tell me about galaxy",
        "who is my teacher",
        "can we chat like chatgpt",
        "write an email to my boss",
        "i have a laptop problem",
        "hi tell me a joke",
        "how to switch on tv",
        "what is the weather today it is cold"
    ]
    for query in non_health_queries:
        # BioGPT
        res_bio = client.post('/askbiogpt', json={'question': query})
        assert res_bio.status_code == 200
        assert "Medical & Symptom Checker Domain Restriction" in res_bio.get_json()['answer'], f"BioGPT failed to reject: {query}"

        # Gemini
        res_gem = client.post('/askgemini', json={'question': query})
        assert res_gem.status_code == 200
        assert "Medical & Symptom Checker Domain Restriction" in res_gem.get_json()['answer'], f"Gemini failed to reject: {query}"

        # LRv1
        res_lrv1 = client.post('/asklrv1', json={'symptoms': query})
        assert res_lrv1.status_code == 200
        assert res_lrv1.get_json()['predicted_disease'] == "Non-Health Query", f"LRv1 failed to reject: {query}"

        # LRv2
        res_lrv2 = client.post('/asklrv2', json={'symptoms': query})
        assert res_lrv2.status_code == 200
        assert res_lrv2.get_json()['predicted_disease'] == "Non-Health Query", f"LRv2 failed to reject: {query}"

def test_ai_symptoms_are_properly_accepted_and_answered(client):
    """Verifies that genuine health symptoms in English and Hindi are accepted and answered."""
    symptom_queries = [
        "Digestive Issues",
        "I have severe fever and headache for 2 days",
        "vomiting and loose motion with stomach pain",
        "chest pain and shortness of breath",
        "skin rash with severe itching",
        "mujhe bukhar aur pet dard hai"
    ]
    for query in symptom_queries:
        # BioGPT: Biomedical knowledge & pathophysiology
        res_bio = client.post('/askbiogpt', json={'question': query})
        assert res_bio.status_code == 200
        bio_data = res_bio.get_json()
        assert "Pathophysiology" in bio_data['answer'] or "Biomedical" in bio_data['answer']

        # Gemini: Health Assistant guidance + follow-up questions (distinct from BioGPT!)
        res_gem = client.post('/askgemini', json={'question': query})
        assert res_gem.status_code == 200
        gem_data = res_gem.get_json()
        assert "Health Assistant" in gem_data['answer'] or "Follow-Up" in gem_data['answer']
        assert bio_data['answer'] != gem_data['answer'], "BioGPT and Gemini must produce differentiated outputs"

        # LRv1: Independent Logistic Regression prediction with real probabilities
        res_lrv1 = client.post('/asklrv1', json={'symptoms': query})
        assert res_lrv1.status_code == 200
        v1 = res_lrv1.get_json()
        assert v1['predicted_disease'] != "Non-Health Query"
        if v1.get('inference_status') == 'success':
            assert len(v1['top_predictions']) > 0
            assert 0 < v1['top_probability'] <= 100.0
            assert sum(p['probability'] for p in v1['top_predictions']) <= 100.05

        # LRv2: Independent Random Forest prediction with real probabilities & precautions
        res_lrv2 = client.post('/asklrv2', json={'symptoms': query})
        assert res_lrv2.status_code == 200
        v2 = res_lrv2.get_json()
        assert v2['predicted_disease'] != "Non-Health Query"
        assert len(v2.get('precautions', [])) > 0
        if v2.get('inference_status') == 'success':
            assert len(v2['top_predictions']) > 0
            assert 0 < v2['top_probability'] <= 100.0
            assert sum(p['probability'] for p in v2['top_predictions']) <= 100.05


def test_askall_four_models_differentiation_and_lrv1_vs_lrv2_comparison(client):
    """Verifies /askall returns 4 unique, non-duplicated model outputs plus an authentic LRv1 vs LRv2 comparison."""
    res = client.post('/askall', json={'question': 'fever, headache, cough, vomiting'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['is_health_related'] is True

    # 1. BioGPT: Biomedical knowledge
    assert data['biogpt']['model'] == 'BioGPT'
    assert 'Pathophysiology' in data['biogpt']['answer']

    # 2. Gemini: Health Assistant + follow-up questions
    assert data['gemini']['model'] == 'Gemini'
    assert 'Follow-Up Questions' in data['gemini']['answer']
    assert len(data['gemini'].get('follow_up_questions', [])) >= 2

    # Ensure BioGPT and Gemini are completely distinct (no duplicate responses)
    assert data['biogpt']['answer'] != data['gemini']['answer']

    # 3. LRv1: Independent Logistic Regression with real predict_proba
    lrv1 = data['lrv1']
    assert lrv1['model'] == 'LRv1'
    assert 'Logistic Regression' in lrv1['algorithm']
    assert lrv1['inference_status'] == 'success'
    assert len(lrv1['top_predictions']) == 5
    assert 0 < lrv1['top_probability'] <= 100.0

    # 4. LRv2: Independent Random Forest with real predict_proba
    lrv2 = data['lrv2']
    assert lrv2['model'] == 'LRv2'
    assert 'Random Forest' in lrv2['algorithm']
    assert lrv2['inference_status'] == 'success'
    assert len(lrv2['top_predictions']) >= 1
    assert 0 < lrv2['top_probability'] <= 100.0
    assert len(lrv2['precautions']) > 0

    # 5. Authentic LRv1 vs LRv2 Comparison section
    comp = data['comparison']
    assert comp['agreement_status'] in ('Full Agreement', 'Partial Agreement', 'Disagreement')
    assert comp['lrv1_summary']['predicted_disease'] == lrv1['predicted_disease']
    assert comp['lrv2_summary']['predicted_disease'] == lrv2['predicted_disease']
    assert comp['lrv1_summary']['top_probability'] == lrv1['top_probability']
    assert comp['lrv2_summary']['top_probability'] == lrv2['top_probability']
    assert len(comp['comparison_notes']) > 20

def test_ai_greetings_guide_user_to_enter_symptoms(client):
    """Verifies that greetings guide the user specifically to enter symptoms."""
    for greet in ["hello", "hi", "namaste", "good morning"]:
        res = client.post('/askbiogpt', json={'question': greet})
        assert res.status_code == 200
        data = res.get_json()
        assert "Niramaya AI Health Assistant" in data['answer']
        assert "symptom" in data['answer'].lower()

def test_system_status_and_health_endpoints(client):
    """Verifies that the fast public health check endpoints return instantly with 200 OK."""
    for endpoint in ['/api/status', '/health', '/system/status']:
        res = client.get(endpoint)
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'healthy'
        assert data['online'] is True

def test_ai_different_symptoms_give_distinct_customized_answers(client):
    """Verifies that BioGPT (biomedical) and Gemini (assistant guidance) give distinct, symptom-specific answers."""
    bio_digestive = client.post('/askbiogpt', json={'question': 'Digestive Issues'}).get_json()['answer']
    bio_throat = client.post('/askbiogpt', json={'question': 'sore throat'}).get_json()['answer']
    bio_multi = client.post('/askbiogpt', json={'question': 'fever and cough'}).get_json()['answer']

    gem_digestive = client.post('/askgemini', json={'question': 'Digestive Issues'}).get_json()['answer']
    gem_throat = client.post('/askgemini', json={'question': 'sore throat'}).get_json()['answer']

    # 1. BioGPT: Biomedical terminology & pathophysiology per condition
    assert "Gastrointestinal" in bio_digestive or "Dyspepsia" in bio_digestive
    assert "dysbiosis" in bio_digestive.lower() or "mucosal" in bio_digestive.lower() or "gerd" in bio_digestive.lower()
    assert "Pharyngitis" in bio_throat or "Throat" in bio_throat
    assert "Multi-System" in bio_multi or ("Pyrexia" in bio_multi and "Respiratory" in bio_multi)

    # 2. Gemini: Practical self-care, home remedies & follow-up questions per condition
    assert "curd" in gem_digestive.lower() or "probiotic" in gem_digestive.lower() or "fennel" in gem_digestive.lower()
    assert "gargle" in gem_throat.lower() or "honey" in gem_throat.lower() or "saline" in gem_throat.lower()
    assert "Follow-Up Questions" in gem_digestive

    # 3. All responses must be completely distinct across symptoms AND across models
    assert bio_digestive != bio_throat
    assert bio_throat != bio_multi
    assert bio_digestive != gem_digestive
    assert bio_throat != gem_throat


def test_registration_and_password_reset_otp_flow(client, monkeypatch):
    """Verifies user registration, duplicate detection, email-only OTP (no API leak), wrong OTP rejection, and password reset."""
    import time
    from routes import password_reset_API

    sent_records = []
    def fake_send_otp_email(email, otp):
        sent_records.append((email, otp))
        return True, "smtp:587"

    monkeypatch.setattr(password_reset_API, "send_otp_email", fake_send_otp_email)
    test_email = f"verify_user_{int(time.time() * 1000)}@example.com"

    # 1. Register new user
    reg_res = client.post('/register', json={
        'fname': 'Test Patient',
        'email': test_email,
        'password': 'OldPassword123'
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.get_json()
    assert reg_data['success'] is True
    acc_id = reg_data['account_id']

    # 2. Duplicate registration returns clean 400
    dup_res = client.post('/register', json={
        'fname': 'Test Patient',
        'email': test_email,
        'password': 'OldPassword123'
    })
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.get_json()['message'].lower()

    # 3. Forgot password sends OTP via email and does NOT leak OTP in JSON response
    fp_res = client.post('/forgotpassword', json={'email': test_email.upper()})
    assert fp_res.status_code == 200
    fp_data = fp_res.get_json()
    assert fp_data['success'] is True
    assert fp_data['email_sent'] is True
    assert 'otp' not in fp_data
    assert str(fp_data['account_id']) == str(acc_id)
    assert len(sent_records) == 1
    otp = sent_records[0][1]
    assert otp and len(otp) == 6

    # 4. Wrong OTP is rejected server-side
    bad_reset = client.post('/resetpassword', json={
        'account_id': acc_id,
        'otp': '000000' if otp != '000000' else '999999',
        'new_password': 'NewPassword456'
    })
    assert bad_reset.status_code == 400

    # 5. Correct OTP resets password
    good_reset = client.post('/resetpassword', json={
        'account_id': acc_id,
        'otp': otp,
        'new_password': 'NewPassword456'
    })
    assert good_reset.status_code == 200
    assert good_reset.get_json()['success'] is True

    # 6. Login works with the newly reset password
    login_res = client.post('/userlogin', json={
        'email': test_email,
        'password': 'NewPassword456'
    })
    assert login_res.status_code == 200
    assert login_res.get_json()['success'] is True

    # Clean up test user from DB
    from db_config import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset_otps WHERE account_id = %s", (int(acc_id),))
    cur.execute("DELETE FROM account_tbl WHERE account_id = %s", (int(acc_id),))
    conn.commit()
    cur.close()
    conn.close()


def test_verify_human_and_theme_files():
    """Verifies verify_human.html supports unified dark/light theme and no duplicate click handlers remain."""
    import os
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    with open(os.path.join(frontend_dir, 'verify_human.html'), 'r', encoding='utf-8') as f:
        vh = f.read()
    assert 'theme.js' in vh
    assert ':root.light' in vh
    assert ':root.dark' in vh
    assert 'id="theme-toggle"' in vh

    for fname in ('about.html', 'our_model.html', 'wellness_tips.html', 'script.js'):
        with open(os.path.join(frontend_dir, fname), 'r', encoding='utf-8') as f:
            content = f.read()
        assert "themeToggleButton.addEventListener('click'" not in content, f"Duplicate theme listener in {fname}"


def test_chat_history_strict_isolation_per_logged_in_family_user(client):
    """Verifies guest/invalid accounts cannot save history and each logged-in user only sees their own history."""
    import time
    ts = int(time.time() * 1000)

    # 1. Guest / non-existent account cannot save chat into another user's account
    guest_save = client.post('/savechat', json={
        'account_id': 99999999,
        'user_input': 'guest headache',
        'bot_response': 'guest answer',
        'model': 'BioGPT'
    })
    assert guest_save.status_code == 404

    # 2. Register two separate family users
    r1 = client.post('/register', json={'fname': 'FamilyOne', 'email': f'fam1_{ts}@example.com', 'password': 'Password123'})
    r2 = client.post('/register', json={'fname': 'FamilyTwo', 'email': f'fam2_{ts}@example.com', 'password': 'Password123'})
    acc1 = int(r1.get_json()['account_id'])
    acc2 = int(r2.get_json()['account_id'])

    # 3. Save a private chat for FamilyOne only
    save1 = client.post('/savechat', json={
        'account_id': acc1,
        'user_input': 'private fever symptom family one',
        'bot_response': 'clinical advice one',
        'model': 'BioGPT'
    })
    assert save1.status_code == 200

    # 4. FamilyOne sees their own chat; FamilyTwo sees 0 chats (strictly isolated!)
    h1 = client.post('/getchat', json={'account_id': acc1}).get_json()['history']
    h2 = client.post('/getchat', json={'account_id': acc2}).get_json()['history']
    assert len(h1) == 1 and h1[0]['question'] == 'private fever symptom family one'
    assert len(h2) == 0

    # Cleanup
    from db_config import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    for aid in (acc1, acc2):
        cur.execute("DELETE FROM chat_history_tbl WHERE account_id = %s", (aid,))
        cur.execute("DELETE FROM member_tbl WHERE account_id = %s", (aid,))
        cur.execute("DELETE FROM account_tbl WHERE account_id = %s", (aid,))
    conn.commit()
    cur.close()
    conn.close()



