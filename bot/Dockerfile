FROM python:3.9-slim

WORKDIR /app

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin -c "Application User" appuser

# Copy and install common dependencies
COPY requirements.txt ./common_requirements.txt
RUN pip install --no-cache-dir -r common_requirements.txt

# Copy and install bot-specific dependencies
COPY bot/requirements.txt ./bot_requirements.txt
RUN pip install --no-cache-dir -r bot_requirements.txt

# Copy the rest of the application code, setting ownership
COPY --chown=appuser:appuser bot/ /app/
COPY --chown=appuser:appuser config/ /app/config/

USER appuser

CMD ["python", "bot.py"] 
