#!/usr/bin/env python3
"""
Extract LLM Agents Papers - Top Papers sobre Autonomía (LLM Agents) 2024-2025
==============================================================================

Extrae información de los papers top sobre agentes LLM autónomos.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class LLMAgentPaper:
    """Información de un paper sobre agentes LLM."""
    title: str
    authors: List[str]
    year: int
    venue: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    key_contributions: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    architecture: Optional[str] = None
    category: str = "agents"  # agents, autonomous_driving, survey


# Papers sobre Autonomía (LLM Agents) - 2024-2025
LLM_AGENTS_PAPERS = [
    {
        "title": "SimuRA: Towards General Goal-Oriented Agent via Simulative Reasoning Architecture with LLM-Based World Model",
        "authors": ["Deng", "Hou", "Shen", "Jin", "Neubig", "Hu", "Xing"],
        "year": 2025,
        "venue": "arXiv",
        "description": "Proponen un 'world-model' basado en LLM para hacer simulaciones mental-lingüísticas, planear acciones y razonar como agente general.",
        "key_contributions": [
            "World-model basado en LLM",
            "Simulaciones mental-lingüísticas",
            "Planificación de acciones",
            "Razonamiento como agente general"
        ],
        "techniques": [
            "Simulative Reasoning Architecture",
            "LLM-Based World Model",
            "Goal-Oriented Planning"
        ],
        "architecture": "Simulative Reasoning Architecture con World Model",
        "category": "agents"
    },
    {
        "title": "A Concurrent Modular Agent: Framework for Autonomous LLM Agents",
        "authors": ["Maruyama", "Yoshida", "Sato", "Masumori", "Ikegami"],
        "year": 2025,
        "venue": "arXiv",
        "description": "Presentan una arquitectura de agente con módulos concurrentes que operan de forma autónoma, comunicación entre módulos y un 'estado global' compartido.",
        "key_contributions": [
            "Arquitectura modular concurrente",
            "Módulos autónomos",
            "Comunicación entre módulos",
            "Estado global compartido"
        ],
        "techniques": [
            "Concurrent Modular Architecture",
            "Inter-module Communication",
            "Shared Global State"
        ],
        "architecture": "Concurrent Modular Agent Framework",
        "category": "agents"
    },
    {
        "title": "Formal-LLM: Integrating Formal Language and Natural Language for Controllable LLM-based Agents",
        "authors": ["Li", "Hua", "Wang", "Zhu", "Zhang"],
        "year": 2024,
        "venue": "arXiv",
        "description": "Integran lenguaje formal con natural para guiar a agentes LLM en generar planes válidos, evitando planes inválidos a través de un autómata formal.",
        "key_contributions": [
            "Integración de lenguaje formal y natural",
            "Generación de planes válidos",
            "Prevención de planes inválidos",
            "Autómata formal para control"
        ],
        "techniques": [
            "Formal Language Integration",
            "Formal Automata",
            "Plan Validation",
            "Controllable Agent Generation"
        ],
        "architecture": "Formal-LLM con autómata formal",
        "category": "agents"
    },
    {
        "title": "EMPOWERING AUTONOMOUS DRIVING WITH LARGE LANGUAGE MODELS: A SAFETY PERSPECTIVE",
        "authors": ["Wang", "Jiao", "Zhan", "Lang", "Huang", "Wang", "Yang", "Zhu"],
        "year": 2024,
        "venue": "ICLR Workshop",
        "url": "OpenReview",
        "description": "Usan LLMs para planificación en conducción autónoma y proponen un 'verificador de seguridad' para planes generados por el agente, mejorando comportamientos en escenarios complejos.",
        "key_contributions": [
            "Planificación con LLMs en conducción autónoma",
            "Verificador de seguridad para planes",
            "Mejora de comportamientos en escenarios complejos",
            "Perspectiva de seguridad"
        ],
        "techniques": [
            "Safety Verification",
            "Autonomous Driving Planning",
            "Complex Scenario Handling"
        ],
        "architecture": "LLM-based Planning con Safety Verifier",
        "category": "autonomous_driving"
    },
    {
        "title": "MARS: Memory-Enhanced Agents with Reflective Self-improvement",
        "authors": ["Liang", "Tao", "Xia", "Wang", "Li", "Wang", "Yang", "Shi", "Wang", "Zhang"],
        "year": 2025,
        "venue": "LXL Sword",
        "description": "Proponen un agente con tres componentes: usuario, asistente y verificador ('checker'), usando memoria optimizada y reflexión para mejorar con el tiempo.",
        "key_contributions": [
            "Arquitectura de tres componentes (usuario, asistente, verificador)",
            "Memoria optimizada",
            "Reflexión para auto-mejora",
            "Mejora continua con el tiempo"
        ],
        "techniques": [
            "Memory Enhancement",
            "Reflective Self-improvement",
            "Three-component Architecture",
            "Optimized Memory"
        ],
        "architecture": "MARS: Usuario + Asistente + Verificador con memoria",
        "category": "agents"
    },
    {
        "title": "DriveAgent: LLM-Driven Multi-Agent Autonomous Driving",
        "authors": ["Hou", "Wang", "Yang", "Lin", "Feng", "Min", "Zhao"],
        "year": 2025,
        "venue": "LXL Sword",
        "description": "Un framework de agente modular para conducción autónoma: sensores (cámaras, LiDAR, GPS) + agentes de razonamiento + agente decisor para maniobras urgentes.",
        "key_contributions": [
            "Framework modular multi-agente",
            "Integración de sensores (cámaras, LiDAR, GPS)",
            "Agentes de razonamiento",
            "Agente decisor para maniobras urgentes"
        ],
        "techniques": [
            "Multi-Agent Architecture",
            "Sensor Integration",
            "Reasoning Agents",
            "Urgent Maneuver Decision Making"
        ],
        "architecture": "Modular Multi-Agent: Sensores + Razonamiento + Decisor",
        "category": "autonomous_driving"
    },
    {
        "title": "A Survey on Large Language Model Based Autonomous Agents",
        "authors": ["Tang", "Chen", "Yue", "Fan", "Zhou", "Li", "Zhang", "Zhao"],
        "year": 2024,
        "venue": "SpringerLink",
        "description": "Revisión sistemática del estado de agentes LLMs: memoria, planificación, uso de herramientas, evaluación y desafíos.",
        "key_contributions": [
            "Revisión sistemática de agentes LLM",
            "Análisis de memoria",
            "Análisis de planificación",
            "Uso de herramientas",
            "Evaluación y desafíos"
        ],
        "techniques": [
            "Systematic Review",
            "Memory Analysis",
            "Planning Analysis",
            "Tool Usage",
            "Evaluation Methods"
        ],
        "architecture": "Survey Paper",
        "category": "survey"
    },
    {
        "title": "A Survey on Large Language Model-Powered Autonomous Driving",
        "authors": [],
        "year": 2025,
        "venue": "sciencedirect.com",
        "description": "Estudio que revisa cómo se están usando LLMs en vehículos autónomos para mejorar el razonamiento, la toma de decisiones y la interpretación del entorno.",
        "key_contributions": [
            "Revisión de LLMs en vehículos autónomos",
            "Mejora del razonamiento",
            "Toma de decisiones",
            "Interpretación del entorno"
        ],
        "techniques": [
            "Survey on Autonomous Driving",
            "Reasoning Enhancement",
            "Decision Making",
            "Environment Interpretation"
        ],
        "architecture": "Survey Paper",
        "category": "survey"
    }
]


def extract_arxiv_id_from_title(title: str) -> Optional[str]:
    """Intenta extraer un arxiv_id del título o generar uno basado en el título."""
    # Para papers de arXiv, normalmente no tenemos el ID en el título
    # Esto sería útil si tuviéramos URLs completas
    return None


def create_paper_objects() -> List[LLMAgentPaper]:
    """Crea objetos Paper a partir de los datos."""
    papers = []
    for paper_data in LLM_AGENTS_PAPERS:
        paper = LLMAgentPaper(
            title=paper_data["title"],
            authors=paper_data["authors"],
            year=paper_data["year"],
            venue=paper_data.get("venue"),
            arxiv_id=paper_data.get("arxiv_id"),
            url=paper_data.get("url"),
            description=paper_data["description"],
            key_contributions=paper_data.get("key_contributions", []),
            techniques=paper_data.get("techniques", []),
            architecture=paper_data.get("architecture"),
            category=paper_data.get("category", "agents")
        )
        papers.append(paper)
    return papers


def generate_paper_id(title: str) -> str:
    """Genera un ID único para el paper basado en el título."""
    # Convertir título a slug
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    # Limitar longitud
    if len(slug) > 50:
        slug = slug[:50]
    return slug


def export_to_json(papers: List[LLMAgentPaper], output_file: Path):
    """Exporta los papers a JSON."""
    papers_dict = []
    for paper in papers:
        paper_dict = asdict(paper)
        paper_dict["paper_id"] = generate_paper_id(paper.title)
        papers_dict.append(paper_dict)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Exported {len(papers)} papers to {output_file}")


def generate_markdown_report(papers: List[LLMAgentPaper], output_file: Path):
    """Genera un reporte en Markdown."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Top Papers sobre Autonomía (LLM Agents) — 2024-2025\n\n")
        f.write(f"**Fecha de extracción**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total de papers**: {len(papers)}\n\n")
        f.write("---\n\n")
        
        # Agrupar por categoría
        categories = {}
        for paper in papers:
            if paper.category not in categories:
                categories[paper.category] = []
            categories[paper.category].append(paper)
        
        for category, category_papers in categories.items():
            f.write(f"## {category.upper().replace('_', ' ')}\n\n")
            
            for i, paper in enumerate(category_papers, 1):
                f.write(f"### {i}. {paper.title}\n\n")
                f.write(f"**Autores**: {', '.join(paper.authors)}\n\n")
                f.write(f"**Año**: {paper.year}\n\n")
                if paper.venue:
                    f.write(f"**Venue**: {paper.venue}\n\n")
                if paper.url:
                    f.write(f"**URL**: {paper.url}\n\n")
                
                f.write(f"**Descripción**: {paper.description}\n\n")
                
                if paper.key_contributions:
                    f.write("**Contribuciones Clave**:\n")
                    for contrib in paper.key_contributions:
                        f.write(f"- {contrib}\n")
                    f.write("\n")
                
                if paper.techniques:
                    f.write("**Técnicas**:\n")
                    for technique in paper.techniques:
                        f.write(f"- {technique}\n")
                    f.write("\n")
                
                if paper.architecture:
                    f.write(f"**Arquitectura**: {paper.architecture}\n\n")
                
                f.write("---\n\n")
    
    logger.info(f"✅ Generated Markdown report: {output_file}")


def generate_summary(papers: List[LLMAgentPaper]) -> Dict:
    """Genera un resumen estadístico."""
    summary = {
        "total_papers": len(papers),
        "by_year": {},
        "by_category": {},
        "by_venue": {},
        "total_authors": set(),
        "techniques_count": {}
    }
    
    for paper in papers:
        # Por año
        summary["by_year"][paper.year] = summary["by_year"].get(paper.year, 0) + 1
        
        # Por categoría
        summary["by_category"][paper.category] = summary["by_category"].get(paper.category, 0) + 1
        
        # Por venue
        if paper.venue:
            summary["by_venue"][paper.venue] = summary["by_venue"].get(paper.venue, 0) + 1
        
        # Autores únicos
        summary["total_authors"].update(paper.authors)
        
        # Técnicas
        for technique in paper.techniques:
            summary["techniques_count"][technique] = summary["techniques_count"].get(technique, 0) + 1
    
    summary["total_authors"] = len(summary["total_authors"])
    summary["unique_techniques"] = len(summary["techniques_count"])
    
    return summary


def main():
    """Función principal."""
    logger.info("🚀 Starting LLM Agents Papers extraction...")
    
    # Crear objetos Paper
    papers = create_paper_objects()
    logger.info(f"📚 Created {len(papers)} paper objects")
    
    # Directorio de salida
    output_dir = Path(__file__).parent / "llm_agents_papers"
    output_dir.mkdir(exist_ok=True)
    
    # Exportar JSON
    json_file = output_dir / "llm_agents_papers.json"
    export_to_json(papers, json_file)
    
    # Generar reporte Markdown
    md_file = output_dir / "LLM_AGENTS_PAPERS.md"
    generate_markdown_report(papers, md_file)
    
    # Generar resumen
    summary = generate_summary(papers)
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info("📊 Summary:")
    logger.info(f"  - Total papers: {summary['total_papers']}")
    logger.info(f"  - By year: {summary['by_year']}")
    logger.info(f"  - By category: {summary['by_category']}")
    logger.info(f"  - Total unique authors: {summary['total_authors']}")
    logger.info(f"  - Unique techniques: {summary['unique_techniques']}")
    
    logger.info("✅ Extraction complete!")
    logger.info(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    main()



