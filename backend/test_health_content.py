import unittest
import json
from app import app
from db_config import get_db_connection
from init_db import setup_database

class TestHealthContentManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.client = app.test_client()
        cls.client.testing = True

        # Login admin to obtain valid token
        login_res = cls.client.post('/admin/login', json={
            "username_or_email": "admin@niramaya.com",
            "password": "Admin@1234"
        })
        cls.admin_token = login_res.get_json()["token"]

    def test_01_public_user_read_only_access(self):
        """Test public endpoints allow unauthenticated users to view published tips and articles."""
        # Public tips
        res_tips = self.client.get('/api/health-content/tips')
        self.assertEqual(res_tips.status_code, 200)
        data_tips = res_tips.get_json()
        self.assertTrue(data_tips.get("success"))
        self.assertIn("disclaimer", data_tips)
        self.assertGreaterEqual(len(data_tips.get("tips", [])), 1)

        # Public articles
        res_articles = self.client.get('/api/health-content/articles')
        self.assertEqual(res_articles.status_code, 200)
        data_articles = res_articles.get_json()
        self.assertTrue(data_articles.get("success"))
        self.assertIn("disclaimer", data_articles)

    def test_02_admin_add_health_content(self):
        """Test Admin adding new Wellness Tip and Health Article with input validation."""
        # Invalid input test (missing title)
        res_invalid = self.client.post('/admin/health-content',
            json={"content_type": "wellness_tip", "title": "", "content": "Sample content"},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_invalid.status_code, 400)

        # Add valid Wellness Tip
        res_tip = self.client.post('/admin/health-content',
            json={
                "content_type": "wellness_tip",
                "title": "Monsoon Wellness Guide",
                "category": "Monsoon",
                "content": "Drink boiled water, eat freshly cooked food, and stay dry during heavy rains.",
                "author_or_source": "Niramaya Editorial",
                "status": "published"
            },
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_tip.status_code, 201)
        data_tip = res_tip.get_json()
        self.assertTrue(data_tip.get("success"))
        self.assertIn("disclaimer", data_tip)
        self.new_tip_id = data_tip["item"]["content_id"]

        # Add valid Health Article as Draft
        res_article = self.client.post('/admin/health-content',
            json={
                "content_type": "article",
                "title": "Machine Learning in Preventative Medicine",
                "category": "AI Health",
                "content": "Explores how ML algorithms predict early disease markers.",
                "author_or_source": "Niramaya AI Labs",
                "status": "draft"
            },
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_article.status_code, 201)
        data_article = res_article.get_json()
        self.new_article_id = data_article["item"]["content_id"]

    def test_03_admin_view_all_content(self):
        """Test Admin viewing all health content including drafts and archived items."""
        res = self.client.get('/admin/health-content', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("items", [])), 5)

    def test_04_admin_update_health_content(self):
        """Test Admin editing existing health content."""
        # First get a item id to update
        res_all = self.client.get('/admin/health-content?search=Monsoon', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        items = res_all.get_json()["items"]
        self.assertGreaterEqual(len(items), 1)
        item_id = items[0]["content_id"]

        # Update item
        res_update = self.client.put(f'/admin/health-content/{item_id}',
            json={
                "title": "Updated Monsoon Wellness Guide",
                "category": "Monsoon",
                "content": "Drink warm herbal tea and eat fresh immunity-boosting foods.",
                "author_or_source": "Niramaya Senior Health Team",
                "status": "published"
            },
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_update.status_code, 200)

        # Verify update on public endpoint
        res_public = self.client.get('/api/health-content/tips?category=Monsoon')
        self.assertEqual(res_public.status_code, 200)
        public_tips = res_public.get_json()["tips"]
        self.assertEqual(public_tips[0]["title"], "Updated Monsoon Wellness Guide")

    def test_05_admin_toggle_status_and_archive(self):
        """Test toggling status to 'archived' and verifying user read-only access excludes archived items."""
        # Get item ID
        res_all = self.client.get('/admin/health-content?search=Updated Monsoon', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        items = res_all.get_json()["items"]
        item_id = items[0]["content_id"]

        # Toggle status to archived
        res_archive = self.client.put(f'/admin/health-content/{item_id}/status',
            json={"status": "archived"},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_archive.status_code, 200)
        self.assertEqual(res_archive.get_json()["status"], "archived")

        # Verify public API hides archived item from normal users
        res_public = self.client.get('/api/health-content/tips?category=Monsoon')
        self.assertEqual(res_public.status_code, 200)
        self.assertEqual(len(res_public.get_json()["tips"]), 0)

    def test_06_admin_delete_content(self):
        """Test Admin permanently deleting a content item."""
        # Create temp item for deletion
        res_create = self.client.post('/admin/health-content',
            json={
                "content_type": "wellness_tip",
                "title": "Temporary Tip to Delete",
                "content": "Will be deleted immediately.",
                "status": "published"
            },
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        item_id = res_create.get_json()["item"]["content_id"]

        # Delete item
        res_delete = self.client.delete(f'/admin/health-content/{item_id}', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res_delete.status_code, 200)

        # Verify item is deleted
        res_single = self.client.get(f'/api/health-content/{item_id}')
        self.assertEqual(res_single.status_code, 404)

    def test_07_unauthorized_access_blocked(self):
        """Test unauthenticated or normal users cannot add, edit, toggle, or delete content."""
        # Create without auth header -> 401
        res1 = self.client.post('/admin/health-content', json={"title": "Hacked", "content": "Hacked"})
        self.assertEqual(res1.status_code, 401)

        # Update without auth header -> 401
        res2 = self.client.put('/admin/health-content/1', json={"title": "Hacked", "content": "Hacked"})
        self.assertEqual(res2.status_code, 401)

        # Delete without auth header -> 401
        res3 = self.client.delete('/admin/health-content/1')
        self.assertEqual(res3.status_code, 401)

if __name__ == '__main__':
    unittest.main()
