// Service Bus namespace + extraction queue (with dead-lettering)
param prefix string
param location string
param tags object
param uniqueSuffix string

resource namespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: '${prefix}-sb-${substring(uniqueSuffix, 0, 6)}'
  location: location
  tags: tags
  sku: { name: 'Standard', tier: 'Standard' }
}

resource queue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: namespace
  name: 'extraction'
  properties: {
    maxDeliveryCount: 5                 // dead-letter after 5 failed attempts
    lockDuration: 'PT5M'                // 5 min to process before re-delivery
    deadLetteringOnMessageExpiration: true
    defaultMessageTimeToLive: 'P1D'
  }
}

output namespaceName string = namespace.name
output queueName string = queue.name
