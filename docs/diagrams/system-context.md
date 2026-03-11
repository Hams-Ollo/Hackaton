
        # System Context Diagram

        ```mermaid
        flowchart LR
          subgraph Dev[Developers]
            Dev1[Developer]
          end

          subgraph GitHub[GitHub]
            Repo[Repository]
            PR[Pull Request]
            Issues[Issues]
            Actions[GitHub Actions]
          end

          subgraph Azure[Azure]
            AOA[Azure OpenAI]
            AF[Azure Functions / Container Apps]
            AIS[Azure AI Search]
            KV[Key Vault]
            AppI[Application Insights]
          end

          Dev1 -->|push code| Repo
          Repo --> PR
          PR -->|triggers| Actions
          Actions -->|HTTP call| AF
          AF -->|prompt+tools| AOA
          AF -->|RAG| AIS
          AF -->|secrets| KV
          AF -->|logs+metrics| AppI
          AF -->|review
comments| PR
          Issues <-->|ChatOps / triage| AF
        ```
