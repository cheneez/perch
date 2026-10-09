# Perch

An off-campus housing platform for Boston College students and local landlords. Students can browse listings, message landlords in real time, take a roommate compatibility survey, and form housing groups. Admins can moderate reports.

Built by a team of six for **CSCI3356 Software Engineering** at Boston College (Spring 2026). This is a personal copy of the team repository, with full commit history, shared with permission for portfolio purposes.

## Features

- **Accounts and authentication:** Google Sign-In restricted to verified `@bc.edu` emails for students, plus separate landlord (lessor) accounts with verification.
- **Listings:** create, search, favorite and hide listings, with image uploads and a Google Maps view.
- **Real-time chat:** one-to-one and group messaging over WebSockets (Django Channels).
- **Roommate matching:** a compatibility survey that scores students on lifestyle factors such as cleanliness, plus user search and public profiles.
- **Moderation:** report users or listings, with admin replies and report notifications.
- **Performance testing:** Locust load tests against a generated dataset of hundreds of users, listings and conversations.

## Tech stack

Python, Django, Django Channels (Daphne / Uvicorn), PostgreSQL (SQLite locally), WhiteNoise, Google OAuth 2.0, Google Maps API, Locust. It was deployed on Render during the course.

## My contributions (Hiram Chen, `cheneez`)

- Built the login system and Google Sign-In authentication, restricted student signup to verified `@bc.edu` emails, and wrote the accompanying tests.
- Designed and implemented the roommate compatibility survey, including its data model, scoring, and display on student profiles.
- Built user search and public profile pages, and seeded test students and landlords for demos.
- Added the report workflow on public profiles, report notifications, and admin replies.
- Fixed role switching and CSRF settings for the final demo, and fixed the admin page layout.

## Team

Hiram Chen ([@cheneez](https://github.com/cheneez)), Luke Lestina ([@LukeLestina](https://github.com/LukeLestina)), Jorge ([@Jorge-Saq](https://github.com/Jorge-Saq)), Nathan Thai, James Labrador, Stephen Jones

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_test_data
python manage.py seed_test_users
python manage.py runserver
```

Google Sign-In and Maps need your own keys in a `.env` file (`GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_CALLBACK_URL`, `GOOGLE_MAPS_API_KEY`). Keys are not included in this repository.

### Load testing

```bash
python manage.py seed_load_test_data --students 500 --lessors 120 --listings-per-lessor 8 --conversations 700 --messages-per-conversation 12 --output performance/locust/data/credentials.json
locust -f performance/locust/locustfile.py --host http://127.0.0.1:8000 --web-port 8090
```
