# PowerShell script to deploy API server only to Azure Container Instances
# Version 3: Generalized with config file support

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "deploy-config.yaml"
)

# Load configuration from YAML file
if (-not (Test-Path $ConfigFile)) {
    Write-Host "Configuration file not found: $ConfigFile" -ForegroundColor Red
    Write-Host "Please copy deploy-config.template.yaml to $ConfigFile and configure your settings." -ForegroundColor Yellow
    exit 1
}

# Read YAML configuration (simple parsing for this use case)
$configContent = Get-Content $ConfigFile -Raw
if ($configContent -match 'prefix:\s*"?([^"\r\n]+)"?') {
    $prefix = $matches[1].Trim()
} else {
    Write-Host "Error: Could not find 'prefix' in configuration file" -ForegroundColor Red
    exit 1
}

if ($configContent -match 'location:\s*"?([^"\r\n]+)"?') {
    $location = $matches[1].Trim()
} else {
    Write-Host "Error: Could not find 'location' in configuration file" -ForegroundColor Red
    exit 1
}

# Generate resource names based on prefix
$ResourceGroup = "rg-$prefix"
$ContainerName = "$prefix-containers"
$KeyVaultName = "$prefix-kv"

Write-Host "Using configuration:" -ForegroundColor Cyan
Write-Host "  Prefix: $prefix" -ForegroundColor Cyan
Write-Host "  Location: $location" -ForegroundColor Cyan
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Cyan
Write-Host "  Container Name: $ContainerName" -ForegroundColor Cyan
Write-Host "  Key Vault: $KeyVaultName" -ForegroundColor Cyan

Write-Host "=== Deploying API Server to Azure Container Instances ===" -ForegroundColor Green

# Check if logged in to Azure
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in to Azure. Please run 'az login' first." -ForegroundColor Red
    exit 1
}
Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green

# Get necessary values from Key Vault
Write-Host "`nGetting secrets from Key Vault..." -ForegroundColor Yellow
$acrPassword = az keyvault secret show --vault-name $KeyVaultName --name "acr-password" --query value -o tsv
$dbPassword = az keyvault secret show --vault-name $KeyVaultName --name "db-password" --query value -o tsv
$apiKey = az keyvault secret show --vault-name $KeyVaultName --name "mcp-api-key" --query value -o tsv

Write-Host "ACR Password: Retrieved" -ForegroundColor Green
Write-Host "DB Password: Retrieved" -ForegroundColor Green

# Get Managed Identity Client ID
$identityClientId = az identity show --resource-group $ResourceGroup --name "$prefix-identity" --query clientId -o tsv
Write-Host "Identity Client ID: Retrieved" -ForegroundColor Green

# Create deployment YAML with actual values
Write-Host "`nCreating deployment configuration..." -ForegroundColor Yellow
$deployYaml = Get-Content "deploy-api-only.yaml" -Raw
$deployYaml = $deployYaml -replace "\{PREFIX_ACR\}", $prefix_acr
$deployYaml = $deployYaml -replace "\{PREFIX\}", $prefix
$deployYaml = $deployYaml -replace "\{LOCATION\}", $location
$deployYaml = $deployYaml -replace "ACR_PASSWORD_PLACEHOLDER", $acrPassword
$deployYaml = $deployYaml -replace "DB_PASSWORD_PLACEHOLDER", $dbPassword
$deployYaml = $deployYaml -replace "API_KEY_PLACEHOLDER", $apiKey
$deployYaml = $deployYaml -replace "AZURE_CLIENT_ID_PLACEHOLDER", $identityClientId

# Save to temporary file
$tempFile = "deploy-api-only-temp.yaml"
$deployYaml | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "`nChecking if container group exists..." -ForegroundColor Yellow
$exists = az container show --resource-group $ResourceGroup --name $ContainerName 2>$null
if ($exists) {
    Write-Host "Container group still exists. It may be in deletion process." -ForegroundColor Yellow
    Write-Host "Waiting additional 30 seconds for deletion to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

Write-Host "`nDeploying new container configuration..." -ForegroundColor Yellow
try {
    az container create --resource-group $ResourceGroup --file $tempFile
    Write-Host "Deployment successful!" -ForegroundColor Green
} catch {
    Write-Host "Deployment failed. Error: $_" -ForegroundColor Red
    Write-Host "`nDebugging: Check the deploy-api-only-temp.yaml file for syntax errors" -ForegroundColor Yellow
}

# Clean up temporary file
if (Test-Path $tempFile) {
    # Keep the file for debugging if deployment failed
    Write-Host "`nTemporary YAML file kept at: $tempFile" -ForegroundColor Cyan
}

Write-Host "`n=== Deployment Status ===" -ForegroundColor Green
Write-Host "API Server URL: http://$prefix-mcp.$location.azurecontainer.io:8080" -ForegroundColor Cyan
Write-Host "Health Check: http://$prefix-mcp.$location.azurecontainer.io:8080/health" -ForegroundColor Cyan
Write-Host "`nNote: MCP server has been removed from Azure. Use local MCP server with API key authentication." -ForegroundColor Yellow

# Check deployment status
Write-Host "`nChecking deployment status..." -ForegroundColor Yellow
$status = az container show --resource-group $ResourceGroup --name $ContainerName --query "provisioningState" -o tsv 2>$null
if ($status -eq "Succeeded") {
    Write-Host "Container deployment successful!" -ForegroundColor Green
} else {
    Write-Host "Container deployment status: $status" -ForegroundColor Yellow
}