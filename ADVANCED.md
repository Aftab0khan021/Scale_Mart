# ScaleMart - Advanced Features Guide

This guide covers the advanced production features for ScaleMart.

## 📊 Monitoring Stack (Prometheus + Grafana)

### Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### What's Monitored

**Application Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users

**Infrastructure Metrics:**
- Redis: Memory usage, hit rate, operations/sec
- MongoDB: Connections, operations, query performance
- Celery: Queue size, task execution time, worker status

**Business Metrics:**
- Orders per minute
- Revenue per hour
- Stock levels
- Flash sale conversion rate

### Alerts Configured

- High error rate (> 5% for 5 minutes)
- High response time (p95 > 1s for 5 minutes)
- Redis/MongoDB down
- High memory usage (> 90%)
- Large Celery queue (> 1000 tasks)
- Low stock products (< 10 items)

### Grafana Dashboards

Login to Grafana (http://localhost:3001) with `admin/admin`

**Pre-configured dashboards:**
- ScaleMart Overview
- API Performance
- Infrastructure Health
- Business Metrics

---

## 🐛 Error Tracking (Sentry)

### Setup

1. **Create Sentry account** at https://sentry.io
2. **Get your DSN** from project settings
3. **Add to environment:**

```bash
# backend/.env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1
ENVIRONMENT=production
```

4. **Install dependencies:**

```bash
cd backend
pip install -r requirements-extra.txt
```

5. **Enable in server.py:**

```python
# Add at the top of server.py
from sentry_integration import sentry_sdk, track_error, track_performance
```

### Features

- **Automatic error capture** - All unhandled exceptions
- **Performance monitoring** - Transaction tracing
- **User context** - Track which users hit errors
- **Release tracking** - Compare errors across versions
- **Alerts** - Email/Slack notifications for new errors

---

## 🚀 CI/CD Pipeline (GitHub Actions)

### What It Does

**On Every Push:**
1. ✅ Run backend tests (pytest)
2. ✅ Run frontend tests (npm test)
3. ✅ Code quality checks (flake8, black, isort)
4. ✅ Security scanning (Trivy)

**On Main Branch:**
5. ✅ Build Docker images
6. ✅ Push to GitHub Container Registry
7. ✅ Deploy to staging (optional)

### Setup

1. **Enable GitHub Actions** in your repository
2. **Add secrets** in repository settings:
   - `SENTRY_DSN` - Your Sentry DSN
   - `DOCKER_USERNAME` - Docker Hub username (optional)
   - `DOCKER_PASSWORD` - Docker Hub token (optional)

3. **Push to trigger:**

```bash
git add .
git commit -m "Enable CI/CD"
git push origin main
```

### View Results

- Go to **Actions** tab in GitHub
- See test results, coverage, and build status
- Download artifacts (coverage reports, test results)

---

## 🧪 Load Testing

### Quick Start

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000

# Open web UI
# http://localhost:8089
```

### Test Scenarios

**1. Normal User Behavior**
- View products (30% of requests)
- Flash buy (50% of requests)
- View orders (10% of requests)
- View admin stats (10% of requests)

**2. High Concurrency Test**
- Everyone buys the same product simultaneously
- Tests atomic inventory operations
- Verifies no overselling

### Running Tests

**Small test (100 users):**
```bash
locust -f tests/load_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

**Large test (10,000 users):**
```bash
locust -f tests/load_test.py --host=http://localhost:8000 --users 10000 --spawn-rate 100
```

**Headless mode (CI/CD):**
```bash
locust -f tests/load_test.py --host=http://localhost:8000 \
  --users 1000 --spawn-rate 50 --run-time 5m --headless
```

### Expected Results

- ✅ Response time p95 < 100ms
- ✅ Error rate < 1% (excluding out-of-stock)
- ✅ Zero overselling (verify in database)
- ✅ System handles 1000+ concurrent users

---

## 💾 Automated Backups

### Setup Cron Job

```bash
# Make scripts executable
chmod +x scripts/backup.sh scripts/restore.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /path/to/Scale_Mart/scripts/backup.sh >> /var/log/scalemart-backup.log 2>&1
```

### Manual Backup

```bash
./scripts/backup.sh
```

**Backs up:**
- MongoDB database
- Redis data
- Environment configuration

**Retention:** 30 days (configurable)

### Restore from Backup

```bash
./scripts/restore.sh /backups/scalemart/scalemart_backup_20260130_020000.tar.gz
```

### Cloud Backup (Optional)

Uncomment in `scripts/backup.sh`:

```bash
# Upload to AWS S3
aws s3 cp "$BACKUP_DIR/scalemart_backup_$DATE.tar.gz" s3://your-bucket/backups/

# Or Google Cloud Storage
gsutil cp "$BACKUP_DIR/scalemart_backup_$DATE.tar.gz" gs://your-bucket/backups/
```

---

## 🏗️ Staging Environment

### Deploy to Staging

```bash
# Start staging environment
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Initialize database
docker-compose exec backend python init_db.py
```

### Staging Configuration

**Differences from production:**
- 2 backend replicas (vs 3+ in production)
- 2 Celery workers (vs 4+ in production)
- 50% transaction sampling for Sentry
- Debug logging enabled
- Separate database volumes

### Environment Variables

```bash
# .env.staging
ENVIRONMENT=staging
SENTRY_DSN=<staging-sentry-dsn>
REACT_APP_BACKEND_URL=https://api-staging.yourdomain.com
```

---

## 📈 Performance Benchmarks

### Run Benchmarks

```bash
# Install dependencies
pip install -r backend/requirements-extra.txt

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000 \
  --users 1000 --spawn-rate 50 --run-time 10m --headless

# Check results
cat locust_stats.csv
```

### Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Response Time (p95) | < 100ms | TBD |
| Concurrent Users | 10,000+ | TBD |
| Throughput | 1000+ req/s | TBD |
| Error Rate | < 1% | TBD |
| Uptime | 99.9% | TBD |

---

## 🔍 Monitoring Best Practices

### 1. Set Up Alerts

Configure Prometheus alerts for:
- Service downtime
- High error rates
- Performance degradation
- Resource exhaustion

### 2. Monitor Business Metrics

Track:
- Conversion rate (views → purchases)
- Average order value
- Stock turnover rate
- Peak traffic times

### 3. Regular Reviews

- Weekly: Review error trends in Sentry
- Daily: Check Grafana dashboards
- Real-time: Monitor during flash sales

### 4. Capacity Planning

Use metrics to plan:
- When to scale workers
- Redis memory requirements
- Database connection pools

---

## 🎯 Next Steps

1. **Enable monitoring** - Start Prometheus + Grafana
2. **Set up Sentry** - Configure error tracking
3. **Run load tests** - Verify performance claims
4. **Schedule backups** - Set up cron jobs
5. **Deploy staging** - Test before production

---

**For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)**  
**For production configuration, see [PRODUCTION.md](./PRODUCTION.md)**
