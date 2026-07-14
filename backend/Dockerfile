FROM python:3.11-slim

WORKDIR /app



# Install system dependencies required by Poppler (pdf2image) and Tesseract (OCR)
# Use noninteractive to prevent tzdata from hanging the build waiting for user input
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (Force CPU versions for all PyTorch libraries like torchvision)
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application (will run DB init and seed first, then start server)
CMD python init_db.py && python seed_data.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
