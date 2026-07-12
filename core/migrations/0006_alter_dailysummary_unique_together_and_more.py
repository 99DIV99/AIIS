import uuid
from django.conf import settings
from django.db import migrations, models

def migrate_data(apps, schema_editor):
    DailySummary = apps.get_model('core', 'DailySummary')
    for ds in DailySummary.objects.all():
        # Copy date to target_date
        ds.target_date = ds.date
        # Map old types to new types
        if ds.summary_type == 'personal':
            ds.summary_type = 'individual'
        elif ds.summary_type == 'office':
            ds.summary_type = 'team'
        # Set unique UUID
        ds.uuid_id = uuid.uuid4()
        ds.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_ping_pingreply'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add new fields
        migrations.AddField(
            model_name='dailysummary',
            name='target_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='uuid_id',
            field=models.UUIDField(null=True),
        ),
        # 2. Alter summary_type length
        migrations.AlterField(
            model_name='dailysummary',
            name='summary_type',
            field=models.CharField(max_length=20),
        ),
        # 3. Migrate data
        migrations.RunPython(migrate_data),
        # 4. Remove old constraints and fields
        migrations.AlterUniqueTogether(
            name='dailysummary',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='date',
        ),
        migrations.RemoveField(
            model_name='dailysummary',
            name='id',
        ),
        # 5. Rename uuid_id to id and make PK
        migrations.RenameField(
            model_name='dailysummary',
            old_name='uuid_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='dailysummary',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        # 6. Apply new constraints
        migrations.AlterUniqueTogether(
            name='dailysummary',
            unique_together={('user', 'target_date', 'summary_type')},
        ),
        # 7. Set final choices for summary_type
        migrations.AlterField(
            model_name='dailysummary',
            name='summary_type',
            field=models.CharField(choices=[('individual', 'Individual'), ('team', 'Team')], max_length=20),
        ),
    ]
