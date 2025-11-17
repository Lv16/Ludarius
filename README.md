# Ludarius (scaffold)

Scaffold inicial do projeto Ludarius — backend Django + PWA frontend básico.

Setup rápido (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Notas:
- O scaffold usa SQLite para desenvolvimento. Para produção, configure PostgreSQL em `ludarius_project/settings.py`.
- O frontend PWA básico está em `ludarius_project/templates` e `ludarius_project/static`.
 - Integração opcional: `django-allauth` foi adicionada para suportar login social (configuração mínima aplicada). Configure provedores sociais nas variáveis `SOCIALACCOUNT_PROVIDERS` e registre credenciais nos portais dos provedores.

Exemplo: configurar login via Google
 - 1) No Google Cloud Console crie um projeto e um OAuth 2.0 Client ID (Credentials).
	 - Tipo de aplicação: "Web application".
	 - Authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`
 - 2) No Django Admin -> Social applications, clique em Add Social Application:
	 - Provider: `Google`
	 - Name: `Google` (ou o que preferir)
	 - Client id: (cole o client id do Google)
	 - Secret key: (cole o client secret)
	 - Sites: selecione `localhost` (marque o site criado previamente)
 - 3) No `settings.py` já existe um exemplo `SOCIALACCOUNT_PROVIDERS['google']` com `SCOPE` configurado. Ajuste se precisar.
 - 4) Teste: acesse `http://localhost:8000/accounts/login/` e clique em "Sign in with Google".

Notas de segurança e produção
 - Não coloque client secrets em repositórios públicos; use variáveis de ambiente.
 - Para produção configure HTTPS e os redirect URIs apropriados no console do provedor.
 - Depois que tudo funcionar localmente, remova credenciais de teste e crie apps de produção nos provedores.

Autenticação API (JWT)

 - Instalado `djangorestframework-simplejwt` para autenticação baseada em tokens JWT.
 - Endpoints disponíveis (REST):
	 - `POST /api/token/` → obter `access` e `refresh` (envie `username` e `password`).
	 - `POST /api/token/refresh/` → renovar `access` usando `refresh`.

Exemplo (cURL):
```bash
curl -X POST http://localhost:8000/api/token/ -d "username=admin&password=admin"
```
Resposta (JSON):
```json
{
	"access": "<JWT_TOKEN>",
	"refresh": "<REFRESH_TOKEN>"
}
```

Para chamadas autenticadas à API, envie o header:
```
Authorization: Bearer <JWT_TOKEN>
```

Nota: para o frontend PWA recomendamos usar o fluxo `refresh` para manter sessões longas e armazenar tokens com cuidado (preferencialmente no `httpOnly` cookie via backend ou armazenamento seguro no dispositivo).
