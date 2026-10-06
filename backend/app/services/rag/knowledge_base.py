from typing import List, Dict, Any

SEED_KNOWLEDGE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "title": "Resume Optimization Grounding Principles",
        "category": "resume_principle",
        "content": """
Core Rule of Evidence-Grounded Optimization:
Never invent candidate metrics, responsibilities, years of experience, or unpracticed technologies.
When rewriting bullet points, adhere to the Google XYZ framework: 'Accomplished [X] as measured by [Y] by doing [Z]'.
If the candidate has weak evidence (e.g. 'Python' listed only in skills), prompt the candidate to clarify an existing project rather than hallucinating a production deployment.
Distinguish clearly between active leadership ('Architected', 'Spearheaded') and contributing participation ('Collaborated with', 'Contributed to').
Preserve absolute factual accuracy at all times.
        """,
        "metadata": {"type": "guidelines", "target": "resume_enhancement"}
    },
    {
        "title": "Backend Engineering Taxonomy and System Design Standards",
        "category": "skill_definition",
        "content": """
Backend engineering encompasses server-side logic, API design, database architecture, and asynchronous processing.
Key Frameworks: FastAPI, Flask, Django (Python); Spring Boot (Java); Express, NestJS (Node/TypeScript); Gin, Echo (Go).
Relational Databases: PostgreSQL, MySQL, SQL Server. Key competencies: ACID compliance, indexing, query optimization, connection pooling, migrations.
In-Memory Stores: Redis, Memcached for caching, rate limiting, and pub/sub messaging.
Asynchronous Task Queues: Celery, RQ, BullMQ for handling long-running background workloads without blocking HTTP request lifecycles.
        """,
        "metadata": {"domain": "backend", "seniority": "all"}
    },
    {
        "title": "Data Engineering and Business Intelligence Taxonomy",
        "category": "skill_definition",
        "content": """
Data Engineering involves ETL/ELT pipelines, distributed processing, and analytical modeling.
Business Intelligence Tools: Power BI (DAX, Power Query, Data Modeling), Tableau, Looker.
Data Warehouses: Snowflake, BigQuery, Amazon Redshift, Databricks.
Processing Engines: Apache Spark, Pandas, Polars.
Key Skills: Dimensional modeling (star/snowflake schema), window functions in SQL, data lineage, and data quality testing.
Transferability: A candidate strong in Power BI DAX has strong transferable capability to Tableau and SQL analytical queries.
        """,
        "metadata": {"domain": "data_bi", "seniority": "mid_senior"}
    },
    {
        "title": "Cloud Architecture and DevOps Ecosystem",
        "category": "role_taxonomy",
        "content": """
Cloud Platforms: AWS, Google Cloud Platform (GCP), Microsoft Azure.
Core Services: Compute (EC2, Cloud Run, GKE, ECS), Storage (S3, Cloud Storage), Managed Databases (RDS, Cloud SQL, DynamoDB).
Containerization: Docker (Dockerfiles, multi-stage builds, Docker Compose).
Orchestration: Kubernetes (Deployments, Services, Ingress, Helm).
Infrastructure as Code: Terraform, CloudFormation.
CI/CD Pipelines: GitHub Actions, GitLab CI, ArgoCD.
Cross-Cloud Transferability: Cloud concepts (IAM, VPCs, Object Storage, Container orchestration) are 80-85% transferable across AWS, GCP, and Azure.
        """,
        "metadata": {"domain": "cloud_devops"}
    },
    {
        "title": "Machine Learning and GenAI / RAG Engineering",
        "category": "skill_definition",
        "content": """
Machine Learning and AI Systems encompass Classical ML (Scikit-learn, XGBoost) and Deep Learning (PyTorch, TensorFlow).
Modern GenAI / RAG Architecture:
- Document chunking strategies (semantic chunking, recursive character splitting)
- Embeddings and dense vector representations (e.g. text-embedding-004)
- Vector stores (pgvector, Milvus, Pinecone, Qdrant)
- Hybrid search (combining dense vector cosine similarity with BM25 keyword matching via Reciprocal Rank Fusion)
- Re-ranking models (Cross-encoders)
- Evidence verification and structured generation preventing hallucinations.
        """,
        "metadata": {"domain": "ai_ml"}
    },
    {
        "title": "Effective Tech Cover Letters and Recruiter Outreach",
        "category": "application_guidance",
        "content": """
Recruiters and hiring managers spend an average of 30-45 seconds skimming cover letters and outreach messages.
Guidelines:
1. Immediately cite 2-3 specific verified accomplishments from your resume that directly solve the team's core problems.
2. Address the company's stated engineering challenges or business domain.
3. Keep recruiter messages under 150 words: Greeting -> Role & Relevance -> Specific Evidence Hook -> Clear Call to Action.
4. Keep cover letters under 350 words: Opening Hook -> 2 Body Paragraphs with cited evidence -> Closing with enthusiasm and availability.
5. Never claim skills or metrics not backed by candidate record.
        """,
        "metadata": {"type": "application_templates"}
    }
]
