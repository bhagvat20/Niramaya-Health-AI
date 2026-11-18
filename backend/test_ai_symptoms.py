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
        # BioGPT
        res_bio = client.post('/askbiogpt', json={'question': query})
        assert res_bio.status_code == 200
        assert "Clinical Assessment" in res_bio.get_json()['answer']

        # Gemini
        res_gem = client.post('/askgemini', json={'question': query})
        assert res_gem.status_code == 200
        assert "Clinical Assessment" in res_gem.get_json()['answer']

        # LRv1
        res_lrv1 = client.post('/asklrv1', json={'symptoms': query})
        assert res_lrv1.status_code == 200
        assert res_lrv1.get_json()['predicted_disease'] != "Non-Health Query"

        # LRv2
        res_lrv2 = client.post('/asklrv2', json={'symptoms': query})
        assert res_lrv2.status_code == 200
        assert res_lrv2.get_json()['predicted_disease'] != "Non-Health Query"
        assert len(res_lrv2.get_json().get('precautions', [])) > 0

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
    """Verifies that different symptoms produce distinct, symptom-specific answers and not identical boilerplate."""
    res_digestive = client.post('/askbiogpt', json={'question': 'Digestive Issues'}).get_json()['answer']
    res_throat = client.post('/askbiogpt', json={'question': 'sore throat'}).get_json()['answer']
    res_multi = client.post('/askbiogpt', json={'question': 'fever and cough'}).get_json()['answer']

    # 1. Digestive must mention digestive-specific advice
    assert "Gastrointestinal" in res_digestive or "Dyspepsia" in res_digestive
    assert "curd" in res_digestive.lower() or "probiotic" in res_digestive.lower() or "fennel" in res_digestive.lower()

    # 2. Throat must mention throat-specific advice
    assert "Pharyngitis" in res_throat or "Gale" in res_throat or "Throat" in res_throat
    assert "gargle" in res_throat.lower() or "honey" in res_throat.lower() or "saline" in res_throat.lower()

    # 3. Multi symptom must detect multi-symptom complex
    assert "Multi-Symptom" in res_multi or ("Pyrexia" in res_multi and "Respiratory" in res_multi)

    # 4. Responses must be completely distinct from each other!
    assert res_digestive != res_throat
    assert res_throat != res_multi


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


