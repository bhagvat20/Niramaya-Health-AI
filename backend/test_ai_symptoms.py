import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ai_general_questions_are_strictly_rejected(client):
    """Verifies that non-health/general questions are strictly refused across all AI endpoints."""
    non_health_queries = [
        "what is the capital of France",
        "how to write python code",
        "tell me a funny joke",
        "who is the prime minister of india",
        "how to bake a chocolate cake",
        "what is the score in cricket match",
        "can you solve 25 times 40"
    ]
    for query in non_health_queries:
        # BioGPT
        res_bio = client.post('/askbiogpt', json={'question': query})
        assert res_bio.status_code == 200
        assert "Medical & Symptom Checker Domain Restriction" in res_bio.get_json()['answer']

        # Gemini
        res_gem = client.post('/askgemini', json={'question': query})
        assert res_gem.status_code == 200
        assert "Medical & Symptom Checker Domain Restriction" in res_gem.get_json()['answer']

        # LRv1
        res_lrv1 = client.post('/asklrv1', json={'symptoms': query})
        assert res_lrv1.status_code == 200
        assert res_lrv1.get_json()['predicted_disease'] == "Non-Health Query"

        # LRv2
        res_lrv2 = client.post('/asklrv2', json={'symptoms': query})
        assert res_lrv2.status_code == 200
        assert res_lrv2.get_json()['predicted_disease'] == "Non-Health Query"

def test_ai_symptoms_are_properly_accepted_and_answered(client):
    """Verifies that genuine health symptoms in English and Hindi are accepted and answered."""
    symptom_queries = [
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
