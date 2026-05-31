// Azure SQL server + database
param prefix string
param location string
param tags object
param uniqueSuffix string
param adminLogin string
@secure()
param adminPassword string

resource server 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: '${prefix}-sql-${substring(uniqueSuffix, 0, 6)}'
  location: location
  tags: tags
  properties: {
    administratorLogin: adminLogin
    administratorLoginPassword: adminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource database 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: server
  name: 'shipdocai'
  location: location
  tags: tags
  sku: { name: 'S1', tier: 'Standard' }   // starting tier per plan
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 10737418240             // 10 GB
  }
}

// Allow other Azure services (e.g. Container Apps) to reach the server.
resource allowAzure 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: server
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

output serverFqdn string = server.properties.fullyQualifiedDomainName
output databaseName string = database.name
// Connection string using Managed Identity (no secrets). The app's identity must
// be added as a contained DB user (post-deploy T-SQL step — see infra/README.md).
output connectionStringIdentity string = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${server.properties.fullyQualifiedDomainName},1433;Database=${database.name};Authentication=ActiveDirectoryMsi;Encrypt=yes;TrustServerCertificate=no;'
