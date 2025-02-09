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

