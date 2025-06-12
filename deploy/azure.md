# Deploy to Azure

## Option 1: Azure Container Instances (Recommended)

### Prerequisites
- Azure account
- Azure CLI installed
- Docker installed
- OpenAI API key

### Steps

#### 1. Login to Azure
```bash
az login
```

#### 2. Create Resource Group
```bash
az group create --name pre-sales-evaluator-rg --location uksouth
```

#### 3. Build and Push to Azure Container Registry
```bash
# Create ACR
az acr create --resource-group pre-sales-evaluator-rg --name presalesevaluatoracr --sku Basic

# Login to ACR
az acr login --name presalesevaluatoracr

# Build and push
docker build -t presalesevaluatoracr.azurecr.io/pre-sales-evaluator:latest .
docker push presalesevaluatoracr.azurecr.io/pre-sales-evaluator:latest
```

#### 4. Deploy Container Instance
```bash
az container create \
  --resource-group pre-sales-evaluator-rg \
  --name pre-sales-evaluator \
  --image presalesevaluatoracr.azurecr.io/pre-sales-evaluator:latest \
  --registry-login-server presalesevaluatoracr.azurecr.io \
  --registry-username presalesevaluatoracr \
  --registry-password $(az acr credential show --name presalesevaluatoracr --query "passwords[0].value" -o tsv) \
  --dns-name-label pre-sales-evaluator-unique \
  --ports 8501 \
  --environment-variables OPENAI_API_KEY=your_openai_api_key_here \
  --cpu 1 \
  --memory 2
```

#### 5. Get Public URL
```bash
az container show --resource-group pre-sales-evaluator-rg --name pre-sales-evaluator --query ipAddress.fqdn
```

## Option 2: Azure Container Apps

For more advanced scenarios with auto-scaling and traffic splitting.

### Steps
1. **Create Container Apps Environment**
2. **Deploy Container App**
3. **Configure custom domains and SSL**
4. **Set up monitoring and logging**

## Option 3: Azure App Service

For traditional web app deployment with built-in CI/CD.

## Benefits
- Enterprise-grade security
- Integration with Azure services
- Auto-scaling capabilities
- Custom domains and SSL
- Built-in monitoring and logging 