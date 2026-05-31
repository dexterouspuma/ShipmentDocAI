// Blob storage with raw + processed containers
param prefix string
param location string
param tags object
param uniqueSuffix string

resource account 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: toLower('${prefix}st${substring(uniqueSuffix, 0, 6)}')
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: account
  name: 'default'
}

resource raw 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blob
  name: 'raw'
}

resource processed 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blob
  name: 'processed'
}

output accountName string = account.name
