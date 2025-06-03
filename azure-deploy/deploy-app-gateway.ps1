# Azure Application Gateway deployment script for SSL termination

# Variables
$RESOURCE_GROUP = "rg-ticket-system"
$LOCATION = "japaneast"
$VNET_NAME = "ticket-system-vnet"
$SUBNET_NAME = "appgw-subnet"
$APPGW_NAME = "ticket-system-appgw"
$PUBLIC_IP_NAME = "ticket-system-appgw-pip"
$CONTAINER_FQDN = "ticket-system-mcp.japaneast.azurecontainer.io"

Write-Host "=== Creating Application Gateway for SSL termination ===" -ForegroundColor Green

# Create Virtual Network and Subnet
Write-Host "Creating Virtual Network..."
az network vnet create `
  --resource-group $RESOURCE_GROUP `
  --name $VNET_NAME `
  --location $LOCATION `
  --address-prefix 10.0.0.0/16 `
  --subnet-name $SUBNET_NAME `
  --subnet-prefix 10.0.1.0/24

# Create Public IP
Write-Host "Creating Public IP..."
az network public-ip create `
  --resource-group $RESOURCE_GROUP `
  --name $PUBLIC_IP_NAME `
  --location $LOCATION `
  --sku Standard `
  --allocation-method Static

# Create Application Gateway
Write-Host "Creating Application Gateway..."
az network application-gateway create `
  --resource-group $RESOURCE_GROUP `
  --name $APPGW_NAME `
  --location $LOCATION `
  --vnet-name $VNET_NAME `
  --subnet $SUBNET_NAME `
  --public-ip-address $PUBLIC_IP_NAME `
  --sku Standard_v2 `
  --capacity 1 `
  --http-settings-port 8000 `
  --http-settings-protocol Http `
  --frontend-port 443 `
  --servers $CONTAINER_FQDN

# Generate self-signed certificate for testing
Write-Host "Generating self-signed certificate..." -ForegroundColor Yellow
$cert = New-SelfSignedCertificate `
  -Subject "CN=ticket-system-mcp.japaneast.cloudapp.azure.com" `
  -KeyAlgorithm RSA `
  -KeyLength 2048 `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -NotAfter (Get-Date).AddYears(1)

# Export certificate to PFX
# Get certificate password from environment variable or Key Vault
$certPassword = $env:APPGW_CERT_PASSWORD
if (-not $certPassword) {
    # Try to get from Key Vault
    $certPassword = az keyvault secret show --vault-name "ticket-system-keyvault" --name "app-gateway-cert-password" --query value -o tsv 2>$null
    if (-not $certPassword) {
        Write-Host "Certificate password not found in environment or Key Vault." -ForegroundColor Red
        Write-Host "Please set APPGW_CERT_PASSWORD environment variable or create 'app-gateway-cert-password' secret in Key Vault." -ForegroundColor Yellow
        exit 1
    }
}
$pwd = ConvertTo-SecureString -String $certPassword -Force -AsPlainText
$certPath = Join-Path $PWD "appgw-cert.pfx"
Export-PfxCertificate -Cert $cert -FilePath $certPath -Password $pwd

# Upload certificate to Application Gateway
Write-Host "Uploading SSL certificate..."
az network application-gateway ssl-cert create `
  --resource-group $RESOURCE_GROUP `
  --gateway-name $APPGW_NAME `
  --name appgw-ssl-cert `
  --cert-file $certPath `
  --cert-password $certPassword

# Update listener to use HTTPS
Write-Host "Configuring HTTPS listener..."
az network application-gateway http-listener update `
  --resource-group $RESOURCE_GROUP `
  --gateway-name $APPGW_NAME `
  --name appGatewayHttpListener `
  --frontend-port 443 `
  --ssl-cert appgw-ssl-cert

# Add health probe
Write-Host "Adding health probe..."
az network application-gateway probe create `
  --resource-group $RESOURCE_GROUP `
  --gateway-name $APPGW_NAME `
  --name health-probe `
  --protocol Http `
  --host $CONTAINER_FQDN `
  --path /health `
  --interval 30 `
  --timeout 30 `
  --unhealthy-threshold 3

# Update backend settings to use probe
az network application-gateway http-settings update `
  --resource-group $RESOURCE_GROUP `
  --gateway-name $APPGW_NAME `
  --name appGatewayBackendHttpSettings `
  --probe health-probe

# Get Application Gateway public IP
$PUBLIC_IP = az network public-ip show `
  --resource-group $RESOURCE_GROUP `
  --name $PUBLIC_IP_NAME `
  --query ipAddress -o tsv

Write-Host "=== Application Gateway deployed ===" -ForegroundColor Green
Write-Host "HTTPS endpoint: https://$PUBLIC_IP"
Write-Host "Note: Using self-signed certificate. For production, use a proper SSL certificate." -ForegroundColor Yellow

# Clean up temporary files
Remove-Item $certPath -Force

# Test commands
Write-Host "`n=== Test commands ===" -ForegroundColor Cyan
Write-Host "Health check:"
Write-Host "curl -k https://$PUBLIC_IP/health"
Write-Host "`nWith API key (replace with your actual API key):"
Write-Host "curl -k -H 'x-api-key: YOUR_API_KEY_HERE' https://$PUBLIC_IP/capabilities"