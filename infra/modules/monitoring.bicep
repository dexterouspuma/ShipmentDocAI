// Log Analytics workspace + Application Insights
param prefix string
param location string
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-appi'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

output customerId string = workspace.properties.customerId
output primarySharedKey string = workspace.listKeys().primarySharedKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
