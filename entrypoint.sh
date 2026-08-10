echo "Applying database migrations..."
python manage.py migrate --noinput
echo "Starting Django Development Server..."
exec python manage.py runserver 0.0.0.0:8000