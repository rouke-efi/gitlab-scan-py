# Use the official Python image from Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file (if you have one)
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy the entry point script
COPY entrypoint.sh ./

# Make the script executable
RUN chmod +x /app/entrypoint.sh

# Set the entry point
ENTRYPOINT ["./entrypoint.sh"]