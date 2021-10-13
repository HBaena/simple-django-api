from django.test import TestCase
from icecream import ic
from rest_framework.test import APIClient

# from rest_framework.authtoken.models import Token
# from rest_framework.test import force_authenticate
from faker import Faker
from django.contrib.auth.models import User
from .responses import StatusMsg, SuccessMsg, ErrorMsg
from datetime import datetime, timedelta


class PropertyTests(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "admin@example.com", "password123")

    def test_as_client(self):
        client = APIClient()
        # client.login(username='admin', password='password123')
        client.force_authenticate(user=User.objects.get(username="admin"))
        fake = Faker()
        path = "/api/properties/"

        ic("Check list of properties")
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("data"), [])

        ic("Create propeties")
        data = {
            "title": fake.sentence(nb_words=3),
            "address": fake.address(),
            "description": fake.paragraph(nb_sentences=5),
            "status": "Active",
        }
        response = client.post(path, data=data)
        self.assertContains(response, StatusMsg.OK, status_code=201)
        data = {
            "title": fake.sentence(nb_words=3),
            "address": fake.address(),
            "description": fake.paragraph(nb_sentences=5),
            "status": "Active",
        }
        response = client.post(path, data=data)
        self.assertContains(response, StatusMsg.OK, status_code=201)
        data = {
            "title": fake.sentence(nb_words=3),
            "address": fake.address(),
            "description": fake.paragraph(nb_sentences=5),
            "status": "Inactive",
        }
        response = client.post(path, data=data)
        self.assertContains(response, StatusMsg.OK, status_code=201)
        ic("Validation error")
        data = {
            "title": fake.sentence(nb_words=3),
            "address": fake.address(),
            "description": fake.paragraph(nb_sentences=5),
            "status": "active",
        }
        response = client.post(path, data=data)
        self.assertContains(response, StatusMsg.ERROR, status_code=400)
        self.assertTrue(response.data.get("error"))
        self.assertEqual(response.data.get("error"), ErrorMsg.VALIDATION)

        ic("Check list properties again")
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, StatusMsg.OK)
        self.assertEqual(response.data.get("count"), 3)

        ic("delete property (Default method)")
        response = client.delete(f"{path}1/")
        self.assertEqual(response.status_code, 204)

        ic("Trying to access to deleted property")
        response = client.get(f"{path}1/")
        self.assertContains(response, ErrorMsg.NOT_FOUND, status_code=400)

        ic("Properties done!")

        # ----------------------------------------------------------------
        path = "/api/activities/"

        ic("Check list of activities")
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("data"), [])

        data = {
            "property": 2,  # One was removed,
            "title": fake.sentence(nb_words=2),
            "schedule": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        ic("Validation error: schedule format")
        response = client.post(path, data=data)
        self.assertContains(response, ErrorMsg.VALIDATION, status_code=400)

        ic("Validation error: inactive property")
        data["schedule"] = (datetime.now() + timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        data["property"] = 3
        response = client.post(path, data=data)  # Activity 1
        self.assertContains(
            response, "Selected property is Inactive or Removed", status_code=400
        )

        ic("Add activity successfully")
        # data['schedule'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        data["property"] = 2
        response = client.post(path, data=data)  # Activity 1
        self.assertContains(response, SuccessMsg.CREATED, status_code=201)

        ic(
            "Validation error: same schedule (must be more than one hour later or before)"
        )
        response = client.post(path, data=data)  # Activity 1
        self.assertContains(response, ErrorMsg.VALIDATION, status_code=400)
        ic("Add activity successfully")
        data["title"] = fake.sentence(nb_words=2)
        data["schedule"] = (datetime.now() + timedelta(days=30)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        response = client.post(path, data=data)  # Activity 1
        self.assertContains(response, SuccessMsg.CREATED, status_code=201)
        ic("Activities done!")
