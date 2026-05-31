// User-assigned managed identity + RBAC so the apps reach Azure services
// without secrets (data-plane roles on storage, service bus, doc intelligence,
// and AcrPull on the registry).
param prefix string
param location string
param tags object
param storageAccountName string
param serviceBusNamespaceName string
param docIntelAccountName string
param registryName string

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-id'
  location: location
  tags: tags
}

// Existing resources to scope role assignments to.
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}
resource sb 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' existing = {
  name: serviceBusNamespaceName
}
resource docintel 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: docIntelAccountName
}
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

// Built-in role definition IDs
var roleStorageBlobDataContributor = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var roleServiceBusDataSender       = '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
var roleServiceBusDataReceiver     = '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'
var roleCognitiveServicesUser      = 'a97b65f3-24c7-4388-baec-2e87135dc908'
var roleAcrPull                    = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource raStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, uami.id, roleStorageBlobDataContributor)
  scope: storage
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageBlobDataContributor)
  }
}

resource raSbSender 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sb.id, uami.id, roleServiceBusDataSender)
  scope: sb
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleServiceBusDataSender)
  }
}

resource raSbReceiver 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sb.id, uami.id, roleServiceBusDataReceiver)
  scope: sb
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleServiceBusDataReceiver)
  }
}

resource raDocIntel 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(docintel.id, uami.id, roleCognitiveServicesUser)
  scope: docintel
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesUser)
  }
}

resource raAcr 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, roleAcrPull)
  scope: acr
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAcrPull)
  }
}

output identityId string = uami.id
output principalId string = uami.properties.principalId
output clientId string = uami.properties.clientId
