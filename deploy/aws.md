# Deploy to AWS

## Option 1: AWS ECS Fargate (Recommended)

### Prerequisites
- AWS account with CLI configured
- Docker installed
- OpenAI API key

### Steps

#### 1. Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name pre-sales-evaluator
```

#### 2. Build and Push Docker Image
```bash
# Build image
docker build -t pre-sales-evaluator .

# Create ECR repository
aws ecr create-repository --repository-name pre-sales-evaluator

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag for ECR
docker tag pre-sales-evaluator:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/pre-sales-evaluator:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/pre-sales-evaluator:latest
```

#### 3. Create Task Definition
Create `task-definition.json`:
```json
{
  "family": "pre-sales-evaluator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "pre-sales-evaluator",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/pre-sales-evaluator:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pre-sales-evaluator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### 4. Create ECS Service
```bash
aws ecs create-service \
  --cluster pre-sales-evaluator \
  --service-name pre-sales-evaluator-service \
  --task-definition pre-sales-evaluator \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

#### 5. Configure Application Load Balancer (Optional)
For production deployments, configure an ALB to distribute traffic and enable custom domains.

## Option 2: AWS Lambda + API Gateway

For serverless deployment (requires code modifications for Lambda compatibility).

## Benefits
- Highly scalable
- Enterprise-grade security
- Multiple deployment options
- Integration with AWS services
- Cost-effective for variable workloads 