from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

@dataclass
class SkillNode:
    canonical_name: str
    category: str
    aliases: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    transferable_to: Dict[str, float] = field(default_factory=dict)  # target_skill -> transfer_weight (0.0 - 1.0)

class SkillOntology:
    """
    Production-grade Hierarchical Skill Ontology.
    Maps thousands of technical and business skills into normalized canonical forms,
    hierarchies, parent-child lineages, and transferable relationship matrices.
    """
    def __init__(self):
        self.nodes: Dict[str, SkillNode] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self._build_taxonomy()

    def _add_node(self, node: SkillNode):
        canonical_lower = node.canonical_name.lower()
        self.nodes[canonical_lower] = node
        self.alias_to_canonical[canonical_lower] = node.canonical_name
        for alias in node.aliases:
            self.alias_to_canonical[alias.lower()] = node.canonical_name

    def normalize(self, term: str) -> Optional[str]:
        cleaned = term.strip().lower()
        return self.alias_to_canonical.get(cleaned)

    def get_node(self, canonical_or_alias: str) -> Optional[SkillNode]:
        canonical = self.normalize(canonical_or_alias)
        if canonical:
            return self.nodes.get(canonical.lower())
        return None

    def _build_taxonomy(self):
        # 1. Programming Languages & Ecosystems
        self._add_node(SkillNode(
            canonical_name="Python",
            category="programming_language",
            aliases=["python3", "py", "python 3"],
            children=["Pandas", "NumPy", "FastAPI", "Flask", "Django", "Scikit-learn", "PyTorch", "TensorFlow", "Celery", "SQLAlchemy"],
            related=["R", "Julia", "Ruby"],
            transferable_to={"Go": 0.65, "JavaScript": 0.70, "Ruby": 0.75}
        ))
        self._add_node(SkillNode(
            canonical_name="FastAPI",
            category="backend_framework",
            aliases=["fastapi framework", "fast api"],
            parents=["Python", "REST API"],
            related=["Flask", "Django", "Express.js", "NestJS"],
            transferable_to={"Flask": 0.90, "Django": 0.80, "Express.js": 0.75}
        ))
        self._add_node(SkillNode(
            canonical_name="Flask",
            category="backend_framework",
            aliases=["flask framework"],
            parents=["Python", "REST API"],
            related=["FastAPI", "Django"],
            transferable_to={"FastAPI": 0.90, "Django": 0.80}
        ))
        self._add_node(SkillNode(
            canonical_name="Django",
            category="backend_framework",
            aliases=["django framework", "django rest framework", "drf"],
            parents=["Python", "REST API"],
            related=["FastAPI", "Flask", "Ruby on Rails"],
            transferable_to={"FastAPI": 0.80, "Ruby on Rails": 0.75}
        ))
        self._add_node(SkillNode(
            canonical_name="JavaScript",
            category="programming_language",
            aliases=["js", "es6", "ecmascript"],
            children=["TypeScript", "React", "Node.js", "Express.js", "Vue.js", "Next.js"],
            related=["TypeScript", "Python"],
            transferable_to={"TypeScript": 0.85, "Python": 0.70}
        ))
        self._add_node(SkillNode(
            canonical_name="TypeScript",
            category="programming_language",
            aliases=["ts"],
            parents=["JavaScript"],
            children=["React", "Next.js", "Angular", "NestJS"],
            related=["JavaScript"],
            transferable_to={"JavaScript": 0.95, "Java": 0.65, "C#": 0.65}
        ))
        self._add_node(SkillNode(
            canonical_name="Java",
            category="programming_language",
            aliases=["java 8", "java 11", "java 17", "java 21"],
            children=["Spring Boot", "Spring", "Hibernate", "Maven", "Gradle"],
            related=["Kotlin", "C#", "Scala"],
            transferable_to={"Kotlin": 0.85, "C#": 0.80, "Go": 0.60}
        ))
        self._add_node(SkillNode(
            canonical_name="Go",
            category="programming_language",
            aliases=["golang"],
            children=["Gin", "Echo", "Goroutines", "gRPC"],
            related=["Rust", "C++", "Java"],
            transferable_to={"Rust": 0.60, "C++": 0.60, "Python": 0.70}
        ))

        # 2. Databases & Storage
        self._add_node(SkillNode(
            canonical_name="SQL",
            category="database",
            aliases=["structured query language", "relational database", "rdbms"],
            children=["PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQLite"],
            related=["NoSQL", "Data Modeling"],
            transferable_to={"PostgreSQL": 0.90, "MySQL": 0.90, "SQL Server": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="PostgreSQL",
            category="database",
            aliases=["postgres", "psql", "postgresql database", "pgvector"],
            parents=["SQL"],
            related=["MySQL", "SQL Server", "SQLite"],
            transferable_to={"MySQL": 0.90, "SQL Server": 0.85, "Oracle": 0.80, "SQLite": 0.90}
        ))
        self._add_node(SkillNode(
            canonical_name="MySQL",
            category="database",
            aliases=["mysql database", "mariadb"],
            parents=["SQL"],
            related=["PostgreSQL", "SQLite"],
            transferable_to={"PostgreSQL": 0.90, "SQLite": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="Redis",
            category="database",
            aliases=["redis cache", "redis key-value"],
            related=["Memcached", "RabbitMQ", "Kafka"],
            transferable_to={"Memcached": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="MongoDB",
            category="database",
            aliases=["mongo", "mongodb database"],
            related=["DynamoDB", "CouchDB", "Firestore"],
            transferable_to={"DynamoDB": 0.80, "Firestore": 0.80}
        ))

        # 3. Data Science & Machine Learning
        self._add_node(SkillNode(
            canonical_name="Pandas",
            category="data_science",
            aliases=["pandas dataframe", "python pandas"],
            parents=["Python", "Data Analysis"],
            related=["NumPy", "Polars", "R"],
            transferable_to={"Polars": 0.85, "R": 0.70}
        ))
        self._add_node(SkillNode(
            canonical_name="NumPy",
            category="data_science",
            aliases=["numpy array"],
            parents=["Python", "Linear Algebra"],
            related=["Pandas", "SciPy"],
            transferable_to={"SciPy": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="Scikit-learn",
            category="machine_learning",
            aliases=["sklearn", "scikit learn"],
            parents=["Python", "Machine Learning"],
            related=["XGBoost", "LightGBM"],
            transferable_to={"XGBoost": 0.85, "LightGBM": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="PyTorch",
            category="deep_learning",
            aliases=["torch"],
            parents=["Python", "Deep Learning"],
            related=["TensorFlow", "Keras", "JAX"],
            transferable_to={"TensorFlow": 0.85, "JAX": 0.75}
        ))
        self._add_node(SkillNode(
            canonical_name="TensorFlow",
            category="deep_learning",
            aliases=["tf", "keras"],
            parents=["Python", "Deep Learning"],
            related=["PyTorch", "JAX"],
            transferable_to={"PyTorch": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="RAG",
            category="ai_systems",
            aliases=["retrieval augmented generation", "retrieval-augmented generation"],
            children=["Vector Databases", "Embeddings", "Hybrid Retrieval", "Reranking"],
            related=["LLMs", "NLP", "LangChain", "LlamaIndex"]
        ))
        self._add_node(SkillNode(
            canonical_name="LLMs",
            category="ai_systems",
            aliases=["large language models", "generative ai", "genai", "prompt engineering"],
            children=["RAG", "Fine-Tuning", "Gemini API", "OpenAI API"],
            related=["NLP"]
        ))

        # 4. Business Intelligence & Analytics
        self._add_node(SkillNode(
            canonical_name="Power BI",
            category="business_intelligence",
            aliases=["powerbi", "microsoft power bi"],
            children=["DAX", "Power Query", "Data Modeling"],
            related=["Tableau", "Looker", "Qlik"],
            transferable_to={"Tableau": 0.85, "Looker": 0.80}
        ))
        self._add_node(SkillNode(
            canonical_name="DAX",
            category="business_intelligence",
            aliases=["data analysis expressions"],
            parents=["Power BI"],
            related=["Power Query", "Excel Formulas"]
        ))
        self._add_node(SkillNode(
            canonical_name="Tableau",
            category="business_intelligence",
            aliases=["tableau software", "tableau desktop"],
            related=["Power BI", "Looker"],
            transferable_to={"Power BI": 0.85, "Looker": 0.80}
        ))

        # 5. Cloud & DevOps
        self._add_node(SkillNode(
            canonical_name="AWS",
            category="cloud",
            aliases=["amazon web services", "amazon aws"],
            children=["EC2", "S3", "AWS Lambda", "ECS", "CloudFormation", "DynamoDB"],
            related=["Google Cloud Platform", "Microsoft Azure"],
            transferable_to={"Google Cloud Platform": 0.85, "Microsoft Azure": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="Google Cloud Platform",
            category="cloud",
            aliases=["gcp", "google cloud"],
            children=["BigQuery", "Cloud Run", "GKE", "Compute Engine"],
            related=["AWS", "Microsoft Azure"],
            transferable_to={"AWS": 0.85, "Microsoft Azure": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="Microsoft Azure",
            category="cloud",
            aliases=["azure", "azure cloud"],
            related=["AWS", "Google Cloud Platform"],
            transferable_to={"AWS": 0.85, "Google Cloud Platform": 0.85}
        ))
        self._add_node(SkillNode(
            canonical_name="Docker",
            category="devops",
            aliases=["containerization", "containers", "dockerfile", "docker compose"],
            children=["Docker Compose", "Containerization"],
            related=["Kubernetes", "Podman"],
            transferable_to={"Podman": 0.95}
        ))
        self._add_node(SkillNode(
            canonical_name="Kubernetes",
            category="devops",
            aliases=["k8s", "k8s orchestration"],
            parents=["DevOps"],
            related=["Docker", "Helm", "OpenShift"],
            transferable_to={"OpenShift": 0.90}
        ))
        self._add_node(SkillNode(
            canonical_name="CI/CD",
            category="devops",
            aliases=["continuous integration", "continuous deployment", "github actions", "gitlab ci", "jenkins"],
            children=["GitHub Actions", "GitLab CI", "Jenkins"]
        ))

        # 6. Frontend
        self._add_node(SkillNode(
            canonical_name="React",
            category="frontend",
            aliases=["react.js", "reactjs"],
            parents=["JavaScript"],
            children=["Next.js", "Redux", "React Query"],
            related=["Vue.js", "Angular", "Svelte"],
            transferable_to={"Vue.js": 0.80, "Angular": 0.70, "Next.js": 0.95}
        ))
        self._add_node(SkillNode(
            canonical_name="Next.js",
            category="frontend",
            aliases=["nextjs"],
            parents=["React", "TypeScript"],
            related=["Remix", "Gatsby", "Nuxt.js"],
            transferable_to={"Remix": 0.85, "Nuxt.js": 0.75}
        ))
        self._add_node(SkillNode(
            canonical_name="HTML/CSS",
            category="frontend",
            aliases=["html", "css", "html5", "css3", "tailwind", "sass"],
            children=["Tailwind CSS", "Sass", "Bootstrap"]
        ))

        # 7. Software Engineering Fundamentals
        self._add_node(SkillNode(
            canonical_name="REST API",
            category="architecture",
            aliases=["rest", "restful", "restful apis", "rest apis", "api design"],
            children=["FastAPI", "Flask", "Express.js"],
            related=["GraphQL", "gRPC"],
            transferable_to={"GraphQL": 0.75, "gRPC": 0.70}
        ))
        self._add_node(SkillNode(
            canonical_name="System Design",
            category="architecture",
            aliases=["microservices", "distributed systems", "software architecture"]
        ))
        self._add_node(SkillNode(
            canonical_name="Git",
            category="tools",
            aliases=["git version control", "github", "gitlab"],
            children=["GitHub", "GitLab"]
        ))

ontology = SkillOntology()
