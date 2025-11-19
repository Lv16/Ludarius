import os
import sys

# prepare Django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ludarius_project.settings')
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import argparse

# Configure email backend from environment if provided, otherwise default to console
smtp_host = os.environ.get('SMTP_HOST')
if smtp_host:
    # configure SMTP from environment
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    settings.EMAIL_HOST = smtp_host
    settings.EMAIL_PORT = int(os.environ.get('SMTP_PORT', '587'))
    settings.EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
    settings.EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    use_tls = os.environ.get('SMTP_USE_TLS')
    use_ssl = os.environ.get('SMTP_USE_SSL')
    # prefer explicit flags, default to TLS on port 587
    if use_tls is not None:
        settings.EMAIL_USE_TLS = use_tls.lower() in ('1', 'true', 'yes')
    else:
        settings.EMAIL_USE_TLS = (settings.EMAIL_PORT == 587)
    if use_ssl is not None:
        settings.EMAIL_USE_SSL = use_ssl.lower() in ('1', 'true', 'yes')
    # override from email if provided
    settings.DEFAULT_FROM_EMAIL = os.environ.get('FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
else:
    # Default to console backend for safe local preview
    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

User = get_user_model()
parser = argparse.ArgumentParser(description='Enviar e-mail de teste de reset de senha')
parser.add_argument('--to', '-t', help='Endereço de e-mail destinatário (sobrescreve TO_EMAIL)')
parser.add_argument('--username', '-u', help='Nome de usuário a usar (opcional)')
args = parser.parse_args()

# determine recipient email and username (order of precedence: --to, TO_EMAIL env, fallback)
email = args.to or os.environ.get('TO_EMAIL') or 'teste@example.com'
username = args.username or os.environ.get('TO_USERNAME') or (email.split('@', 1)[0] if email else 'teste')

# create or get a test user
user, created = User.objects.get_or_create(email=email, defaults={'username': username})
if created:
    user.set_password('password123')
    user.save()

protocol = 'https'
domain = 'localhost:8000'
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = default_token_generator.make_token(user)
reset_url = f"{protocol}://{domain}/reset/{uid}/{token}/"

context = {
    'user': user,
    'protocol': protocol,
    'domain': domain,
    'uid': uid,
    'token': token,
    'reset_url': reset_url,
}

subject = render_to_string('emails/password_reset_subject.txt', context).strip() if os.path.exists(os.path.join(PROJECT_ROOT, 'templates', 'emails', 'password_reset_subject.txt')) else 'Redefinição de senha — Ludarius'

text_body = render_to_string('emails/password_reset_email.txt', context)
html_body = render_to_string('emails/password_reset_email.html', context)

from_email = os.environ.get('FROM_EMAIL') or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[email])
msg.attach_alternative(html_body, 'text/html')
msg.send()

backend_label = getattr(settings, 'EMAIL_BACKEND', 'console')
print('\n--- Preview enviado ---')
print(f'Backend: {backend_label}')
print(f'To: {email}')
print(f'From: {from_email}')
print(f'Reset URL: {reset_url}')
