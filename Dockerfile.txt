FROM python:3.11-slim

# Install gawk
RUN apt-get update && apt-get install -y gawk

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (optional, for documentation)
EXPOSE 5000

# Run your app
CMD ["python", "app.py"]