FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files at build time (SECRET_KEY here is a throw-away value).
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

# Run as an unprivileged user.
RUN useradd --create-home app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media /app/staticfiles
USER app

EXPOSE 8000

CMD ["gunicorn", "resturant.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
