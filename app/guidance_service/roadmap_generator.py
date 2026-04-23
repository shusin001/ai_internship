"""Rule-based learning roadmap generation for missing skills."""

from typing import Dict, List

from app.guidance_service.utils import unique_preserve_order

ROADMAP_MAP: Dict[str, Dict[str, List[str]]] = {
    "react": {
        "phase_1": ["Strengthen JavaScript fundamentals (ES6+, async, modules)"],
        "phase_2": ["Learn React core concepts: components, props, state, hooks"],
        "phase_3": ["Master routing, state management, and API integration in React"],
        "phase_4": ["Build and deploy 2 React projects with reusable components"],
    },
    "fastapi": {
        "phase_1": ["Review Python typing, async/await, and HTTP fundamentals"],
        "phase_2": ["Build REST APIs with FastAPI routers, validation, and docs"],
        "phase_3": ["Add auth, database integration, and error handling patterns"],
        "phase_4": ["Ship a production-style backend project with tests"],
    },
    "docker": {
        "phase_1": ["Understand containers, images, and Docker basics"],
        "phase_2": ["Write Dockerfiles and docker-compose for local stacks"],
        "phase_3": ["Optimize images, networking, and volume strategies"],
        "phase_4": ["Containerize and run end-to-end full-stack demo projects"],
    },
    "aws": {
        "phase_1": ["Learn core cloud concepts and AWS global infrastructure"],
        "phase_2": ["Use EC2, S3, IAM, and VPC for secure deployments"],
        "phase_3": ["Design scalable architectures with managed services"],
        "phase_4": ["Deploy and monitor a cloud-hosted application"],
    },
    "mongodb": {
        "phase_1": ["Learn NoSQL fundamentals and document modeling"],
        "phase_2": ["Practice CRUD, indexing, and aggregation pipelines"],
        "phase_3": ["Improve schema design, query performance, and replication"],
        "phase_4": ["Build data-driven APIs using MongoDB in real projects"],
    },
}


def _generic_skill_roadmap(skill: str) -> Dict[str, List[str]]:
    skill_title = skill.strip().title()
    return {
        "phase_1": ["Learn {} fundamentals from official documentation".format(skill_title)],
        "phase_2": ["Practice {} with guided tutorials and mini exercises".format(skill_title)],
        "phase_3": ["Apply {} in realistic intermediate tasks".format(skill_title)],
        "phase_4": ["Build and publish one portfolio project using {}".format(skill_title)],
    }


def generate_learning_roadmap(missing_skills: List[str]) -> Dict[str, List[str]]:
    """Create multi-phase roadmap by merging per-skill rule-based plans."""
    roadmap = {
        "phase_1": [],
        "phase_2": [],
        "phase_3": [],
        "phase_4": [],
        "phase_5": [],
    }

    for skill in missing_skills:
        key = skill.lower().strip()
        skill_plan = ROADMAP_MAP.get(key, _generic_skill_roadmap(skill))
        roadmap["phase_1"].extend(skill_plan.get("phase_1", []))
        roadmap["phase_2"].extend(skill_plan.get("phase_2", []))
        roadmap["phase_3"].extend(skill_plan.get("phase_3", []))
        roadmap["phase_4"].extend(skill_plan.get("phase_4", []))

    roadmap["phase_5"] = [
        "Prepare STAR-based project stories and resume-ready impact bullets",
        "Practice role-specific interview questions and mock interviews",
        "Revise fundamentals and complete one timed assessment per week",
    ]

    for phase_name in roadmap:
        roadmap[phase_name] = unique_preserve_order(roadmap[phase_name])

    return roadmap
