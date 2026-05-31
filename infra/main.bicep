/* ============================================================================
   Shipment Document AI — main Bicep (resource-group scoped)
   Provisions: monitoring, storage, service bus, document intelligence, Azure SQL,
   container registry, a user-assigned identity (with RBAC), and two Container
   Apps (api + worker) on a shared environment.

   Deploy:
     az deployment group create -g <rg> -f main.bicep -p main.parameters.json \
        -p sqlAdminPassword=<secret>
   ============================================================================ */
targetScope = 'resourceGroup'

@description('Short prefix for resource names, e.g. shipdocai')
param prefix string = 'shipdocai'

@description('Azure region')
param location string = resourceGroup().location

@description('Environment tag: dev | prod')
param environmentName string = 'dev'

@description('Entra tenant id (for API token validation)')
param entraTenantId string = subscription().tenantId

@description('Entra API app client id / audience')
param entraApiClientId string = ''

@description('SQL admin login')
param sqlAdminLogin string = 'shipdocadmin'

@secure()
@description('SQL admin password (pass at deploy time; do not commit)')
param sqlAdminPassword string

@description('Container image tags (set by CI/CD)')
param apiImage string = ''
param workerImage string = ''

var uniqueSuffix = uniqueString(resourceGroup().id)
var tags = { app: 'shipment-document-ai', env: environmentName }

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: { prefix: prefix, location: location, tags: tags }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: { prefix: prefix, location: location, tags: tags, uniqueSuffix: uniqueSuffix }
}

module servicebus 'modules/servicebus.bicep' = {
  name: 'servicebus'
  params: { prefix: prefix, location: location, tags: tags, uniqueSuffix: uniqueSuffix }
}

module docintel 'modules/documentintelligence.bicep' = {
  name: 'docintel'
  params: { prefix: prefix, location: location, tags: tags, uniqueSuffix: uniqueSuffix }
}

module sql 'modules/sql.bicep' = {
  name: 'sql'
  params: {
    prefix: prefix, location: location, tags: tags, uniqueSuffix: uniqueSuffix
    adminLogin: sqlAdminLogin, adminPassword: sqlAdminPassword
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  params: { prefix: prefix, location: location, tags: tags, uniqueSuffix: uniqueSuffix }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  params: {
    prefix: prefix, location: location, tags: tags
    storageAccountName: storage.outputs.accountName
    serviceBusNamespaceName: servicebus.outputs.namespaceName
    docIntelAccountName: docintel.outputs.accountName
    registryName: registry.outputs.registryName
  }
}

module apps 'modules/containerapps.bicep' = {
  name: 'containerapps'
  params: {
    prefix: prefix, location: location, tags: tags
    logAnalyticsCustomerId: monitoring.outputs.customerId
    logAnalyticsKey: monitoring.outputs.primarySharedKey
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    userAssignedIdentityId: identity.outputs.identityId
    userAssignedClientId: identity.outputs.clientId
    registryLoginServer: registry.outputs.loginServer
    apiImage: apiImage
    workerImage: workerImage
    // App settings (non-secret; secrets resolved via managed identity at runtime)
    storageAccountName: storage.outputs.accountName
    serviceBusNamespace: servicebus.outputs.namespaceName
    serviceBusQueue: servicebus.outputs.queueName
    docIntelEndpoint: docintel.outputs.endpoint
    sqlConnectionString: sql.outputs.connectionStringIdentity
    entraTenantId: entraTenantId
    entraApiClientId: entraApiClientId
  }
}

output apiFqdn string = apps.outputs.apiFqdn
output documentIntelligenceEndpoint string = docintel.outputs.endpoint
output sqlServerFqdn string = sql.outputs.serverFqdn
output registryLoginServer string = registry.outputs.loginServer
