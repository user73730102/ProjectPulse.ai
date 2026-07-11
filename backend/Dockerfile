FROM python:3.11-slim

WORKDIR /app



# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application (will run DB init and seed first, then start server)
CMD python init_db.py && python seed_data.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
