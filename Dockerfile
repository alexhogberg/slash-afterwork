# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app
RUN mkdir -p /app/data/state

# Copy the application files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the Bolt app
EXPOSE 3000

# Command to run the Bolt app
CMD ["python", "bolt.py"]