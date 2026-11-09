"""Maintenance surface layer (AES surface layer).

Re-exports the maintenance agent and its capabilities so the package
surface and the command modules share one implementation — no
duplication between the barrel and the modules.
"""

from .src.agent_maintenance_orchestrator import SkillsMaintenanceAgent
from .src.capabilities_skills_prune import SkillsPrune
from .src.capabilities_skills_purge import SkillsPurge

__all__ = ["SkillsMaintenanceAgent", "SkillsPrune", "SkillsPurge"]

_layer_symbols = {
    "SkillsMaintenanceAgent": SkillsMaintenanceAgent,
    "SkillsPrune": SkillsPrune,
    "SkillsPurge": SkillsPurge,
}
