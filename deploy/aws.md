# Deploy to AWS

## Option 1: AWS App Runner (Recommended)

### Prerequisites
- AWS account
- Docker image or GitHub repository
- OpenAI API key

### Steps
1. **Build and push Docker image**:
   ```bash
   # Build image
   docker build -t pre-sales-evaluator .
   
   # Tag for ECR
   docker tag pre-sales-evaluator:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/pre-sales-evaluator:latest
   
   # Push to ECR
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/pre-sales-evaluator:latest
   ```

2. **Create App Runner service**:
   - Go to AWS App Runner console
   - Create service from ECR image
   - Set environment variable: `OPENAI_API_KEY`
   - Configure auto-scaling (1-10 instances)

## Option 2: AWS ECS Fargate

### Prerequisites
- AWS CLI configured
- Docker installed

### Steps
1. **Create ECS cluster**
2. **Create task definition** with environment variables
3. **Create service** with load balancer
4. **Configure auto-scaling**

## Option 3: AWS Lambda + API Gateway

For serverless deployment (requires code modifications for Lambda compatibility).

## Benefits
- ✅ Highly scalable
- ✅ Enterprise-grade security
- ✅ Multiple deployment options
- ✅ Integration with AWS services
- ⚠️ More complex setup 