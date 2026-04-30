from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0008_listingreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='is_hidden',
            field=models.BooleanField(default=False),
        ),
    ]
