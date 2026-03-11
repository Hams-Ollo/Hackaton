
# Sankey: Request Flow (Tokens/Latency)

```mermaid
sankey-beta
  PR[PR Event] 50 Actions
  Actions 40 AF[Azure Function]
  AF 30 AOA[Azure OpenAI]
  AF 10 AIS[Azure AI Search]
  AOA 25 PR
```
