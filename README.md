# Phishing URL Detection Backend

A powerful machine learning-powered REST API for detecting phishing URLs using advanced feature extraction and multiple ML algorithms.

## 🚀 Features

- **Advanced Feature Extraction**: 50+ features extracted from URLs including:
  - Basic URL structure (length, domain, path analysis)
  - Domain-specific features (subdomains, TLD analysis, IP detection)
  - Suspicious patterns (phishing keywords, homograph detection)
  - Entropy-based features (Shannon entropy, character distribution)

- **Multiple ML Models**: Support for various algorithms:
  - XGBoost (default, highest performance)
  - Random Forest
  - Gradient Boosting
  - Logistic Regression
  - Support Vector Machine

- **Production-Ready API**:
  - Fast response times (< 100ms per URL)
  - Batch processing (up to 100 URLs)
  - Rate limiting and security features
  - Comprehensive error handling
  - Health checks and monitoring

- **Easy Deployment**:
  - Docker containerization
  - Docker Compose for orchestration
  - Environment-based configuration
  - Production-ready logging

## 📋 Requirements

- Python 3.8+
- Docker (optional, for containerized deployment)
- 54k+ URL dataset in CSV format

## 🛠️ Installation

### Option 1: Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd phishing-detector-backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**:
   ```bash
   mkdir models data logs
   ```

### Option 2: Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Run with monitoring (optional)**:
   ```bash
   docker-compose --profile with-monitoring up --build
   ```

## 📊 Training the Model

### Step 1: Prepare Your Dataset

Your CSV file should have at least two columns:
- URL column (containing the URLs)
- Label column (0 for legitimate, 1 for phishing)

Example format:
```csv
url,label
https://www.google.com,0
http://phishing-site.fake.com/login,1
https://www.amazon.com/products,0
http://suspicious-banking-site.com/verify,1
```

### Step 2: Train the Model

**Basic training**:
```bash
python train_model.py --dataset path/to/your/dataset.csv
```

**Advanced training with options**:
```bash
python train_model.py \
    --dataset path/to/your/dataset.csv \
    --model-type xgboost \
    --compare-models \
    --hyperparameter-tuning \
    --cross-validation
```

**Available options**:
- `--dataset`: Path to your CSV dataset
- `--url-column`: Name of URL column (default: 'url')
- `--label-column`: Name of label column (default: 'label')
- `--model-type`: Model to train (xgboost, random_forest, gradient_boost, logistic, svm)
- `--compare-models`: Compare multiple model types
- `--hyperparameter-tuning`: Perform hyperparameter optimization
- `--cross-validation`: Perform cross-validation
- `--sample-size`: Use sample of dataset (for testing)

**Example with custom columns**:
```bash
python train_model.py \
    --dataset my_phishing_data.csv \
    --url-column "website_url" \
    --label-column "is_malicious" \
    --model-type xgboost
```

## 🚀 Running the API

### Local Development
```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
python -m app.main
```

### Production
```bash
# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker
docker-compose up -d
```

The API will be available at: `http://localhost:8000`

## 📝 API Usage

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Basic Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "model_status": "loaded",
  "api_version": "1.0.0"
}
```

### Check Single URL
```bash
curl -X POST "http://localhost:8000/check-url" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "http://suspicious-site.com/login"
     }'
```

Response:
```json
{
  "url": "http://suspicious-site.com/login",
  "is_phishing": true,
  "phishing_probability": 0.87,
  "legitimate_probability": 0.13,
  "confidence": 0.87,
  "risk_level": "HIGH",
  "timestamp": "2024-01-15T10:30:00",
  "processing_time_ms": 45.2
}
```

### Batch URL Checking
```bash
curl -X POST "http://localhost:8000/check-urls-batch" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": [
         "https://www.google.com",
         "http://suspicious-site.com/verify",
         "https://www.github.com"
       ]
     }'
```

### Get URL Features (for analysis)
```bash
curl "http://localhost:8000/features/https://example.com"
```

### Model Status
```bash
curl "http://localhost:8000/status"
```

## 🔧 Configuration

Configuration is managed through environment variables:

### Core Settings
```bash
# Server
PORT=8000
HOST=0.0.0.0
WORKERS=4

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,yourdomain.com
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
CHECK_URL_RATE_LIMIT=60/minute
BATCH_CHECK_RATE_LIMIT=10/minute

# Model
MODEL_PATH=models/phishing_detector.joblib
DEFAULT_MODEL_TYPE=xgboost
AUTO_LOAD_MODEL=true

# Data
MAX_URL_LENGTH=2000
MAX_BATCH_SIZE=100
```

### Environment Files
Create `.env` files for different environments:

**.env.development**:
```
ENVIRONMENT=development
LOG_LEVEL=DEBUG
RATE_LIMIT_ENABLED=false
```

**.env.production**:
```
ENVIRONMENT=production
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
```

## 📊 Performance & Metrics

### Expected Performance
- **Single URL prediction**: < 100ms
- **Batch processing**: ~50ms per URL
- **Feature extraction**: ~30ms per URL
- **Memory usage**: ~200MB base + model size
- **Accuracy**: >95% on balanced datasets

### Risk Levels
- **VERY_LOW**: 0.0 - 0.4 phishing probability
- **LOW**: 0.4 - 0.6 phishing probability
- **MEDIUM**: 0.6 - 0.8 phishing probability
- **HIGH**: 0.8 - 1.0 phishing probability

## 🐳 Docker Deployment

### Basic Deployment
```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### With Nginx Proxy
```bash
docker-compose --profile with-nginx up -d
```

### With Monitoring Stack
```bash
docker-compose --profile with-monitoring up -d
```

This includes:
- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3000` (admin/admin)

## 🧪 Testing

### Unit Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### API Testing
```bash
# Test single URL
curl -X POST "http://localhost:8000/check-url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.google.com"}'

# Test batch URLs
python scripts/test_batch_api.py
```

## 📈 Feature Engineering

The system extracts 50+ features from each URL:

### Basic Features (11)
- URL length, domain length
- HTTPS usage, www presence
- Path segments, query parameters
- Fragment presence

### Domain Features (8)
- Subdomain count and length
- Domain numbers and hyphens
- TLD analysis
- IP address detection

### Suspicious Patterns (13)
- Special character counts
- Phishing keywords
- URL shortener detection
- Homograph character detection
- Redirect patterns

### Entropy Features (6)
- Shannon entropy calculation
- Character distribution analysis
- Vowel/digit ratios

### Customization
Add custom features in `app/preprocessing.py`:

```python
def extract_custom_features(self, url: str) -> Dict[str, Any]:
    """Add your custom feature extraction logic"""
    features = {}
    
    # Your custom features here
    features['custom_feature'] = your_logic(url)
    
    return features
```

## 🔒 Security Features

- **Rate limiting**: Prevents API abuse
- **Input validation**: Validates all inputs
- **Error handling**: Secure error messages
- **CORS protection**: Configurable origins
- **Container security**: Non-root user in Docker
- **Logging**: Comprehensive audit logs

## 🚨 Troubleshooting

### Common Issues

1. **Model not loading**:
   ```bash
   # Check if model exists
   ls -la models/
   
   # Retrain model
   python train_model.py --dataset your_data.csv
   ```

2. **Memory issues with large datasets**:
   ```bash
   # Use sampling for training
   python train_model.py --dataset data.csv --sample-size 10000
   ```

3. **Docker build fails**:
   ```bash
   # Clear Docker cache
   docker system prune -a
   
   # Rebuild
   docker-compose build --no-cache
   ```

4. **Rate limit errors**:
   ```bash
   # Disable rate limiting for development
   export RATE_LIMIT_ENABLED=false
   ```

### Logs
```bash
# View API logs
tail -f logs/api.log

# Docker logs
docker-compose logs -f phishing-detector-api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, scikit-learn, and XGBoost
- Inspired by academic research on phishing detection
- Thanks to the cybersecurity community for threat intelligence

---

For questions or issues, please create an issue on GitHub or contact the maintainers.
