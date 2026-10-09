# Perch

An off-campus housing platform for Boston College students and local landlords. Students can browse listings, message landlords in real time, take a roommate compatibility survey, and form housing groups. Admins can moderate reports.

Built by a team of six for **CSCI3356 Software Engineering** at Boston College (Spring 2026). This is a personal copy of the team repository, with full commit history, shared with permission for portfolio purposes.

## My contributions: Hiram Chen ([@cheneez](https://github.com/cheneez))

I worked on Perch from its first commit in March to the final demo in April ([commit history](https://github.com/cheneez/perch/commits/main/?author=cheneez)). My focus was the parts a housing platform depends on most: **who is allowed in, how students are matched, and how the community stays safe.**

### 1. Trust: only real BC students can join
[`accounts/views.py`](accounts/views.py) · [`perch/settings.py`](perch/settings.py) · [`accounts/tests.py`](accounts/tests.py)

A housing app where strangers can pose as students is unsafe, so I made identity the first thing the system gets right.

- **Laid the project's foundation:** created the Django project, its configuration, and the original login and signup flow.
- **Verified `@bc.edu` identities only.** The rule is enforced twice: when the signup form is submitted, and again when Google returns the signed-in identity. Editing a request in the browser cannot bypass it.
- **Removed a redundant step without lowering security:** students trust Google's `email_verified` claim instead of clicking a second email link.
- **Clear failures:** token-exchange, network and profile errors are caught and explained to the user, not shown as a crash.
- **Covered by automated tests:** non-BC emails are rejected and no account is created, while verified Google students go straight to their dashboard.

### 2. Matching: turning lifestyle answers into data
[`student/models.py`](student/models.py) · [`student/views.py`](student/views.py)

Roommate conflicts usually come from everyday habits, so I designed a way to measure them.

- **Designed a 12-question lifestyle survey** covering cleanliness, sleep schedule, noise, smoking, guests, parties, pets, personality and conflict style, stored as one validated response per student.
- **Put every answer on one 1–5 scale.** Each choice carries its score in its key (`s1_…` to `s5_…`), so any question can be compared numerically, and new questions need no extra scoring code.
- **Built each student a five-part compatibility profile** (personality, living habits, roommate preference, cleanliness, sleep). These are the numbers Perch's roommate matching uses to rank compatible students.

### 3. Safety: reporting, moderation and notifications
[`notifications/`](notifications/) · [`moderation/admin.py`](moderation/admin.py)

- **Built a notifications system from scratch,** a self-contained Django app with its own data model, pages, and an unread badge in the navigation bar on every page.
- **Closed the moderation loop:** users can report a profile, admins review and reply, and the reporter is notified automatically, so reports never disappear silently.

### 4. Discovery and reliability
[`perch/search_views.py`](perch/search_views.py) · [`perch/settings.py`](perch/settings.py)

- **People search** across students and landlords. It matches first name, last name, username or a full "first last" query, shows only active accounts (suspended users are hidden), and links to public profiles.
- **Fixed a data-integrity bug** where editing a listing in the admin panel silently changed the owner's account type. Role changes now happen only explicitly.
- **Made the app demo-ready** with secure, environment-based host and CSRF settings, which are strict in production and convenient for local demos.

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
