# Transactional email

The project uses Django's SMTP email backend. Provider-specific presets are
controlled by `EMAIL_PROVIDER`.

## Common production settings

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_PROVIDER=resend
DEFAULT_FROM_EMAIL=no-reply@ludarius.com
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_REQUIRE_AUTH=true
```

Restart Django after changing email settings.

## Resend

Use this when you want a simple developer-focused transactional email provider.

```env
EMAIL_PROVIDER=resend
DEFAULT_FROM_EMAIL=no-reply@ludarius.com
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=re_xxxxxxxxx
```

The preset configures:

```env
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

Production checklist:

- Verify `ludarius.com` in Resend.
- Add the DNS records Resend provides for SPF/DKIM.
- Use a Resend API key as `EMAIL_HOST_PASSWORD`.
- Keep `DEFAULT_FROM_EMAIL` on a verified domain.

Official guide: https://resend.com/docs/send-with-django-smtp

## Brevo

Use this when you want a broader marketing/transactional platform and a larger
free daily limit.

```env
EMAIL_PROVIDER=brevo
DEFAULT_FROM_EMAIL=no-reply@ludarius.com
EMAIL_HOST_USER=your-brevo-smtp-login
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
```

The preset configures:

```env
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

Production checklist:

- Verify `ludarius.com` in Brevo.
- Add the DNS records Brevo provides for SPF/DKIM.
- Use the SMTP key, not the API key, as `EMAIL_HOST_PASSWORD`.
- Keep `DEFAULT_FROM_EMAIL` on a verified sender/domain.

Official guide: https://developers.brevo.com/docs/smtp-integration

## Gmail

Gmail is acceptable for development/MVP, but not ideal for production.

```env
EMAIL_PROVIDER=gmail
DEFAULT_FROM_EMAIL=appludarius@gmail.com
EMAIL_HOST_USER=appludarius@gmail.com
EMAIL_HOST_PASSWORD=google-app-password
```

The preset configures Gmail SMTP host, port and TLS.
