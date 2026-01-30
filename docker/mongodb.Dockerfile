FROM mongo:6

# Expose MongoDB port
EXPOSE 27017

# Use default MongoDB configuration for free tier
CMD ["mongod", "--bind_ip_all"]
