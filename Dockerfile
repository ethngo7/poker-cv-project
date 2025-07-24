# Use a lightweight Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies for OpenCV (YOLO needs this)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Set Streamlit to run on 0.0.0.0
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
