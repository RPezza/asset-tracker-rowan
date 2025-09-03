import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Asset, Booking, UserMessage

# Clear existing data
Asset.objects.all().delete()
Booking.objects.all().delete()
UserMessage.objects.all().delete()
User.objects.exclude(username='admin').delete()

# Sample users
users = []
for i in range(2):
    user, created = User.objects.get_or_create(
        username=f'user{i}',
        defaults={'email': f'user{i}@example.com'}
    )
    if created:
        user.set_password('password')
        user.save()
    users.append(user)

# Sample assets (10 records)
asset_data = [
    {"name": "Leica 360", "description": "High-precision 3D scanner", "category": "Scanning"},
    {"name": "RTC 360", "description": "Rapid laser scanner", "category": "Scanning"},
    {"name": "360 GoPro", "description": "Compact 360 camera", "category": "Media Capture"},
    {"name": "Insta360", "description": "Versatile 360 camera", "category": "Media Capture"},
    {"name": "Spot", "description": "Agile robotic dog", "category": "Robotics"},
    {"name": "Meta Quest 3", "description": "VR headset", "category": "Visual"},
    {"name": "Drone", "description": "Aerial drone", "category": "Media Capture"},
    {"name": "Sony Camera", "description": "Professional camera", "category": "Media Capture"},
    {"name": "IPad", "description": "Tablet", "category": "Devices"},
    {"name": "Canon DSLR", "description": "DSLR camera", "category": "Media Capture"},
]

assets = [Asset.objects.create(**data, available=True) for data in asset_data]

# Create bookings (10 records)
for i in range(10):
    user = random.choice(users)
    asset = random.choice(assets)
    start = date.today() + timedelta(days=i * 2)
    end = start + timedelta(days=1)
    Booking.objects.create(
        user=user,
        asset=asset,
        start_date=start,
        end_date=end,
        purpose="Demo booking",
    )

# Create user messages (10 records)
for i in range(10):
    user = random.choice(users)
    UserMessage.objects.create(
        user=user,
        name=f"User {i}",
        email=f"user{i}@example.com",
        subject=f"Subject {i}",
        message="Demo message",
    )
