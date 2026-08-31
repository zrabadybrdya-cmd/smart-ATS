from django.db import migrations

def enable_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS vector;')

def disable_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP EXTENSION IF EXISTS vector;')

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_applicationhistory_candidate_application_candidate'),
    ]

    operations = [
        migrations.RunPython(
            enable_pgvector,
            reverse_code=disable_pgvector,
        ),
    ]