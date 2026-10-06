from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.matching import Match, SkillGap
from app.schemas.career import RoadmapMilestone, SkillLearningPath, CareerRoadmapResponse
from app.services.ontology.taxonomy import ontology

class CareerRoadmapService:
    @classmethod
    def generate_roadmap(cls, db: Session, match: Match) -> CareerRoadmapResponse:
        gaps = db.query(SkillGap).filter(SkillGap.match_id == match.id).all()
        target_role = match.job.title
        
        learning_paths: List[SkillLearningPath] = []
        total_weeks = 0

        # Prioritize gaps: critical first, then representation, then moderate
        sorted_gaps = sorted(
            gaps,
            key=lambda g: 0 if g.gap_severity == "critical" else (1 if g.gap_severity == "representation" else 2)
        )

        for gap in sorted_gaps[:4]:
            skill_name = gap.skill_name
            node = ontology.get_node(skill_name)
            
            # Determine transferable base if any
            transfer_base = None
            for cand_sk in match.resume.skills:
                c_node = ontology.get_node(cand_sk.normalized_skill)
                if c_node and (skill_name in c_node.related or skill_name in c_node.transferable_to):
                    transfer_base = cand_sk.normalized_skill
                    break

            # Create specific structured milestones
            if gap.gap_severity == "representation":
                milestones = [
                    RoadmapMilestone(
                        step_number=1,
                        title=f"Identify Historical {skill_name} Usage",
                        description=f"Review prior code repositories and notes where you utilized {skill_name}.",
                        estimated_weeks=1,
                        learning_resources=["Internal project records", "Commit histories"],
                        hands_on_project_to_prove="Extract quantitative delivery metrics (latency, requests, lines of code, users).",
                        evidence_to_add_to_resume=f"Revised bullet point: 'Utilized {skill_name} to optimize production workflows.'"
                    ),
                    RoadmapMilestone(
                        step_number=2,
                        title=f"Deploy Production-Style Sandbox",
                        description=f"Build and test an end-to-end integration demo highlighting {skill_name}.",
                        estimated_weeks=1,
                        learning_resources=[f"Official {skill_name} Documentation"],
                        hands_on_project_to_prove="Publish open-source repo with README architecture diagram and CI pipeline.",
                        evidence_to_add_to_resume=f"Added GitHub project link with {skill_name} benchmarks to portfolio."
                    )
                ]
                hours = 15
                priority = "immediate"
            else:
                milestones = [
                    RoadmapMilestone(
                        step_number=1,
                        title=f"{skill_name} Architecture & Fundamentals",
                        description=f"Master core concepts, primitives, and standard design patterns in {skill_name}.",
                        estimated_weeks=2,
                        learning_resources=[f"Official {skill_name} Guide", "System Architecture Reference"],
                        hands_on_project_to_prove="Complete baseline CLI or API implementing primary workflows.",
                        evidence_to_add_to_resume="Foundation established."
                    ),
                    RoadmapMilestone(
                        step_number=2,
                        title=f"Advanced {skill_name} Integration",
                        description="Implement production features: error handling, concurrency, caching, and persistence.",
                        estimated_weeks=2,
                        learning_resources=["Best Practices & Scalability Guides"],
                        hands_on_project_to_prove=f"Deploy an enterprise-grade service integrating {skill_name} with automated test suite.",
                        evidence_to_add_to_resume="Full pipeline delivery."
                    ),
                    RoadmapMilestone(
                        step_number=3,
                        title="Verifiable Portfolio Project & Resume Update",
                        description="Benchmark performance, document quantitative results, and update resume.",
                        estimated_weeks=1,
                        learning_resources=["Google XYZ Resume Formula"],
                        hands_on_project_to_prove="Live hosted URL and reproducible repository.",
                        evidence_to_add_to_resume=f"Engineered and deployed service with {skill_name}, achieving sub-50ms latency."
                    )
                ]
                hours = 45
                priority = "high" if gap.gap_severity == "critical" else "medium"

            path_weeks = sum(m.estimated_weeks for m in milestones)
            total_weeks += path_weeks

            learning_paths.append(SkillLearningPath(
                skill_name=skill_name,
                priority_level=priority,
                job_market_demand="high",
                effort_estimate_hours=hours,
                transferable_base=transfer_base,
                milestones=milestones
            ))

        return CareerRoadmapResponse(
            match_id=match.id,
            target_role=target_role,
            current_seniority_level=match.resume.parsed_data.get("seniority_level", "Mid-Level"),
            target_seniority_level=match.job.seniority.title(),
            summary_strategy=(
                f"Prioritized roadmap designed to close {len(learning_paths)} critical requirements "
                f"and boost compatibility toward {target_role}. Every milestone concludes with verifiable evidence."
            ),
            learning_paths=learning_paths,
            estimated_total_weeks=max(total_weeks, 2)
        )

career_roadmap_service = CareerRoadmapService()
