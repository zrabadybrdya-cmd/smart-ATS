import os
import django
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_storage_connection():
    try:
        file_name = 'test_resume_upload.txt'
        file_content = ContentFile(b'This is a test resume content for Smart ATS.')
        saved_path = default_storage.save(file_name, file_content)
        print(f"[SUCCESS] File successfully saved at: {saved_path}")

        if default_storage.exists(saved_path):
            print("[SUCCESS] File existence verified in storage bucket/directory.")
            default_storage.delete(saved_path)
        print("[SUCCESS] Test file cleaned up successfully.")

    except Exception as e:
        print(f"[ERROR] Storage connection failed: {e}")

if __name__ == '__main__':
    test_storage_connection()