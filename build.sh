#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

cd backend

python manage.py collectstatic --noinput
python manage.py migrate

if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
    python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ['ADMIN_USERNAME']
password = os.environ['ADMIN_PASSWORD']
email = os.environ.get('ADMIN_EMAIL', '')

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'is_staff': True,
        'is_superuser': True,
    }
)

user.email = email
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

print('Admin user created/updated successfully.')
"
fi