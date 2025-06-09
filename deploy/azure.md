# Deploy to Azure

## Option 1: Azure Container Instances (Recommended)

### Prerequisites
- Azure account
- Azure CLI installed
- Docker installed
- OpenAI API key

### Steps

1. **Login to Azure**:
   ```bash
   az login
   ```

2. **Create Resource Group**:
   ```bash
   az group create --name pre-sales-evaluator-rg --location eastus
   ```

3. **Build and push to Azure Container Registry**:
   ```bash
   # Create ACR
   az acr create --resource-group pre-sales-evaluator-rg --name presalesevaluator --sku Basic
   
   # Login to ACR
   az acr login --name presalesevaluator
   
   # Build and push
   docker build -t pre-sales-evaluator .
   docker tag pre-sales-evaluator presalesevaluator.azurecr.io/pre-sales-evaluator:latest
   docker push presalesevaluator.azurecr.io/pre-sales-evaluator:latest
   ```

4. **Deploy Container Instance**:
   ```bash
   az container create \
     --resource-group pre-sales-evaluator-rg \
     --name pre-sales-evaluator \
     --image presalesevaluator.azurecr.io/pre-sales-evaluator:latest \
     --registry-login-server presalesevaluator.azurecr.io \
     --registry-username presalesevaluator \
     --registry-password $(az acr credential show --name presalesevaluator --query "passwords[0].value" -o tsv) \
     --dns-name-label pre-sales-evaluator-unique \
     --ports 8501 \
     --environment-variables OPENAI_API_KEY="your-openai-api-key"
   ```

5. **Access your app**:
   - Your app will be available at: `http://pre-sales-evaluator-unique.eastus.azurecontainer.io:8501`

## Option 2: Azure App Service

### Steps

1. **Create App Service Plan**:
   ```bash
   az appservice plan create --name pre-sales-evaluator-plan --resource-group pre-sales-evaluator-rg --sku B1 --is-linux
   ```

2. **Create Web App**:
   ```bash
   az webapp create --resource-group pre-sales-evaluator-rg --plan pre-sales-evaluator-plan --name pre-sales-evaluator-app --deployment-container-image-name presalesevaluator.azurecr.io/pre-sales-evaluator:latest
   ```

3. **Configure Environment Variables**:
   ```bash
   az webapp config appsettings set --resource-group pre-sales-evaluator-rg --name pre-sales-evaluator-app --settings OPENAI_API_KEY="your-openai-api-key"
   ```

## Option 3: Azure Kubernetes Service (AKS)

For high-scale production deployments with auto-scaling and load balancing.

## Benefits
- ✅ Enterprise-grade security
- ✅ Integration with Azure services
- ✅ Auto-scaling capabilities
- ✅ Custom domains and SSL
- ✅ Built-in monitoring and logging 