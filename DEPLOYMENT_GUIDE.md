# 🚀 Pre-Sales Document Evaluator - Deployment Guide

Quick deployment guide for the Pre-Sales Document Evaluator, ranked from easiest to hardest.

## 🐳 Docker (Recommended - Most Flexible)
**⏱️ Time:** 10 minutes | **💰 Cost:** Varies by provider | **🎯 Difficulty:** ⭐⭐

### Prerequisites
- Docker installed
- OpenAI API key

### Steps
1. **Build the container:**
   ```bash
   docker build -t presales-evaluator .
   ```

2. **Run locally:**
   ```bash
   docker run -p 8501:8501 -e OPENAI_API_KEY=your_key_here presales-evaluator
   ```

3. **Access the app:**
   - Open http://localhost:8501

4. **Deploy to any cloud provider:**
   - Push to Docker Hub, AWS ECR, or Azure Container Registry
   - Deploy to your preferred container service

---

## ☁️ AWS App Runner (Production Ready)
**⏱️ Time:** 30 minutes | **💰 Cost:** ~$20/month | **🎯 Difficulty:** ⭐⭐⭐

### Features
- ✅ Enterprise-grade scaling
- ✅ High availability
- ✅ Custom domains
- ✅ Auto-scaling based on traffic

See `deploy/aws.md` for full instructions.

---

## 🔷 Azure Container Instances
**⏱️ Time:** 20 minutes | **💰 Cost:** ~$15/month | **🎯 Difficulty:** ⭐⭐⭐

### Features
- ✅ Fast deployment
- ✅ Pay-per-use pricing
- ✅ Integration with Azure services
- ✅ Built-in monitoring

See `deploy/azure.md` for full instructions.

---

## 📋 Required Environment Variables

All deployment methods require:
- `OPENAI_API_KEY` - Your OpenAI API key

---

## 📊 Platform Comparison

| Platform | Cost/Month | Setup Time | Scaling | Custom Domain |
|----------|------------|------------|---------|---------------|
| Docker (Local) | Free | 5 min | Manual | No |
| AWS App Runner | ~$20 | 30 min | Auto | Yes |
| Azure Container | ~$15 | 20 min | Manual/Auto | Yes |

---

## 💡 Recommendation

- **For Development/Testing:** Use Docker locally
- **For Production:** Use AWS App Runner or Azure Container Instances
- **For Enterprise:** Consider AWS App Runner with custom domain and monitoring

---

## 🆘 Need Help?

1. Check the detailed deployment guides in the `deploy/` folder
2. Ensure your OpenAI API key is valid
3. Verify all environment variables are set correctly

Choose the deployment method that best fits your needs and budget! 