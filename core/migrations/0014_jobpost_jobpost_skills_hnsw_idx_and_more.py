from django.db import migrations

def create_hnsw_indexes(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            "CREATE INDEX IF NOT EXISTS jobpost_skills_hnsw_idx ON core_jobpost "
            "USING hnsw (skills_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
        )
        schema_editor.execute(
            "CREATE INDEX IF NOT EXISTS resume_skills_hnsw_idx ON core_resume "
            "USING hnsw (skills_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
        )

def drop_hnsw_indexes(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("DROP INDEX IF EXISTS jobpost_skills_hnsw_idx;")
        schema_editor.execute("DROP INDEX IF EXISTS resume_skills_hnsw_idx;")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_jobpost_skills_embedding_resume_skills_embedding'),
    ]

    operations = [
        migrations.RunPython(
            create_hnsw_indexes,
            reverse_code=drop_hnsw_indexes,
        ),
    ]