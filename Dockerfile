# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update && apt-get install bash -y && apt-get install nano -y && apt-get install git -y
RUN pip install --upgrade pip
#RUN apt-get update && apt-get upgrade -y && \
#    apt-get install -y nodejs \
#    npm
#RUN apt-get update && apt-get upgrade -y && curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
# RUN pip3 install mysql-connector-python
# RUN apt-get update
# RUN apt-get install mysql-server -y
# RUN systemctl start mysql.service
# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV FLASK_APP=main.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
