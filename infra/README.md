# Infrastructure (Bicep)

Provisions all Azure resources for Shipment Document AI into an **existing**
resource group.

## What gets created
| Module | Resource |
|---|---|
| `monitoring` | Log Analytics workspace + Application Insights |
| `storage` | Storage account + `raw` / `processed` blob containers |
| `servicebus` | Service Bus namespace + `extraction` queue (dead-letter after 5 tries) |
| `documentintelligence` | Azure AI Document Intelligence (S0, supports custom models) |
| `sql` | Azure SQL server + `shipdocai` database (S1) |
| `registry` | Azure Container Registry (Basic) |
| `identity` | User-assigned managed identity + RBAC (no secrets in app config) |
| `containerapps` | Container Apps env + `api` (external) + `worker` (queue-autoscaled 0→5) |

## Security model
The apps authenticate to Azure services via a **user-assigned managed identity**
with least-privilege data-plane roles (Storage Blob Data Contributor, Service Bus
Sender/Receiver, Cognitive Services User, AcrPull). No storage keys or connection
secrets live in app settings — `DefaultAzureCredential` uses the identity.

## Deploy
Prereqs: Azure CLI + Bicep, logged in (`az login`), correct subscription selected.

```powershell
$rg = "rg-shipdocai-dev"
az group create -n $rg -l eastus    # if the RG doesn't exist yet

# Validate / preview
az deployment group what-if -g $rg -f main.bicep -p main.parameters.json `
  -p sqlAdminPassword=$env:SQL_ADMIN_PASSWORD

# Deploy
az deployment group create -g $rg -f main.bicep -p main.parameters.json `
  -p sqlAdminPassword=$env:SQL_ADMIN_PASSWORD
```

First deploy uses a public placeholder image for the apps; CI/CD then builds and
pushes the real images and re-deploys with `-p apiImage=... workerImage=...`.

## Post-deploy steps (one-time)
1. **Apply the DB schema:** run `db/schema.sql` then `db/views.sql` against the
   new database (see `db/README.md`).
2. **Grant the managed identity DB access** (it authenticates as `ActiveDirectoryMsi`).
   Connect to the DB as an Entra admin and run:
   ```sql
   CREATE USER [shipdocai-id] FROM EXTERNAL PROVIDER;   -- the UAMI name
   ALTER ROLE db_datareader ADD MEMBER [shipdocai-id];
   ALTER ROLE db_datawriter ADD MEMBER [shipdocai-id];
   ```
3. **Train custom models** in Document Intelligence Studio (arrival notice, carrier
   invoice, packing list, BOL) and set their model IDs as app settings
   (`DOCINTEL_MODEL_*`).
4. **Set the API CORS origin** to the deployed frontend URL.

## Notes / caveats
- Templates target resource-group scope and have **not been deployed/validated
  against a live subscription** in this scaffold environment. Run `what-if` first.
- `publicNetworkAccess` is Enabled for SQL/Doc Intelligence to keep first setup
  simple; tighten with Private Endpoints / VNet integration before production.
- SQL admin password is passed at deploy time (never committed).
