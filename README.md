# Gitkeepers

Off-campus housing platform for Boston College students and realtors.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Seeding sample data

To get a realtor account and one sample listing in your local database:

```bash
python manage.py seed_listings
```

This creates:
- **User:** `realtor_seed` / `perch1234` (realtor, email pre-verified)
- **Listing:** "Sunny 2BR Near Boston College" at 25 Commonwealth Ave, Brighton — status `available`, so it shows up on the Find Housing page immediately

Run it once after cloning. Re-running is safe — it skips creation if the user/listing already exist.

For a fuller local dataset with seeded admin, students, lessors, surveys, and listings:

```bash
python manage.py populate_test_data
```

This creates:
- **Admin:** `admin_seed` / `perch1234`
- **Students:** `student_seed_1` ... `student_seed_5` / `testpass123`
- **Lessors:** `lessor_seed_1` ... `lessor_seed_3` / `testpass123`
- **Listings:** approved, pending, rejected, and rented examples for moderation and browse testing

## Key URLs (local dev)

| Page | URL |
|---|---|
| Landing | http://127.0.0.1:8000/ |
| Login | http://127.0.0.1:8000/auth/login/ |
| Find Housing (students) | http://127.0.0.1:8000/student/find-housing/ |
| My Listings (realtors) | http://127.0.0.1:8000/listings/ |
| Create Listing | http://127.0.0.1:8000/listings/create/ |
