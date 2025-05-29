FROM python:3.9-slim

WORKDIR /app

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin -c "Application User" appuser

# Copy and install all dependencies (base and bot-specific)
COPY requirements-base.txt ./requirements-base.txt
COPY bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code, setting ownership
COPY --chown=appuser:appuser bot/ /app/
COPY --chown=appuser:appuser config/ /app/config/

USER appuser

CMD ["python", "bot.py"] 
