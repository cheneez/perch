# Gitkeepers

Off-campus housing platform for Boston College students and realtors.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_test_data
python manage.py seed_test_users
python manage.py runserver
```

## How to set up Peformance Testing/Quick Locust run



```bash
python manage.py seed_load_test_data --students 500 --lessors 120 --listings-per-lessor 8 --conversations 700 --messages-per-conversation 12 --output performance/locust/data/credentials.json
locust -f performance/locust/locustfile.py --host http://127.0.0.1:8000 --web-port 8090
```
The first command generates a large, realistic load-testing dataset (users, lessors, listings, conversations, messages) and writes a credentials manifest JSON that Locust can use

Second command is to start up locust on port 8090