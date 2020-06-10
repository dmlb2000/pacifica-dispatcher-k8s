FROM localhost/pacifica/dispatcher-k8s:latest

# Copy your script into the scripts directory
COPY scripts/run /scripts.d/run
RUN chmod +x /scripts.d/run

# Add your own custom uploader config json (this is optional)
COPY uploader.json /data/uploader.json
