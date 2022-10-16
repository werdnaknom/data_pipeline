FROM python:3.8

# Set proxy settings
ENV http_proxy http://proxy.jf.intel.com:911
ENV https_proxy http://proxy.jf.intel.com:911

# Copy the current directory contents into the container at /app
COPY requirements.txt requirements.txt
COPY celery_worker.py celery_worker.py
COPY celeryconfig.py celeryconfig.py
COPY config.py config.py

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app




ENV MONGO_DOCKER_NAME "${MONGO_DOCKER_NAME}"
ENV UPLOAD_FOLDER "${UPLOAD_FOLDER}"
ENV RESULTS_FOLDER "${RESULTS_FOLDER}"
ENV CELERY_TEMP_FOLDER "${CELERY_TEMP_FOLDER}"

RUN mkdir "/uploads/"
#RUN chown -R webmaster:webmaster "/uploads/"
RUN mkdir "/CeleryTemp/"


# Add /app to the PYTHONPATH
#ENV PYTHONPATH "${PYTHONPATH}:/app"

