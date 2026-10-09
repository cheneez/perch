# Perch

An off-campus housing platform for Boston College students and local landlords. Students can browse listings, message landlords in real time, take a roommate compatibility survey, and form housing groups. Admins can moderate reports.

Built by a team of six for **CSCI3356 Software Engineering** at Boston College (Spring 2026). This is a personal copy of the team repository, with full commit history, shared with permission for portfolio purposes.

## My contributions: Hiram Chen ([@cheneez](https://github.com/cheneez))

13 commits from the project's first commit in March to the final demo in April. [See all of them.](https://github.com/cheneez/perch/commits/main/?author=cheneez)

### Roommate compatibility survey and scoring model
[`student/models.py`](student/models.py) · [`student/views.py`](student/views.py)

- Designed the **12-question lifestyle survey** (cleanliness, sleep schedule, noise, smoking, guests, pets, personality and more) and its data model, with one saved response per student.
- Encoded every answer onto a consistent **1–5 numeric scale**. Each choice carries its score in its key, so new questions plug in without extra code.
- Turned each student's answers into a **five-part compatibility profile** (personality, living habits, roommate preference, cleanliness, sleep). This is the numeric foundation the team's weighted roommate-matching feature ([`student/compatibility.py`](student/compatibility.py)) builds on.

### Account security and project foundation
[`accounts/views.py`](accounts/views.py) · [`perch/settings.py`](perch/settings.py)

- Set up the Django project and built the original login and signup system that the team built on.
- Restricted student accounts to **verified `@bc.edu` Google identities**, so only real BC students can join. The rule is checked at signup and again when Google returns the user. I used Google's verified-email flag so students skip a second email-link step, and added tests for these rules.
- Hardened the Google sign-in error handling so network, token and profile failures show a clear message instead of crashing.
- Fixed role switching and CSRF settings before the final demo.

### Moderation and notifications
[`notifications/`](notifications/) · [`moderation/admin.py`](moderation/admin.py)

- Built the **notifications app from scratch**, including its model, views, unread count in the navigation bar, and notification page.
- Added "report" links on public profiles, so admins receive reports and reply, and users are notified of the outcome.

### Search and admin tools
[`perch/search_views.py`](perch/search_views.py)

- Built user search across students and landlords, with public profile pages, plus seed data for demos.
- Redesigned the admin page layout.

## Features

- **Accounts and authentication:** Google Sign-In restricted to verified `@bc.edu` emails for students, plus separate landlord (lessor) accounts with verification.
- **Listings:** create, search, favorite and hide listings, with image uploads and a Google Maps view.
- **Real-time chat:** one-to-one and group messaging over WebSockets (Django Channels).
- **Roommate matching:** a compatibility survey that scores students on lifestyle factors such as cleanliness, plus user search and public profiles.
- **Moderation:** report users or listings, with admin replies and report notifications.
- **Performance testing:** Locust load tests against a generated dataset of hundreds of users, listings and conversations.

## Tech stack

Python, Django, Django Channels (Daphne / Uvicorn), PostgreSQL (SQLite locally), WhiteNoise, Google OAuth 2.0, Google Maps API, Locust. It was deployed on Render during the course.

## Team

Hiram Chen ([@cheneez](https://github.com/cheneez)), Stephen Jones ([@SJones339](https://github.com/SJones339)), Jorge ([@Jorge-Saq](https://github.com/Jorge-Saq)), Luke Lestina ([@LukeLestina](https://github.com/LukeLestina)), Nathan Thai ([@daganaa](https://github.com/daganaa)), James Labrador ([@jartus101](https://github.com/jartus101))

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
