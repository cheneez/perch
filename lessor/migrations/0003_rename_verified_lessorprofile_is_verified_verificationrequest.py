import django.db.models.deletion
import lessor.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessor', '0002_remove_profile_fun_facts_and_scores'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='lessorprofile',
            old_name='verified',
            new_name='is_verified',
        ),
        migrations.CreateModel(
            name='VerificationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('government_id', models.FileField(upload_to=lessor.models._verification_doc_path)),
                ('property_proof', models.FileField(upload_to=lessor.models._verification_doc_path)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('verified', 'Verified'), ('declined', 'Declined')],
                    default='pending',
                    max_length=20,
                )),
                ('admin_feedback', models.TextField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('lessor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='verification_requests',
                    to='lessor.lessorprofile',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_verifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
    ]
