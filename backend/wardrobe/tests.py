from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import WardrobeItem

User = get_user_model()


class WardrobeItemIsolationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def _create_sample_image(self):
        file = BytesIO()
        image = Image.new("RGB", (200, 200), color="blue")
        image.save(file, "JPEG")
        file.seek(0)
        return SimpleUploadedFile(
            "test_shirt.jpg", file.read(), content_type="image/jpeg"
        )

    def test_original_image_field_removed_from_model(self):
        item = WardrobeItem.objects.create(
            user=self.user,
            name="Test Shirt",
            category="top",
            color="Blue",
        )
        self.assertFalse(hasattr(item, "original_image"))

    def test_add_item_with_invalid_image_fails_and_does_not_save_item(self):
        invalid_file = SimpleUploadedFile(
            "corrupt.jpg", b"invalid_binary_data", content_type="image/jpeg"
        )
        response = self.client.post(
            "/api/wardrobe/items/",
            {
                "name": "Corrupt Item",
                "category": "top",
                "color": "Red",
                "image": invalid_file,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors", response.data)
        self.assertIn("image", errors)
        self.assertEqual(WardrobeItem.objects.count(), 0)
