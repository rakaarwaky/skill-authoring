"""Skills-design shared kernel — maintenance layer.

Shared mutation utilities: skill-dir resolution, category-name validation,
containment assertions, atomic writes, lifecycle support, and mutation plan
generators.
"""
from shared.src.maintenance.contract_maintenance_aggregate import (
    ISkillsMaintenanceAggregate,
    ISkillsPrunerProtocol,
    ISkillsPurgerProtocol,
)
from shared.src.maintenance.taxonomy_maintenance_constant import (
    MAINTENANCE_LOCK_FILENAME,
    MAINTENANCE_SIDECAR_FILENAME,
    PRUNE_TTL_DEFAULT_DAYS,
    PURGE_TTL_DEFAULT_DAYS,
)
from shared.src.maintenance.taxonomy_maintenance_entity import (
    MaintenanceRecord,
    PruneCandidate,
)
from shared.src.maintenance.taxonomy_maintenance_error import (
    MaintenanceError,
    PruneEmptyError,
    PurgeEmptyError,
    SkillNotArchivedError,
)
from shared.src.maintenance.taxonomy_maintenance_request import (
    MaintenanceRequest,
    MaintenanceVerb,
    SkillsRoot,
)
from shared.src.maintenance.taxonomy_maintenance_response import (
    MaintenanceResponse,
)
from shared.src.maintenance.taxonomy_maintenance_vo import MaintenanceOpId
from shared.src.maintenance.utility_lifecycle_support import (
    ACTIVE,
    ARCHIVED,
    STALE,
    archive_skill,
    restore_skill,
)
from shared.src.maintenance.utility_maintenance_core import (
    default_prune_ttl_days,
    default_purge_ttl_days,
    maintenance_lock_path,
    maintenance_sidecar_path,
)
from shared.src.maintenance.utility_skills_mutation import (
    plan_repair,
    plan_weed,
)

__all__ = [
    "ACTIVE",
    "ARCHIVED",
    "MAINTENANCE_LOCK_FILENAME",
    "MAINTENANCE_SIDECAR_FILENAME",
    "PRUNE_TTL_DEFAULT_DAYS",
    "PURGE_TTL_DEFAULT_DAYS",
    "STALE",
    "ISkillsMaintenanceAggregate",
    "ISkillsPrunerProtocol",
    "ISkillsPurgerProtocol",
    "MaintenanceError",
    "MaintenanceOpId",
    "MaintenanceRecord",
    "MaintenanceRequest",
    "MaintenanceResponse",
    "MaintenanceVerb",
    "PruneCandidate",
    "PruneEmptyError",
    "PurgeEmptyError",
    "SkillNotArchivedError",
    "SkillsRoot",
    "archive_skill",
    "default_prune_ttl_days",
    "default_purge_ttl_days",
    "maintenance_lock_path",
    "maintenance_sidecar_path",
    "plan_repair",
    "plan_weed",
    "restore_skill",
]

_layer_symbols = {
    "ACTIVE": ACTIVE,
    "ARCHIVED": ARCHIVED,
    "MaintenanceError": MaintenanceError,
    "MaintenanceOpId": MaintenanceOpId,
    "MaintenanceRecord": MaintenanceRecord,
    "MaintenanceRequest": MaintenanceRequest,
    "MaintenanceResponse": MaintenanceResponse,
    "MaintenanceVerb": MaintenanceVerb,
    "MAINTENANCE_LOCK_FILENAME": MAINTENANCE_LOCK_FILENAME,
    "MAINTENANCE_SIDECAR_FILENAME": MAINTENANCE_SIDECAR_FILENAME,
    "PRUNE_TTL_DEFAULT_DAYS": PRUNE_TTL_DEFAULT_DAYS,
    "PURGE_TTL_DEFAULT_DAYS": PURGE_TTL_DEFAULT_DAYS,
    "PruneCandidate": PruneCandidate,
    "PruneEmptyError": PruneEmptyError,
    "PurgeEmptyError": PurgeEmptyError,
    "STALE": STALE,
    "SkillNotArchivedError": SkillNotArchivedError,
    "SkillsRoot": SkillsRoot,
    "archive_skill": archive_skill,
    "default_purge_ttl_days": default_purge_ttl_days,
    "default_prune_ttl_days": default_prune_ttl_days,
    "maintenance_lock_path": maintenance_lock_path,
    "maintenance_sidecar_path": maintenance_sidecar_path,
    "plan_repair": plan_repair,
    "plan_weed": plan_weed,
    "restore_skill": restore_skill,
    "ISkillsMaintenanceAggregate": ISkillsMaintenanceAggregate,
    "ISkillsPurgerProtocol": ISkillsPurgerProtocol,
    "ISkillsPrunerProtocol": ISkillsPrunerProtocol,
}
