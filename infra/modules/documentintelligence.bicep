// Azure AI Document Intelligence (Cognitive Services, kind FormRecognizer)
param prefix string
param location string
param tags object
param uniqueSuffix string

resource account 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${prefix}-docintel-${substring(uniqueSuffix, 0, 6)}'
  location: location
  tags: tags
  kind: 'FormRecognizer'
  sku: { name: 'S0' }                  // S0 supports custom models
  properties: {
    customSubDomainName: '${prefix}-docintel-${substring(uniqueSuffix, 0, 6)}'
    publicNetworkAccess: 'Enabled'
    // Entra-only auth is preferred; key auth left enabled for initial setup.
    disableLocalAuth: false
  }
}

output accountName string = account.name
output endpoint string = account.properties.endpoint
