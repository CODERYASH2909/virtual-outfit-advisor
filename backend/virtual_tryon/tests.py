import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from django.conf import settings
from django.test import TestCase

from .services import (
    preprocess_person_photo,
    composite_garments_onto_avatar,
    log_body_continuity,
)


class VirtualTryOnBodyPreservationTests(TestCase):
    def setUp(self):
        # Create a sample synthetic full-body person photo (red head, blue body, green legs)
        self.temp_dir = tempfile.mkdtemp()
        self.sample_person_path = os.path.join(self.temp_dir, "sample_person.png")

        img = Image.new("RGBA", (400, 800), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Head (y: 20 to 120)
        draw.ellipse([150, 20, 250, 120], fill=(220, 150, 130, 255))
        # Torso/Arms (y: 120 to 450)
        draw.rectangle([100, 120, 300, 450], fill=(0, 0, 255, 255))
        # Legs (y: 450 to 760)
        draw.rectangle([130, 450, 270, 760], fill=(50, 50, 50, 255))
        img.save(self.sample_person_path, "PNG")

        # Create a sample garment
        self.sample_garment_path = os.path.join(self.temp_dir, "sample_hoodie.png")
        garm = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
        garm.save(self.sample_garment_path, "PNG")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preprocess_person_photo_preserves_full_body(self):
        base_char_path = preprocess_person_photo(self.sample_person_path)
        self.assertTrue(os.path.exists(base_char_path))

        with Image.open(base_char_path) as img:
            w, h = img.size
            self.assertEqual(w, 768)
            self.assertEqual(h, 1024)
            bbox = img.convert("RGBA").split()[-1].getbbox()
            self.assertTrue(bbox is not None)

    def test_composite_garments_onto_avatar_fast_execution(self):
        base_char_path = preprocess_person_photo(self.sample_person_path)
        items = [
            {
                "name": "Black Jeans",
                "category": "bottom",
                "cloth_type": "lower",
                "image_path": self.sample_garment_path,
                "clean_path": self.sample_garment_path,
            },
            {
                "name": "Navy Shirt",
                "category": "top",
                "cloth_type": "upper",
                "image_path": self.sample_garment_path,
                "clean_path": self.sample_garment_path,
            },
        ]

        result_path = composite_garments_onto_avatar(base_char_path, items)
        self.assertTrue(os.path.exists(result_path))

        with Image.open(result_path) as img:
            self.assertEqual(img.size, (768, 1024))
            colors = img.getcolors(maxcolors=10000)
            self.assertTrue(len(colors) > 1)
