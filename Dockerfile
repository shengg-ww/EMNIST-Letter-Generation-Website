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

FROM python:3.8-slim
#update the packages installed in the image
RUN apt-get update -y
# Make a app directory to contain our application
RUN mkdir /app
# Copy every files and folder into the app folder
COPY . /app
# Change our working directory to app fold
WORKDIR /app
# Install all the packages needed to run our web app
RUN pip install -r requirements.txt
# Add every files and folder into the app folder
ADD . /app
# Expose port 5000 for http communication
EXPOSE 5000
# Run gunicorn web server and binds it to the port
CMD gunicorn --bind 0.0.0.0:5000 app:app