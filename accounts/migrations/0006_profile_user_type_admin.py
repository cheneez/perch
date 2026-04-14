from django.db import migrations, models


def forwards_set_admin_for_staff(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    User = apps.get_model('auth', 'User')
    staff_ids = set(
        User.objects.filter(is_staff=True).values_list('pk', flat=True)
    ) | set(User.objects.filter(is_superuser=True).values_list('pk', flat=True))
    if not staff_ids:
        return
    Profile.objects.filter(user_id__in=staff_ids).exclude(user_type='admin').update(user_type='admin')


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_favorite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user_type',
            field=models.CharField(
                choices=[
                    ('student', 'Student'),
                    ('realtor', 'Realtor'),
                    ('admin', 'Admin'),
                ],
                default='student',
                max_length=10,
            ),
        ),
        migrations.RunPython(forwards_set_admin_for_staff, backwards_noop),
    ]
