FROM python:3.13-slim

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

# Copy uv files and project
COPY pyproject.toml ./

# Install dependencies via uv system install
RUN uv pip install --system fastapi uvicorn 'markdown[extra]' playwright jinja2 python-multipart python-dotenv

# Install Playwright browsers and OS dependencies
RUN playwright install --with-deps chromium

# Install custom fonts
COPY HarmonyOS_Sans_SC /usr/share/fonts/HarmonyOS_Sans_SC/
RUN fc-cache -fv

# Copy application files
COPY main.py template.html ./
# Create public directory
RUN mkdir -p public

# Expose port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
