import os
import sys
import django
from django.utils import translation
from django.template.loader import render_to_string

# Ensure project root is on sys.path so Django settings module can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure Django settings module (adjust if your settings module name differs)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ludarius_project.settings')
django.setup()

translation.activate('pt_BR')

class DummyUser:
    def __init__(self, email, full_name=None):
        self.email = email
        self._full_name = full_name or 'Usuário Teste'
    def get_full_name(self):
        return self._full_name
    @property
    def username(self):
        # derive a simple username from email if not explicitly provided
        return self.email.split('@')[0]

protocol = 'https'
domain = 'localhost:8000'
uid = 'uidb64-example'
token = 'token-example'

# build a full reset URL used by templates
reset_url = f"{protocol}://{domain}/reset/{uid}/{token}/"

context = {
    'user': DummyUser('teste@example.com', 'Usuário Teste'),
    'protocol': protocol,
    'domain': domain,
    'uid': uid,
    'token': token,
    'reset_url': reset_url,
}

print('--- Render: emails/password_reset_email.txt ---')
print(render_to_string('emails/password_reset_email.txt', context))
print('\n--- Render: emails/password_reset_email.html ---')
print(render_to_string('emails/password_reset_email.html', context))

# indicate which language was active
print('\n--- Idioma ativo ---')
print(translation.get_language())
