import json
import os

cases = [
    # 1. Senior Backend Engineer
    {
        "id": "case_01_sr_backend",
        "category": "Senior Backend",
        "resume_text": """ALEX MORGAN
alex.morgan@example.com | (555) 011-2233 | San Francisco, CA
SUMMARY: Senior Backend Engineer with 6 years experience building distributed microservices in Python and PostgreSQL.
EXPERIENCE:
Senior Software Engineer at FinScale (2021 - Present)
- Architected payment microservices with FastAPI and PostgreSQL handling 20,000 req/s.
- Reduced database query latency by 45% using Redis caching.
- Orchestrated container deployment with Docker.
Software Engineer at CloudCore (2018 - 2021)
- Built REST APIs using Flask and PostgreSQL.
SKILLS:
Backend: Python, FastAPI, Flask, PostgreSQL, Redis, Docker
EDUCATION:
B.S. Computer Science at UC Berkeley (2014 - 2018)""",
        "ground_truth": {
            "expected_skills": ["Python", "FastAPI", "Flask", "PostgreSQL", "Redis", "Docker"],
            "expected_companies": ["FinScale", "CloudCore"],
            "unsupported_claims": ["Kubernetes", "GraphQL", "Java", "Ruby", "Golang"],
            "expected_metrics": ["20,000 req/s", "45%"]
        }
    },
    # 2. Junior Frontend Developer
    {
        "id": "case_02_jr_frontend",
        "category": "Junior Frontend",
        "resume_text": """SARAH CHEN
sarah.chen@example.com | Seattle, WA
SUMMARY: Frontend Developer with 2 years of experience crafting responsive web apps using React and TypeScript.
EXPERIENCE:
Junior Frontend Developer at PixelForge (2022 - Present)
- Developed responsive web interfaces using React and TypeScript.
- Implemented state management using Redux.
- Styled components using Tailwind CSS and CSS Modules.
SKILLS:
Frontend: React, TypeScript, JavaScript, Redux, HTML, CSS, Tailwind CSS
EDUCATION:
B.S. in Informatics at University of Washington (2018 - 2022)""",
        "ground_truth": {
            "expected_skills": ["React", "TypeScript", "JavaScript", "Redux", "HTML", "CSS"],
            "expected_companies": ["PixelForge"],
            "unsupported_claims": ["Angular", "Vue", "AWS", "Docker", "Python"],
            "expected_metrics": []
        }
    },
    # 3. Data Scientist
    {
        "id": "case_03_data_scientist",
        "category": "Data Science",
        "resume_text": """DAVID PARK
david.park@example.com | Boston, MA
SUMMARY: Data Scientist with 4 years experience building predictive machine learning models in Python.
EXPERIENCE:
Data Scientist at HealthAnalytica (2021 - Present)
- Trained gradient boosting models with Scikit-Learn and Pandas predicting patient readmission with 88% accuracy.
- Analyzed 500,000 clinical records using SQL and PostgreSQL.
Data Analyst at BioMetrics (2019 - 2021)
- Automated monthly analytical dashboards in Python.
SKILLS:
Data & ML: Python, Pandas, Scikit-Learn, SQL, PostgreSQL, NumPy
EDUCATION:
M.S. in Statistics at Columbia University (2017 - 2019)""",
        "ground_truth": {
            "expected_skills": ["Python", "Pandas", "Scikit-Learn", "SQL", "PostgreSQL", "NumPy"],
            "expected_companies": ["HealthAnalytica", "BioMetrics"],
            "unsupported_claims": ["TensorFlow", "PyTorch", "Kubernetes", "Snowflake"],
            "expected_metrics": ["88%", "500,000"]
        }
    },
    # 4. ML Engineer
    {
        "id": "case_04_ml_engineer",
        "category": "Machine Learning",
        "resume_text": """ELENA ROSTOVA
elena.r@example.com | New York, NY
SUMMARY: Machine Learning Engineer specializing in computer vision and deep learning pipelines with PyTorch.
EXPERIENCE:
Machine Learning Engineer at VisionTech (2021 - Present)
- Trained convolutional neural networks with PyTorch achieving 94% mAP on object detection.
- Deployed ML inference endpoints using Docker and FastAPI serving 500 req/s.
SKILLS:
ML & Frameworks: Python, PyTorch, FastAPI, Docker, OpenCV
EDUCATION:
M.S. in Computer Science at NYU (2019 - 2021)""",
        "ground_truth": {
            "expected_skills": ["Python", "PyTorch", "FastAPI", "Docker"],
            "expected_companies": ["VisionTech"],
            "unsupported_claims": ["TensorFlow", "Kubernetes", "AWS SageMaker", "Spark"],
            "expected_metrics": ["94%", "500 req/s"]
        }
    },
    # 5. DevOps / SRE Engineer
    {
        "id": "case_05_devops_sre",
        "category": "DevOps / SRE",
        "resume_text": """MARCUS AURELIUS
marcus.a@example.com | Austin, TX
SUMMARY: Site Reliability Engineer focused on Kubernetes infrastructure, CI/CD, and Terraform automation.
EXPERIENCE:
Senior DevOps Engineer at InfraCloud (2020 - Present)
- Orchestrated multi-region Kubernetes clusters running Docker containers across AWS.
- Automated infrastructure provisioning using Terraform and Ansible.
- Maintained 99.95% system availability across 40 microservices.
SKILLS:
DevOps: Kubernetes, Docker, Terraform, Ansible, AWS, Linux
EDUCATION:
B.S. in Computer Engineering at UT Austin (2016 - 2020)""",
        "ground_truth": {
            "expected_skills": ["Kubernetes", "Docker", "Terraform", "Ansible", "AWS", "Linux"],
            "expected_companies": ["InfraCloud"],
            "unsupported_claims": ["GCP", "Azure", "Pulumi", "Ruby"],
            "expected_metrics": ["99.95%", "40 microservices"]
        }
    },
    # 6. Full Stack Engineer
    {
        "id": "case_06_full_stack",
        "category": "Full Stack",
        "resume_text": """JESSICA TAYLOR
jessica.t@example.com | Chicago, IL
SUMMARY: Full Stack Engineer building end-to-end web applications with React, Node.js, and PostgreSQL.
EXPERIENCE:
Full Stack Developer at Omnicorp (2021 - Present)
- Developed full-stack SaaS features using React, Node.js, and Express.
- Designed database schemas and indexing in PostgreSQL.
SKILLS:
Full Stack: React, JavaScript, Node.js, Express, PostgreSQL, HTML, CSS
EDUCATION:
B.S. in Computer Science at University of Illinois (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["React", "JavaScript", "Node.js", "Express", "PostgreSQL", "HTML", "CSS"],
            "expected_companies": ["Omnicorp"],
            "unsupported_claims": ["Python", "Docker", "Kubernetes", "Ruby on Rails"],
            "expected_metrics": []
        }
    },
    # 7. Product Manager
    {
        "id": "case_07_product_manager",
        "category": "Product Management",
        "resume_text": """PRIYA SHARMA
priya.s@example.com | San Jose, CA
SUMMARY: Technical Product Manager with 5 years leading roadmap delivery for cloud B2B software products.
EXPERIENCE:
Senior Product Manager at CloudSaaS (2021 - Present)
- Led product roadmap for enterprise analytics tool, growing ARR by 30%.
- Authored PRDs and collaborated with engineering teams using Agile and Jira.
Product Manager at AppFlow (2019 - 2021)
- Managed feature launches for customer portal.
SKILLS:
Product: Product Management, Agile, Scrum, Jira, Roadmapping, User Research
EDUCATION:
B.A. in Economics at Stanford University (2015 - 2019)""",
        "ground_truth": {
            "expected_skills": ["Product Management", "Agile", "Scrum", "Jira"],
            "expected_companies": ["CloudSaaS", "AppFlow"],
            "unsupported_claims": ["Python", "Java", "Docker", "Figma"],
            "expected_metrics": ["30%"]
        }
    },
    # 8. QA Automation Engineer
    {
        "id": "case_08_qa_automation",
        "category": "QA / Testing",
        "resume_text": """BRIAN KOWALSKI
brian.k@example.com | Denver, CO
SUMMARY: QA Automation Engineer with 4 years building automated test suites with Python, Selenium, and PyTest.
EXPERIENCE:
QA Automation Engineer at QualityFirst (2020 - Present)
- Engineered end-to-end regression test suite using Python and Selenium.
- Integrated automated tests into CI/CD pipelines with GitHub Actions.
- Reduced manual testing cycle from 3 days to 4 hours.
SKILLS:
Testing: Python, Selenium, PyTest, Automated Testing, GitHub Actions
EDUCATION:
B.S. in Information Systems at Colorado State (2016 - 2020)""",
        "ground_truth": {
            "expected_skills": ["Python", "Selenium", "PyTest", "GitHub Actions"],
            "expected_companies": ["QualityFirst"],
            "unsupported_claims": ["Cypress", "Playwright", "Java", "Docker"],
            "expected_metrics": ["3 days to 4 hours"]
        }
    },
    # 9. Cloud Security Architect
    {
        "id": "case_09_cloud_security",
        "category": "Cybersecurity",
        "resume_text": """TARIQ AL-MANSOUR
tariq.m@example.com | Washington, DC
SUMMARY: Cloud Security Architect designing Zero Trust architecture and IAM governance on AWS.
EXPERIENCE:
Lead Security Architect at SecureCloud (2020 - Present)
- Hardened AWS multi-account infrastructure implementing IAM policies and KMS encryption.
- Automated vulnerability scanning using Python and AWS Security Hub.
SKILLS:
Security: AWS, Cyber Security, Cryptography, Python, Linux
EDUCATION:
M.S. in Cybersecurity at George Mason University (2018 - 2020)""",
        "ground_truth": {
            "expected_skills": ["AWS", "Python", "Linux"],
            "expected_companies": ["SecureCloud"],
            "unsupported_claims": ["Azure", "GCP", "Kubernetes", "Splunk"],
            "expected_metrics": []
        }
    },
    # 10. Mobile Developer (iOS)
    {
        "id": "case_10_ios_dev",
        "category": "Mobile iOS",
        "resume_text": """CHLOE DUBOIS
chloe.d@example.com | Los Angeles, CA
SUMMARY: iOS Developer with 3 years building consumer mobile apps using Swift and SwiftUI.
EXPERIENCE:
iOS Developer at MobileCraft (2021 - Present)
- Developed native iOS applications using Swift and SwiftUI.
- Integrated REST APIs and local data caching with CoreData.
- Maintained 4.8 star App Store rating across 100,000 active users.
SKILLS:
iOS: Swift, SwiftUI, iOS, Git
EDUCATION:
B.S. in Computer Science at UCLA (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["Swift", "iOS", "Git"],
            "expected_companies": ["MobileCraft"],
            "unsupported_claims": ["Kotlin", "React Native", "Flutter", "Android"],
            "expected_metrics": ["100,000"]
        }
    },
    # 11. Mobile Developer (Android)
    {
        "id": "case_11_android_dev",
        "category": "Mobile Android",
        "resume_text": """RAJESH PATEL
rajesh.p@example.com | Atlanta, GA
SUMMARY: Android Developer with 4 years building scalable apps using Kotlin and Jetpack Compose.
EXPERIENCE:
Android Engineer at DroidWorks (2020 - Present)
- Engineered native Android apps with Kotlin and Jetpack Compose.
- Implemented Coroutines for asynchronous network tasks.
SKILLS:
Android: Kotlin, Android, Java, Git
EDUCATION:
B.Tech in Computer Engineering at Georgia Tech (2016 - 2020)""",
        "ground_truth": {
            "expected_skills": ["Kotlin", "Android", "Java", "Git"],
            "expected_companies": ["DroidWorks"],
            "unsupported_claims": ["Swift", "Objective-C", "Flutter", "React Native"],
            "expected_metrics": []
        }
    },
    # 12. Data Engineer
    {
        "id": "case_12_data_engineer",
        "category": "Data Engineering",
        "resume_text": """VICTORIA ADAMS
victoria.a@example.com | Minneapolis, MN
SUMMARY: Data Engineer building high-scale streaming and batch data pipelines using Apache Spark and Python.
EXPERIENCE:
Data Engineer at BigDataFlow (2021 - Present)
- Built distributed ETL pipelines with Apache Spark and Python processing 2TB daily data.
- Modeled data warehousing tables in PostgreSQL and Snowflake.
SKILLS:
Data Eng: Python, Apache Spark, SQL, PostgreSQL, Docker
EDUCATION:
B.S. in Computer Science at University of Minnesota (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["Python", "Apache Spark", "SQL", "PostgreSQL", "Docker"],
            "expected_companies": ["BigDataFlow"],
            "unsupported_claims": ["Flink", "Kafka", "Hadoop", "Scala"],
            "expected_metrics": ["2TB"]
        }
    },
    # 13. Blockchain Developer
    {
        "id": "case_13_blockchain_dev",
        "category": "Web3 / Blockchain",
        "resume_text": """NIKOLAI IVANOV
nikolai.i@example.com | Miami, FL
SUMMARY: Smart Contract Developer writing decentralized protocols with Solidity and JavaScript.
EXPERIENCE:
Blockchain Developer at ChainForge (2022 - Present)
- Developed secure smart contracts using Solidity and Hardhat.
- Built web3 frontend connections using JavaScript and React.
SKILLS:
Web3: Solidity, JavaScript, React, Git
EDUCATION:
B.S. in Software Engineering at Florida State (2018 - 2022)""",
        "ground_truth": {
            "expected_skills": ["Solidity", "JavaScript", "React", "Git"],
            "expected_companies": ["ChainForge"],
            "unsupported_claims": ["Rust", "Solana", "Python", "Go"],
            "expected_metrics": []
        }
    },
    # 14. Fresher / CS Graduate
    {
        "id": "case_14_fresher_cs",
        "category": "Fresher / Student",
        "resume_text": """KEVIN ZHANG
kevin.z@example.com | San Diego, CA
EDUCATION:
B.S. in Computer Science at UC San Diego (2020 - 2024) | GPA: 3.8
PROJECTS:
Cloud File Storage System (2023)
- Implemented file storage API using Python and FastAPI.
- Containerized application with Docker.
Distributed Key-Value Store (2024)
- Built distributed storage protocol using Go.
SKILLS:
Languages: Python, Go, JavaScript, C++
Tools: Docker, Git, Linux""",
        "ground_truth": {
            "expected_skills": ["Python", "FastAPI", "Docker", "Go", "JavaScript", "C++", "Git", "Linux"],
            "expected_companies": ["UC San Diego"],
            "unsupported_claims": ["Kubernetes", "AWS", "Redis", "Kafka"],
            "expected_metrics": ["3.8"]
        }
    },
    # 15. Career Switcher (Teacher -> QA Engineer)
    {
        "id": "case_15_career_switcher_qa",
        "category": "Career Switcher",
        "resume_text": """RACHEL MILLER
rachel.m@example.com | Phoenix, AZ
SUMMARY: Detail-oriented professional transitioning into QA Engineering with practical experience in manual and Python automated testing.
EXPERIENCE:
QA Intern at TechForward (2023 - Present)
- Executed manual and automated regression tests in Python with PyTest.
High School Math Teacher at Phoenix Academy (2018 - 2023)
- Analyzed curriculum outcomes for 150+ students.
SKILLS:
Testing: Python, PyTest, Git
EDUCATION:
B.A. in Mathematics at Arizona State University (2014 - 2018)""",
        "ground_truth": {
            "expected_skills": ["Python", "PyTest", "Git"],
            "expected_companies": ["TechForward", "Phoenix Academy"],
            "unsupported_claims": ["Selenium", "Java", "Docker", "Kubernetes"],
            "expected_metrics": ["150+"]
        }
    },
    # 16. Career Switcher (Accountant -> Data Analyst)
    {
        "id": "case_16_career_switcher_analyst",
        "category": "Career Switcher",
        "resume_text": """SAMANTHA GREEN
samantha.g@example.com | Dallas, TX
SUMMARY: Former Financial Accountant transitioned to Data Analytics, proficient in SQL, PostgreSQL, and Power BI.
EXPERIENCE:
Junior Data Analyst at FinMetrics (2023 - Present)
- Wrote SQL queries in PostgreSQL to analyze monthly revenue trends.
- Built interactive reporting dashboards in Power BI.
Senior Accountant at AuditGroup (2019 - 2023)
- Reconciled ledger accounts and audit reports.
SKILLS:
Analytics: SQL, PostgreSQL, Power BI, Excel
EDUCATION:
B.B.A. in Accounting at SMU (2015 - 2019)""",
        "ground_truth": {
            "expected_skills": ["SQL", "PostgreSQL", "Power BI"],
            "expected_companies": ["FinMetrics", "AuditGroup"],
            "unsupported_claims": ["Python", "Pandas", "Tableau", "AWS"],
            "expected_metrics": []
        }
    },
    # 17. Executive (VP of Engineering)
    {
        "id": "case_17_vp_engineering",
        "category": "Executive",
        "resume_text": """ARTHUR PENDRAGON
arthur.p@example.com | San Francisco, CA
SUMMARY: VP of Engineering with 12+ years scaling engineering organizations from 15 to 120 engineers.
EXPERIENCE:
VP of Engineering at HyperScale Tech (2019 - Present)
- Led 85-person distributed engineering team across backend, platform, and data orgs.
- Reduced cloud infrastructure spend by 25% through strategic AWS architecture optimization.
Director of Engineering at CoreSaaS (2015 - 2019)
- Managed core product delivery and agile processes.
SKILLS:
Leadership: Software Architecture, Agile, Cloud Computing, AWS
EDUCATION:
M.S. in Computer Science at Stanford University (2008 - 2010)""",
        "ground_truth": {
            "expected_skills": ["Software Architecture", "Agile", "AWS"],
            "expected_companies": ["HyperScale Tech", "CoreSaaS"],
            "unsupported_claims": ["Kubernetes", "C++", "Rust", "Golang"],
            "expected_metrics": ["25%", "85-person"]
        }
    },
    # 18. Solutions Architect
    {
        "id": "case_18_solutions_architect",
        "category": "Solutions Architecture",
        "resume_text": """LEO VANDERBILT
leo.v@example.com | Philadelphia, PA
SUMMARY: Enterprise Solutions Architect designing hybrid-cloud architectures on AWS and Docker.
EXPERIENCE:
Principal Solutions Architect at EnterpriseSys (2020 - Present)
- Designed cloud migrations for Fortune 500 financial clients onto AWS.
- Standardized container deployment patterns using Docker.
SKILLS:
Cloud: AWS, Docker, Linux, System Architecture
EDUCATION:
B.S. in Electrical Engineering at Penn State (2012 - 2016)""",
        "ground_truth": {
            "expected_skills": ["AWS", "Docker", "Linux"],
            "expected_companies": ["EnterpriseSys"],
            "unsupported_claims": ["GCP", "Kubernetes", "Python", "Java"],
            "expected_metrics": []
        }
    },
    # 19. Embedded Systems Engineer
    {
        "id": "case_19_embedded_engineer",
        "category": "Embedded / IoT",
        "resume_text": """HIROSHI TANAKA
hiroshi.t@example.com | San Jose, CA
SUMMARY: Embedded Systems Engineer programming microcontrollers and real-time operating systems in C and C++.
EXPERIENCE:
Embedded Firmware Engineer at IoTDevices (2021 - Present)
- Programmed firmware for ARM microcontrollers in C and C++.
- Implemented UART and SPI communication drivers.
SKILLS:
Embedded: C, C++, Embedded Systems, Linux, Git
EDUCATION:
B.S. in Computer Engineering at San Jose State (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["C", "C++", "Linux", "Git"],
            "expected_companies": ["IoTDevices"],
            "unsupported_claims": ["Python", "Java", "Docker", "AWS"],
            "expected_metrics": []
        }
    },
    # 20. UI/UX Designer
    {
        "id": "case_20_ui_ux_designer",
        "category": "UI/UX Design",
        "resume_text": """MAYA LIN
maya.lin@example.com | New York, NY
SUMMARY: Senior Product Designer crafting user-centered mobile and web design systems using Figma.
EXPERIENCE:
Product Designer at DesignForge (2021 - Present)
- Designed design system in Figma adopted across 8 product squads.
- Conducted usability testing sessions improving conversion by 18%.
SKILLS:
Design: Figma, UI/UX Design, Wireframing, HTML, CSS
EDUCATION:
B.F.A. in Graphic Design at RISD (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["Figma", "HTML", "CSS"],
            "expected_companies": ["DesignForge"],
            "unsupported_claims": ["JavaScript", "React", "Python", "Docker"],
            "expected_metrics": ["18%"]
        }
    },
    # 21. Database Administrator
    {
        "id": "case_21_dba",
        "category": "Database Administration",
        "resume_text": """CARLOS MENDEZ
carlos.m@example.com | Houston, TX
SUMMARY: Database Administrator with 7 years administering high-availability PostgreSQL and MySQL clusters.
EXPERIENCE:
Lead DBA at DataVault (2019 - Present)
- Managed 50+ PostgreSQL database instances with streaming replication and automated failover.
- Optimized query execution plans reducing CPU utilization by 30%.
SKILLS:
Database: PostgreSQL, MySQL, SQL, Linux, Bash
EDUCATION:
B.S. in Management Information Systems at University of Houston (2013 - 2017)""",
        "ground_truth": {
            "expected_skills": ["PostgreSQL", "MySQL", "SQL", "Linux", "Bash"],
            "expected_companies": ["DataVault"],
            "unsupported_claims": ["Oracle", "MongoDB", "Python", "Kubernetes"],
            "expected_metrics": ["30%", "50+"]
        }
    },
    # 22. AI Research Scientist
    {
        "id": "case_22_ai_researcher",
        "category": "AI Research",
        "resume_text": """DR. ANNA WEISS
anna.weiss@example.com | Cambridge, MA
SUMMARY: AI Researcher focusing on natural language processing, LLM architectures, and transformer optimization.
EXPERIENCE:
Research Scientist at NeuralLab (2022 - Present)
- Published novel transformer attention mechanism using PyTorch.
- Trained multi-billion parameter language models on GPU clusters.
SKILLS:
AI & Research: Python, PyTorch, Transformers, Deep Learning, Linux
EDUCATION:
Ph.D. in Computer Science at MIT (2018 - 2022)""",
        "ground_truth": {
            "expected_skills": ["Python", "PyTorch", "Deep Learning", "Linux"],
            "expected_companies": ["NeuralLab", "MIT"],
            "unsupported_claims": ["FastAPI", "React", "Docker", "Java"],
            "expected_metrics": []
        }
    },
    # 23. Kubernetes Specialist SRE
    {
        "id": "case_23_k8s_sre",
        "category": "Infrastructure / SRE",
        "resume_text": """DMITRI VOLKOV
dmitri.v@example.com | Chicago, IL
SUMMARY: Infrastructure Engineer specializing in Kubernetes operators, service mesh, and Prometheus observability.
EXPERIENCE:
SRE at CloudWorks (2021 - Present)
- Managed Kubernetes clusters running 200+ containerized microservices.
- Deployed Prometheus and Grafana for cluster monitoring.
SKILLS:
Infra: Kubernetes, Docker, Prometheus, Grafana, Linux, Go
EDUCATION:
B.S. in Computer Science at Purdue (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["Kubernetes", "Docker", "Linux", "Go"],
            "expected_companies": ["CloudWorks"],
            "unsupported_claims": ["Python", "AWS", "Terraform", "Java"],
            "expected_metrics": ["200+"]
        }
    },
    # 24. Junior Python Developer
    {
        "id": "case_24_jr_python",
        "category": "Junior Python",
        "resume_text": """LUCAS SILVA
lucas.s@example.com | Miami, FL
SUMMARY: Junior Python Developer building web scrapers and automation scripts with Python and PostgreSQL.
EXPERIENCE:
Junior Python Developer at AutoWeb (2023 - Present)
- Developed automated data collection scripts in Python.
- Stored structured data in PostgreSQL.
SKILLS:
Languages: Python, SQL, PostgreSQL, Git
EDUCATION:
B.S. in Computer Science at FIU (2019 - 2023)""",
        "ground_truth": {
            "expected_skills": ["Python", "SQL", "PostgreSQL", "Git"],
            "expected_companies": ["AutoWeb"],
            "unsupported_claims": ["FastAPI", "Django", "Docker", "Kubernetes"],
            "expected_metrics": []
        }
    },
    # 25. Technical Writer
    {
        "id": "case_25_tech_writer",
        "category": "Developer Relations",
        "resume_text": """OLIVIA BENNETT
olivia.b@example.com | Portland, OR
SUMMARY: Technical Writer creating clear API documentation, developer guides, and markdown tutorials.
EXPERIENCE:
Senior Technical Writer at DevDocs Inc (2021 - Present)
- Authored REST API documentation and onboarding guides using Markdown.
- Collaborated with engineering teams to document Python SDKs.
SKILLS:
Docs: Technical Writing, Markdown, Git, Python
EDUCATION:
B.A. in English at University of Oregon (2016 - 2020)""",
        "ground_truth": {
            "expected_skills": ["Technical Writing", "Git", "Python"],
            "expected_companies": ["DevDocs Inc"],
            "unsupported_claims": ["FastAPI", "Docker", "Kubernetes", "React"],
            "expected_metrics": []
        }
    },
    # 26. Cybersecurity Analyst
    {
        "id": "case_26_cybersecurity",
        "category": "Security Analyst",
        "resume_text": """GABRIEL NGUYEN
gabriel.n@example.com | Washington, DC
SUMMARY: SOC Analyst monitoring threat telemetry, vulnerability triaging, and incident response on Linux networks.
EXPERIENCE:
Security Analyst at CyberShield (2022 - Present)
- Monitored network security logs and triaged incident alerts.
- Automated security analysis scripts in Python and Bash.
SKILLS:
Security: Cyber Security, Linux, Bash, Python, Network Security
EDUCATION:
B.S. in Cybersecurity at University of Maryland (2018 - 2022)""",
        "ground_truth": {
            "expected_skills": ["Linux", "Bash", "Python"],
            "expected_companies": ["CyberShield"],
            "unsupported_claims": ["AWS", "Docker", "Java", "Kubernetes"],
            "expected_metrics": []
        }
    },
    # 27. Enterprise Java Architect
    {
        "id": "case_27_enterprise_java",
        "category": "Java Architecture",
        "resume_text": """THOMAS SCHMIDT
thomas.s@example.com | Milwaukee, WI
SUMMARY: Principal Java Architect with 10 years designing high-throughput banking systems with Spring Boot.
EXPERIENCE:
Principal Java Engineer at BankPlatform (2018 - Present)
- Engineered financial processing engines using Java, Spring Boot, and PostgreSQL.
- Handled transactions exceeding $50M daily.
SKILLS:
Java Stack: Java, Spring Boot, PostgreSQL, Docker, Maven
EDUCATION:
B.S. in Computer Science at Marquette University (2010 - 2014)""",
        "ground_truth": {
            "expected_skills": ["Java", "Spring Boot", "PostgreSQL", "Docker"],
            "expected_companies": ["BankPlatform"],
            "unsupported_claims": ["Python", "FastAPI", "Ruby", "Golang"],
            "expected_metrics": ["$50M"]
        }
    },
    # 28. Next.js / React Specialist
    {
        "id": "case_28_nextjs_specialist",
        "category": "Modern Web",
        "resume_text": """ALEXA REYES
alexa.r@example.com | San Francisco, CA
SUMMARY: Frontend Engineer specializing in Next.js, Server Components, and TypeScript.
EXPERIENCE:
Frontend Engineer at WebScale App (2022 - Present)
- Built e-commerce web platform using Next.js, React, and TypeScript.
- Improved Core Web Vitals resulting in 35% faster page load times.
SKILLS:
Frontend: Next.js, React, TypeScript, Tailwind CSS, JavaScript
EDUCATION:
B.S. in Computer Science at UC Davis (2018 - 2022)""",
        "ground_truth": {
            "expected_skills": ["React", "TypeScript", "Tailwind CSS", "JavaScript"],
            "expected_companies": ["WebScale App"],
            "unsupported_claims": ["Python", "Docker", "Kubernetes", "Angular"],
            "expected_metrics": ["35%"]
        }
    },
    # 29. Bootcamper / Career Pivot
    {
        "id": "case_29_bootcamper",
        "category": "Bootcamper",
        "resume_text": """JORDAN BLACK
jordan.b@example.com | Atlanta, GA
SUMMARY: Full Stack Web Developer trained in modern JavaScript, React, Node.js, and MongoDB.
PROJECTS:
Recipe Sharing Web App (2023)
- Built interactive single-page app with React and Node.js.
- Deployed frontend to cloud hosting.
SKILLS:
Languages & Tools: JavaScript, React, Node.js, HTML, CSS, Git
EDUCATION:
Software Engineering Certificate at Flatiron School (2023)
B.A. in Communications at Georgia State (2017 - 2021)""",
        "ground_truth": {
            "expected_skills": ["JavaScript", "React", "Node.js", "HTML", "CSS", "Git"],
            "expected_companies": ["Flatiron School"],
            "unsupported_claims": ["Python", "Docker", "AWS", "Kubernetes"],
            "expected_metrics": []
        }
    },
    # 30. Senior Engineering Manager
    {
        "id": "case_30_eng_manager",
        "category": "Management",
        "resume_text": """DANIEL THORNE
daniel.t@example.com | Seattle, WA
SUMMARY: Engineering Manager with 8+ years leading cross-functional engineering teams in SaaS.
EXPERIENCE:
Engineering Manager at CloudSaaS (2020 - Present)
- Managed 14 software engineers delivering platform infrastructure.
- Mentored 4 engineers to senior promotions.
Lead Developer at WebCorp (2016 - 2020)
- Architected web services using Python and PostgreSQL.
SKILLS:
Leadership & Tech: Engineering Management, Agile, Python, PostgreSQL, System Design
EDUCATION:
B.S. in Computer Science at University of Washington (2012 - 2016)""",
        "ground_truth": {
            "expected_skills": ["Agile", "Python", "PostgreSQL"],
            "expected_companies": ["CloudSaaS", "WebCorp"],
            "unsupported_claims": ["C++", "Java", "Kubernetes", "Rust"],
            "expected_metrics": ["14 software engineers"]
        }
    }
]

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "tests", "evaluation", "eval_dataset_v2.json"))
with open(out_path, "w") as f:
    json.dump(cases, f, indent=2)

print(f"Successfully generated {len(cases)} benchmark test cases at {out_path}!")
