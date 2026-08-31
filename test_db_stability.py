import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, JobPost, Resume, Application

def run_stability_check():
    print("--- 1. Testing Database Connection & Read ---")
    users_count = User.objects.count()
    companies_count = Company.objects.count()
    print(f"Total Users: {users_count}, Total Companies: {companies_count}")

    print("\n--- 2. Testing JobPost with Vector Fields & Indexes ---")
    admin_user = User.objects.first()
    if not admin_user:
        admin_user = User.objects.create(username="test_admin", role="admin")

    company, _ = Company.objects.get_or_create(name="Stability Test Corp", owner=admin_user)
    dummy_vector = [0.1] * 1536

    job = JobPost.objects.create(
        company=company,
        title="Python AI Engineer",
        description="Testing vector stability",
        skills="Python, Django, pgvector",
        skills_embedding=dummy_vector,
        status="published"
    )
    print(f"Created JobPost: {job.title} (ID: {job.id})")

    print("\n--- 3. Testing Resume with Vector Fields ---")
    resume = Resume.objects.create(
        user=admin_user,
        parsed_skills="Python, Django",
        skills_embedding=dummy_vector
    )
    print(f"Created Resume: {resume.id} for {admin_user.username}")

    print("\n--- 4. Cleanup Test Records ---")
    job.delete()
    resume.delete()
    print("Cleanup successful. Database is fully stable and operational.")

if __name__ == "__main__":
    run_stability_check()