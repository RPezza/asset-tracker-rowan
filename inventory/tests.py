from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Asset, Booking


class BookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', password='pass')
        self.asset = Asset.objects.create(name='Camera', description='Test', category='Media')

    def test_login_required_for_booking(self):
        response = self.client.get(reverse('book_asset'))
        self.assertEqual(response.status_code, 302)

    def test_booking_sets_asset_unavailable(self):
        self.client.login(username='user', password='pass')
        self.client.post(reverse('book_asset'), {
            'asset': self.asset.id,
            'start_date': '2100-01-01',
            'end_date': '2100-01-02',
            'purpose': 'test',
        })
        self.asset.refresh_from_db()
        self.assertFalse(self.asset.available)
        self.assertEqual(Booking.objects.count(), 1)


class AssetListImageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", password="pass")
        self.asset = Asset.objects.create(name="Camera", description="Test", category="Media")

    def test_asset_list_displays_image(self):
        self.client.login(username="user", password="pass")
        response = self.client.get(reverse("asset_list"))
        self.assertContains(response, "/static/equipment/camera.jpg")

