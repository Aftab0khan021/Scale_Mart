FROM redis:7-alpine

# Expose Redis port
EXPOSE 6379

# Use default Redis configuration for free tier
CMD ["redis-server", "--maxmemory", "25mb", "--maxmemory-policy", "allkeys-lru"]
