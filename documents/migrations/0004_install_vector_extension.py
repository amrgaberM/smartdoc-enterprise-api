from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # ⚠️ IMPORTANT: Check the other files in the folder.
        # If your last file was '0001_initial.py', keep this line:
        ('documents', '0001_initial'),
        
        # If your last file was '0002_something.py', change it to '0002_something'.
    ]

    operations = [
        # This SQL command turns on the AI Brain in the database
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql='DROP EXTENSION IF EXISTS vector;'
        ),
    ]