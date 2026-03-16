# Gitkeepers

## Local setup

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/auth/login/`.

The app auto-loads a local `.env` file from the repo root. Teammates do not need to run `export` commands if `.env` is present.

## Teammate setup

1. Pull the latest code.
2. Create a local `.env`
3. Put in the shared Google OAuth client ID and client secret.
4. Run the local setup commands above.

If the Google OAuth app is still in `Testing`, every teammate who signs in with Google must also be added as a `Test user` in Google Cloud.

## Login flows

- Students sign in with Google OAuth and must use a verified `@bc.edu` email.
- Realtors sign up and log in with email and password.

## Google OAuth config

Put these values in `.env`:

```dotenv
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_CALLBACK_URL=http://127.0.0.1:8000/auth/google/callback/
```

## Verification email

Verification emails are enabled for new accounts.

By default, Django prints those emails into the terminal running `runserver`.
If you want real inbox delivery, add SMTP settings to `.env`.
