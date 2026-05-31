// Container Apps environment + api app (external) + worker app (queue-scaled)
param prefix string
param location string
param tags object

param logAnalyticsCustomerId string
@secure()
param logAnalyticsKey string
param appInsightsConnectionString string

param userAssignedIdentityId string
param userAssignedClientId string
param registryLoginServer string
param apiImage string
param workerImage string

// App settings
param storageAccountName string
param serviceBusNamespace string
param serviceBusQueue string
param docIntelEndpoint string
param sqlConnectionString string
param entraTenantId string
param entraApiClientId string

// Placeholder image used when no image has been pushed yet (first deploy).
var placeholder = 'mcr.microsoft.com/k8se/quickstart:latest'
var apiImageRef = empty(apiImage) ? placeholder : '${registryLoginServer}/${apiImage}'
var workerImageRef = empty(workerImage) ? placeholder : '${registryLoginServer}/${workerImage}'

var commonEnv = [
  { name: 'ENVIRONMENT', value: 'prod' }
  { name: 'STORAGE_ACCOUNT_NAME', value: storageAccountName }
  { name: 'SERVICEBUS_NAMESPACE', value: serviceBusNamespace }
  { name: 'SERVICEBUS_QUEUE_EXTRACTION', value: serviceBusQueue }
  { name: 'DOCINTEL_ENDPOINT', value: docIntelEndpoint }
  { name: 'SQL_CONNECTION_STRING', value: sqlConnectionString }
  { name: 'ENTRA_TENANT_ID', value: entraTenantId }
  { name: 'ENTRA_API_CLIENT_ID', value: entraApiClientId }
  { name: 'AZURE_CLIENT_ID', value: userAssignedClientId }   // for DefaultAzureCredential
  { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
]

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-cae'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-api'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userAssignedIdentityId}': {} }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        { server: registryLoginServer, identity: userAssignedIdentityId }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImageRef
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: commonEnv
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

resource worker 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-worker'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userAssignedIdentityId}': {} }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        { server: registryLoginServer, identity: userAssignedIdentityId }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerImageRef
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: commonEnv
        }
      ]
      // Scale 0 -> N on Service Bus queue depth (KEDA).
      scale: {
        minReplicas: 0
        maxReplicas: 5
        rules: [
          {
            name: 'servicebus-queue'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                namespace: serviceBusNamespace
                queueName: serviceBusQueue
                messageCount: '5'
              }
              identity: userAssignedIdentityId
            }
          }
        ]
      }
    }
  }
}

output apiFqdn string = api.properties.configuration.ingress.fqdn
