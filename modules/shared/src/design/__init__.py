"""Skills-design shared kernel — design layer.

SSOT for validation budgets, naming rules, layout invariants, domain
entities, value objects, request/response envelopes, and the aggregate
dispatch contract.
"""
from shared.src.common.taxonomy_common_constant import (
    ARCHIVE_DIRNAME,
    BM25F_SCORE_SCALE,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.common.taxonomy_common_vo import (
    BM25FHit,
    CatalogCheckResult,
    CatalogReport,
    CategoryName,
    DiscoveryMatch,
    DiscoveryResult,
    MutationOutcome,
    MutationPlan,
    MutationStep,
    SkillContent,
    SkillDescription,
    SkillName,
    SkillRecord,
    SkillsJsonPayload,
)
from shared.src.design.contract_design_aggregate import ISkillsAggregate
from shared.src.design.contract_design_protocol import (
    ISkillsAdopterProtocol,
    ISkillsCreatorProtocol,
    ISkillsLinterProtocol,
    ISkillsRunnerProtocol,
)
from shared.src.design.taxonomy_design_entity import (
    Issue,
)
from shared.src.design.taxonomy_design_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_design_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.design.taxonomy_design_vo import (
    LintReport,
    NewCategoryPlan,
    SkillCreatePlan,
    TelemetryRow,
    ValidationReport,
)

__all__ = [
    "ARCHIVE_DIRNAME",
    "BM25F_SCORE_SCALE",
    "CATEGORY_DESCRIPTION_FILENAME",
    "IGNORED_CATEGORY_DIRS",
    "NAME_MAX",
    "NAME_MIN",
    "NAME_RE",
    "BM25FHit",
    "CatalogCheckResult",
    "CatalogReport",
    "CategoryName",
    "CategorySummary",
    "DiscoveryMatch",
    "DiscoveryResult",
    "ISkillsAdopterProtocol",
    "ISkillsAggregate",
    "ISkillsCreatorProtocol",
    "ISkillsLinterProtocol",
    "ISkillsRunnerProtocol",
    "Issue",
    "LintReport",
    "MutationOutcome",
    "MutationPlan",
    "MutationStep",
    "NewCategoryPlan",
    "SkillContent",
    "SkillCreatePlan",
    "SkillDescription",
    "SkillEntry",
    "SkillName",
    "SkillQuery",
    "SkillRecord",
    "SkillsExitCode",
    "SkillsJsonPayload",
    "SkillsOp",
    "SkillsRequest",
    "SkillsResult",
    "SkillsRoot",
    "TelemetryRow",
    "ValidationReport",
]

_layer_symbols = {
    "ARCHIVE_DIRNAME": ARCHIVE_DIRNAME,
    "BM25FHit": BM25FHit,
    "BM25F_SCORE_SCALE": BM25F_SCORE_SCALE,
    "CATEGORY_DESCRIPTION_FILENAME": CATEGORY_DESCRIPTION_FILENAME,
    "CatalogCheckResult": CatalogCheckResult,
    "CatalogReport": CatalogReport,
    "CategoryName": CategoryName,
    "CategorySummary": CategorySummary,
    "DiscoveryMatch": DiscoveryMatch,
    "DiscoveryResult": DiscoveryResult,
    "IGNORED_CATEGORY_DIRS": IGNORED_CATEGORY_DIRS,
    "ISkillsAdopterProtocol": ISkillsAdopterProtocol,
    "ISkillsAggregate": ISkillsAggregate,
    "ISkillsCreatorProtocol": ISkillsCreatorProtocol,
    "ISkillsLinterProtocol": ISkillsLinterProtocol,
    "ISkillsRunnerProtocol": ISkillsRunnerProtocol,
    "Issue": Issue,
    "LintReport": LintReport,
    "MutationOutcome": MutationOutcome,
    "MutationPlan": MutationPlan,
    "MutationStep": MutationStep,
    "NAME_MAX": NAME_MAX,
    "NAME_MIN": NAME_MIN,
    "NAME_RE": NAME_RE,
    "NewCategoryPlan": NewCategoryPlan,
    "SkillContent": SkillContent,
    "SkillDescription": SkillDescription,
    "SkillEntry": SkillEntry,
    "SkillName": SkillName,
    "SkillQuery": SkillQuery,
    "SkillRecord": SkillRecord,
    "SkillCreatePlan": SkillCreatePlan,
    "SkillsExitCode": SkillsExitCode,
    "SkillsJsonPayload": SkillsJsonPayload,
    "SkillsOp": SkillsOp,
    "SkillsRequest": SkillsRequest,
    "SkillsResult": SkillsResult,
    "SkillsRoot": SkillsRoot,
    "TelemetryRow": TelemetryRow,
    "ValidationReport": ValidationReport,
}
