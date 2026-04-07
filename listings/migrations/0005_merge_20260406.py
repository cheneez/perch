# Merge conflicting 0004 branches (latitude/longitude vs moderation fields).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0004_listing_latitude_listing_longitude"),
        ("listings", "0004_listing_moderated_at_listing_moderated_by_and_more"),
    ]

    operations = []
