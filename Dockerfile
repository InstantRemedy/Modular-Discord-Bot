FROM python:3.12


# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./requirements.txt /app
COPY ./app /app

# Create and run virtual environment and install dependencies
RUN pip install -r requirements.txt

# Run the application
CMD ["python3", "main.py"]
