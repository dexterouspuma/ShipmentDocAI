# Deployment Runbook — Shipment Document AI → Azure

Step-by-step to deploy into your Azure subscription. Commands are PowerShell.
Steps marked **(you)** need your interactive sign-in; run them yourself in the
terminal by prefixing with `!` so the output comes back to this session.

Prerequisites confirmed on this machine: winget ✓, Python ✓, Node ✓.
Not needed: Docker (images build in Azure via `az acr build`).

---

## Step 1 — Install Azure CLI + Bicep  (one-time)
```powershell
winget install -e --id Microsoft.AzureCLI --accept-package-agreements --accept-source-agreements
# open a NEW terminal afterwards so `az` is on PATH, then:
az bicep install
az version
```

## Step 2 — Sign in  **(you)**
```powershell
az login                       # opens a browser
az account show                # confirm the right subscription
# if you have multiple subscriptions:
az account set --subscription "<your-subscription-name-or-id>"
```

## Step 3 — Create the resource group
```powershell
$RG = "rg-shipdocai-dev"
$LOCATION = "eastus"           # pick your region
az group create -n $RG -l $LOCATION
```

## Step 4 — Deploy the infrastructure (Bicep)
```powershell
# Choose a SQL admin password (store it safely; not committed)
$SQLPW = Read-Host -AsSecureString "SQL admin password"
$SQLPW_PLAIN = [System.Net.NetworkCredential]::new('', $SQLPW).Password

cd infra
# Preview first (no changes made):
az deployment group what-if -g $RG -f main.bicep -p main.parameters.json `
  -p sqlAdminPassword=$SQLPW_PLAIN
# Deploy:
az deployment group create -g $RG -f main.bicep -p main.parameters.json `
  -p sqlAdminPassword=$SQLPW_PLAIN
```
This creates: storage, Service Bus, Document Intelligence, Azure SQL, container
registry, managed identity (+RBAC), and the api/worker Container Apps (running a
placeholder image for now).

## Step 5 — Build & deploy the app images
```powershell
$ACR = az acr list -g $RG --query "[0].name" -o tsv
# Build images in Azure (no local Docker):
az acr build -r $ACR -t api:v1 -f api/Dockerfile .
az acr build -r $ACR -t worker:v1 -f workers/Dockerfile .
# Point the Container Apps at the real images:
az containerapp update -g $RG -n shipdocai-api    --image "$ACR.azurecr.io/api:v1"
az containerapp update -g $RG -n shipdocai-worker --image "$ACR.azurecr.io/worker:v1"
# Get the API URL:
az containerapp show -g $RG -n shipdocai-api --query "properties.configuration.ingress.fqdn" -o tsv
```

## Step 6 — Post-deploy setup (one-time)
1. **Load the database schema.**  Connect to the new Azure SQL DB (Azure Data
   Studio or `sqlcmd -G`) and run `db/schema.sql` then `db/views.sql`.
2. **Grant the app identity DB access** (it signs in as the managed identity).
   As an Entra admin on the DB, run:
   ```sql
   CREATE USER [shipdocai-id] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [shipdocai-id];
   ALTER ROLE db_datawriter ADD MEMBER [shipdocai-id];
   ```
3. **Train custom models** in Document Intelligence Studio (arrival notice,
   carrier invoice, packing list, BOL) using the real samples, then set their IDs:
   ```powershell
   az containerapp update -g $RG -n shipdocai-worker `
     --set-env-vars DOCINTEL_MODEL_ARRIVAL_NOTICE=<id> DOCINTEL_MODEL_CARRIER_INVOICE=<id> ...
   ```
4. **Implement Azure SQL persistence** (`api/app/repository.py AzureSqlRepository`)
   and **the G/L defaults shared store** — both currently file/in-memory.

## Still to wire for a full production deploy
- **Frontend hosting:** the React app (`web/`) isn't in the Bicep yet. Simplest is
  Azure Static Web Apps pointing at `web/` (build → `npm run build`), with its API
  setting pointed at the api Container App URL. (Add as a follow-up.)
- **Auth:** MSAL sign-in in the frontend + the Entra app registration.
- **CORS:** set the api's allowed origin to the deployed frontend URL.

## Rollback / teardown
```powershell
az group delete -n $RG --yes --no-wait    # removes everything in the group
```
