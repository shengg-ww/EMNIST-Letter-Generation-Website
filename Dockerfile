FROM tensorflow/serving

# Copy everything from the build context to the container root
COPY / /

# Set environment variables
ENV MODEL_NAME=saved_cgan
ENV MODEL_BASE_PATH=/ModelDev

# Expose REST and gRPC ports
EXPOSE 8500
EXPOSE 8501

# Create an entrypoint script for TensorFlow Serving
RUN echo '#!/bin/bash \n\n\
tensorflow_model_server \
--rest_api_port=$PORT \
--model_name=${MODEL_NAME} \
--model_base_path=${MODEL_BASE_PATH}/${MODEL_NAME} \
"$@"' > /usr/bin/tf_serving_entrypoint.sh \
&& chmod +x /usr/bin/tf_serving_entrypoint.sh

# Use the official Python 3.8 image as the base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the Flask app will run on (default is 5000)
EXPOSE 5000

# Set the command to run the Flask app
CMD ["python", "app.py"]
