
# Deployment View (Azure + GitHub)

```mermaid
flowchart TB
  subgraph GitHub Cloud
    GHRepo[Repo]
    GHAct[Actions Runners]
  end

  subgraph Azure Subscription
    subgraph Net[Virtual Network]
      AF[Azure Functions / Container Apps]
      AIS[Azure AI Search]
      KV[Key Vault]
      AppI[Application Insights]
    end
    AOA[Azure OpenAI (private endpoint optional)]
  end

  GHAct -->|Outbound HTTPS| AF
  AF --> KV
  AF --> AIS
  AF --> AppI
  AF --> AOA
  GHRepo --> GHAct
```
