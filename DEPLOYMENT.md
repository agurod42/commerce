# Deployment Guide

This guide covers deploying the Wholesale AI Agent to production environments.

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8+ installed
- PostgreSQL 12+ (recommended for production)
- Nginx (for reverse proxy, optional)
- Docker (optional, for containerized deployment)
- SSL certificate (for HTTPS)

## 🚀 Production Deployment Options

### Option 1: Direct Server Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3.8 python3.8-venv python3.8-dev \
                 postgresql postgresql-contrib \
                 nginx supervisor git -y

# Create application user
sudo useradd -m -s /bin/bash wholesale-agent
sudo su - wholesale-agent
```

#### 2. Application Installation

```bash
# Clone repository
git clone <your-repo-url> wholesale-agent
cd wholesale-agent

# Create virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install production extras
pip install gunicorn psycopg2-binary
```

#### 3. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE wholesale_agent;
CREATE USER wholesale_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE wholesale_agent TO wholesale_user;
\q
EOF
```

#### 4. Environment Configuration

Create `/home/wholesale-agent/wholesale-agent/.env`:

```bash
# Production Environment
ENVIRONMENT=production
SECRET_KEY=your_very_secure_secret_key_here_min_32_chars

# Database
DATABASE_URL=postgresql://wholesale_user:secure_password_here@localhost/wholesale_agent

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-3.5-turbo

# Logging
LOG_LEVEL=INFO
LOG_STRUCTURED=true
LOG_DIR=/home/wholesale-agent/logs

# Security
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
RATE_LIMIT_PER_MINUTE=100

# Performance
QUERY_TIMEOUT=30
MAX_CONCURRENT_QUERIES=20
CACHE_ENABLED=true

# Monitoring
ENABLE_METRICS=true
```

#### 5. Initialize Database

```bash
# Create logs directory
mkdir -p /home/wholesale-agent/logs

# Initialize database
python -m wholesale_agent.cli.main --migrate

# Generate sample data (optional)
python -m wholesale_agent.cli.main --generate-data
```

#### 6. Create Systemd Service

Create `/etc/systemd/system/wholesale-agent.service`:

```ini
[Unit]
Description=Wholesale AI Agent
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=wholesale-agent
Group=wholesale-agent
WorkingDirectory=/home/wholesale-agent/wholesale-agent
Environment=PATH=/home/wholesale-agent/wholesale-agent/venv/bin
EnvironmentFile=/home/wholesale-agent/wholesale-agent/.env
ExecStart=/home/wholesale-agent/wholesale-agent/venv/bin/python -m wholesale_agent.cli.main
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10
SyslogIdentifier=wholesale-agent

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/wholesale-agent/logs
ReadWritePaths=/home/wholesale-agent/wholesale-agent

[Install]
WantedBy=multi-user.target
```

#### 7. Start and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable wholesale-agent
sudo systemctl start wholesale-agent
sudo systemctl status wholesale-agent
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app user
RUN useradd -m -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m wholesale_agent.cli.main --config-check || exit 1

# Default command
CMD ["python", "-m", "wholesale_agent.cli.main"]
```

#### 2. Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  database:
    image: postgres:14
    environment:
      POSTGRES_DB: wholesale_agent
      POSTGRES_USER: wholesale_user
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wholesale_user -d wholesale_agent"]
      interval: 10s
      timeout: 5s
      retries: 5

  wholesale-agent:
    build: .
    depends_on:
      database:
        condition: service_healthy
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://wholesale_user:secure_password_here@database:5432/wholesale_agent
      - LLM_PROVIDER=openai
      - LLM_API_KEY=${LLM_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
      - LOG_STRUCTURED=true
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-m", "wholesale_agent.cli.main", "--config-check"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

#### 3. Environment File

Create `.env` for Docker Compose:

```bash
LLM_API_KEY=your_openai_api_key_here
SECRET_KEY=your_very_secure_secret_key_here
```

#### 4. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f wholesale-agent

# Run migrations
docker-compose exec wholesale-agent python -m wholesale_agent.cli.main --migrate

# Generate sample data
docker-compose exec wholesale-agent python -m wholesale_agent.cli.main --generate-data
```

## 🔧 Configuration Management

### Environment-Specific Configurations

Create configuration files for different environments:

**config.production.json**:
```json
{
  "database": {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30
  },
  "llm": {
    "timeout": 30,
    "max_tokens": 2000
  },
  "logging": {
    "level": "INFO",
    "structured": true,
    "file_rotation_mb": 50,
    "backup_count": 10
  },
  "security": {
    "rate_limit_per_minute": 120,
    "session_timeout_minutes": 30
  },
  "performance": {
    "query_timeout_seconds": 45,
    "max_concurrent_queries": 50,
    "cache_ttl_seconds": 600
  }
}
```

### Secrets Management

For production, use a secrets management system:

#### AWS Secrets Manager
```bash
# Install AWS CLI
pip install awscli

# Store secrets
aws secretsmanager create-secret \
    --name wholesale-agent/production \
    --secret-string '{"LLM_API_KEY":"your_key","SECRET_KEY":"your_secret"}'

# Retrieve in application
python -c "
import boto3
import json
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='wholesale-agent/production')
secrets = json.loads(response['SecretString'])
print(f'LLM_API_KEY={secrets[\"LLM_API_KEY\"]}')
"
```

#### HashiCorp Vault
```bash
# Store secrets
vault kv put secret/wholesale-agent \
    LLM_API_KEY=your_key \
    SECRET_KEY=your_secret

# Retrieve secrets
vault kv get -format=json secret/wholesale-agent
```

## 📊 Monitoring and Observability

### 1. Application Monitoring

#### Prometheus Metrics

Add to your environment:
```bash
ENABLE_METRICS=true
```

The application exposes metrics at `/metrics`:
- Request duration
- Request count
- Error rates
- Database connection pool status
- LLM response times

#### Grafana Dashboard

Import the provided Grafana dashboard (`monitoring/grafana-dashboard.json`):

1. Login to Grafana
2. Go to Import Dashboard
3. Upload the JSON file
4. Configure data source (Prometheus)

### 2. Log Management

#### ELK Stack (Elasticsearch, Logstash, Kibana)

**logstash.conf**:
```ruby
input {
  file {
    path => "/home/wholesale-agent/logs/*.log"
    start_position => "beginning"
    codec => json
  }
}

filter {
  if [level] == "ERROR" {
    mutate {
      add_tag => [ "error" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "wholesale-agent-%{+YYYY.MM.dd}"
  }
}
```

#### Structured Logging

Enable structured logging in production:
```bash
LOG_STRUCTURED=true
LOG_LEVEL=INFO
```

This outputs JSON logs suitable for log aggregation:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "wholesale_agent.core.agent",
  "message": "User query processed",
  "query": "How much stock do we have?",
  "response_time_ms": 1250,
  "user_id": "user123",
  "session_id": "session456"
}
```

### 3. Health Checks

#### Kubernetes Health Checks

```yaml
livenessProbe:
  exec:
    command:
    - python
    - -m
    - wholesale_agent.cli.main
    - --config-check
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  exec:
    command:
    - python
    - -c
    - "import wholesale_agent.models; wholesale_agent.models.db_manager.get_session().__enter__().execute('SELECT 1')"
  initialDelaySeconds: 5
  periodSeconds: 10
```

#### Load Balancer Health Checks

Create a health check endpoint:
```python
# Add to your web server
@app.route('/health')
def health_check():
    try:
        # Check database
        with db_manager.get_session() as session:
            session.execute('SELECT 1')
        
        # Check LLM availability
        llm_client = LLMClient()
        if not llm_client.is_available():
            raise Exception("LLM not available")
        
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

## 🔐 Security Hardening

### 1. Server Security

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Disable root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload sshd

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 2. Application Security

#### SSL/TLS Configuration

**Nginx configuration** (`/etc/nginx/sites-available/wholesale-agent`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Rate Limiting

Configure rate limiting in your environment:
```bash
RATE_LIMIT_PER_MINUTE=60
MAX_CONCURRENT_QUERIES=10
```

#### Database Security

```sql
-- Create read-only user for monitoring
CREATE USER monitoring WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE wholesale_agent TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;

-- Restrict permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO wholesale_user;
```

## 🔄 Backup and Recovery

### 1. Database Backups

#### Automated PostgreSQL Backups

Create `/home/wholesale-agent/backup.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/home/wholesale-agent/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="wholesale_agent"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump $DB_NAME > $BACKUP_DIR/wholesale_agent_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/wholesale_agent_$DATE.sql

# Remove backups older than 7 days
find $BACKUP_DIR -name "wholesale_agent_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/wholesale_agent_$DATE.sql.gz s3://your-backup-bucket/
```

#### Schedule Backups

Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * /home/wholesale-agent/backup.sh
```

### 2. Application Data Backups

```bash
# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Backup configuration
cp .env config_backup_$(date +%Y%m%d).env
```

### 3. Disaster Recovery

#### Recovery Procedure

1. **Set up new server** following deployment steps
2. **Restore database**:
   ```bash
   gunzip -c wholesale_agent_20240115_020000.sql.gz | psql wholesale_agent
   ```
3. **Deploy application** using the same configuration
4. **Verify functionality**:
   ```bash
   python -m wholesale_agent.cli.main --config-check
   ```
5. **Update DNS** to point to new server

## 🔄 Updates and Maintenance

### 1. Application Updates

Create update script (`update.sh`):
```bash
#!/bin/bash

# Backup current version
cp -r wholesale-agent wholesale-agent.backup.$(date +%Y%m%d)

# Pull latest changes
cd wholesale-agent
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
python -m wholesale_agent.cli.main --migrate

# Restart service
sudo systemctl restart wholesale-agent

# Check status
sudo systemctl status wholesale-agent
```

### 2. Database Maintenance

#### Regular Maintenance Tasks

```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM VERBOSE;

-- Update statistics
UPDATE pg_stat_user_tables SET n_tup_ins = 0, n_tup_upd = 0, n_tup_del = 0;
```

#### Monitoring Queries

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('wholesale_agent'));

-- Monitor active connections
SELECT count(*) FROM pg_stat_activity WHERE datname='wholesale_agent';

-- Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements 
WHERE query LIKE '%wholesale_agent%' 
ORDER BY mean_time DESC LIMIT 10;
```

## 📈 Scaling

### Horizontal Scaling

#### Load Balancer Configuration

**Nginx upstream**:
```nginx
upstream wholesale_backend {
    least_conn;
    server 10.0.1.10:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://wholesale_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Database Scaling

1. **Read Replicas**: Set up PostgreSQL read replicas for read-heavy workloads
2. **Connection Pooling**: Use PgBouncer for connection pooling
3. **Caching**: Implement Redis for query result caching

### Vertical Scaling

#### Resource Optimization

Monitor resource usage:
```bash
# CPU and memory usage
htop

# Database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Application metrics
curl http://localhost:9090/metrics
```

Optimize configuration based on usage patterns. Prefer JSON config files (e.g., `config.production.json`) for tuning `database.pool_size`, `database.max_overflow`, and related parameters.

This deployment guide provides a comprehensive approach to deploying the Wholesale AI Agent in production environments with proper security, monitoring, and scalability considerations.