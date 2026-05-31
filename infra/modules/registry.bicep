// Azure Container Registry
param prefix string
param location string
param tags object
param uniqueSuffix string

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: toLower('${prefix}acr${substring(uniqueSuffix, 0, 6)}')
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false   // use managed-identity AcrPull instead of admin creds
  }
}

output registryName string = registry.name
output loginServer string = registry.properties.loginServer
