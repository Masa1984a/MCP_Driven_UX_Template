#!/bin/bash
# Deploy script for MCP Server to GCP Cloud Run

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_NAME="mcp-server"
IMAGE_NAME="mcp-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting MCP Server deployment to GCP Cloud Run${NC}"

# Check if required tools are installed
check_dependencies() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies check passed${NC}"
}

# Setup GCP project
setup_project() {
    echo -e "${YELLOW}🔧 Setting up GCP project...${NC}"
    
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    echo "Enabling required APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    echo -e "${GREEN}✅ Project setup completed${NC}"
}

# Create secrets
create_secrets() {
    echo -e "${YELLOW}🔐 Creating secrets...${NC}"
    
    # Check if secrets exist
    if ! gcloud secrets describe mcp-api-key >/dev/null 2>&1; then
        echo "Creating mcp-api-key secret..."
        read -s -p "Enter API key: " API_KEY
        echo
        echo -n "$API_KEY" | gcloud secrets create mcp-api-key --data-file=-
    else
        echo "mcp-api-key secret already exists"
    fi
    
    if ! gcloud secrets describe mcp-api-base-url >/dev/null 2>&1; then
        echo "Creating mcp-api-base-url secret..."
        read -p "Enter API base URL: " API_BASE_URL
        echo -n "$API_BASE_URL" | gcloud secrets create mcp-api-base-url --data-file=-
    else
        echo "mcp-api-base-url secret already exists"
    fi
    
    echo -e "${GREEN}✅ Secrets created${NC}"
}

# Create service account
create_service_account() {
    echo -e "${YELLOW}👤 Creating service account...${NC}"
    
    SA_NAME="mcp-server-sa"
    SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
    
    # Create service account if it doesn't exist
    if ! gcloud iam service-accounts describe $SA_EMAIL >/dev/null 2>&1; then
        gcloud iam service-accounts create $SA_NAME \
            --display-name="MCP Server Service Account" \
            --description="Service account for MCP Server on Cloud Run"
    else
        echo "Service account already exists"
    fi
    
    # Grant permissions to access secrets
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor"
    
    echo -e "${GREEN}✅ Service account setup completed${NC}"
}

# Build and deploy
build_and_deploy() {
    echo -e "${YELLOW}🏗️ Building and deploying...${NC}"
    
    # Submit build to Cloud Build
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_REGION=$REGION \
        ..
    
    echo -e "${GREEN}✅ Build and deployment completed${NC}"
}

# Manual deployment option
manual_deploy() {
    echo -e "${YELLOW}🚀 Manual deployment option...${NC}"
    
    IMAGE_URL="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"
    
    echo "Building image locally..."
    docker build -t $IMAGE_URL .
    
    echo "Pushing image to GCR..."
    docker push $IMAGE_URL
    
    echo "Deploying to Cloud Run..."
    gcloud run deploy $SERVICE_NAME \
        --image=$IMAGE_URL \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --memory=512Mi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=10 \
        --timeout=900s \
        --concurrency=100 \
        --set-env-vars="MCP_CLOUD_MODE=true,MCP_LOG_LEVEL=INFO,MCP_AUTH_PROVIDER=api_key" \
        --set-secrets="MCP_API_KEY=mcp-api-key:latest,MCP_API_BASE_URL=mcp-api-base-url:latest" \
        --service-account="mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com"
    
    echo -e "${GREEN}✅ Manual deployment completed${NC}"
}

# Get service URL
get_service_url() {
    echo -e "${YELLOW}🌐 Getting service URL...${NC}"
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    echo -e "${GREEN}✅ Service deployed successfully!${NC}"
    echo -e "${GREEN}🔗 Service URL: $SERVICE_URL${NC}"
    echo -e "${GREEN}🏥 Health check: $SERVICE_URL/health${NC}"
    echo -e "${GREEN}📚 API docs: $SERVICE_URL/docs${NC}"
}

# Test deployment
test_deployment() {
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    echo "Testing health endpoint..."
    if curl -f "$SERVICE_URL/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        exit 1
    fi
    
    echo "Testing root endpoint..."
    if curl -f "$SERVICE_URL/" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Root endpoint test passed${NC}"
    else
        echo -e "${RED}❌ Root endpoint test failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All tests passed${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}🎯 MCP Server GCP Cloud Run Deployment${NC}"
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service Name: $SERVICE_NAME"
    echo ""
    
    check_dependencies
    setup_project
    create_secrets
    create_service_account
    
    echo -e "${YELLOW}Choose deployment method:${NC}"
    echo "1) Cloud Build (recommended)"
    echo "2) Manual build and deploy"
    read -p "Enter choice (1-2): " choice
    
    case $choice in
        1)
            build_and_deploy
            ;;
        2)
            manual_deploy
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    get_service_url
    test_deployment
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "1. Update your MCP client to use the new service URL"
    echo "2. Test SSE connections with your MCP client"
    echo "3. Monitor logs: gcloud logs read --service=$SERVICE_NAME"
    echo "4. Monitor metrics in Cloud Console"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Environment variables:"
        echo "  PROJECT_ID    GCP project ID (default: your-project-id)"
        echo "  REGION        GCP region (default: asia-northeast1)"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac