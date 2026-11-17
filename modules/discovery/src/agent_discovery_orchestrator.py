"""Discovery agent (AES agent layer).

Implements ``ISkillsDiscoveryAggregate`` over the discovery-side capabilities:
catalog, discover, lister, reader. Owns the ops: list, read, lint, catalog,
discover.

The entry point is ``execute(DiscoveryRequest) -> DiscoveryResponse`` using the
discovery-domain request/response VOs from ``taxonomy_discovery_request`` and
``taxonomy_discovery_response``. Capabilities speak ``DiscoveryQuery``/
``DiscoveryRoot`` per their protocols.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import SkillsError, SkillsRootError
from shared.src.common.taxonomy_common_vo import SkillContent
from shared.src.discovery.contract_discovery_aggregate import (
    ISkillsDiscoveryAggregate,
)
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
    T,
)
from shared.src.discovery.taxonomy_discovery_response import DiscoveryResponse

__all__ = [
    "SkillsDiscoveryAgent",
]

# ─── Block 1: Module Declaration ────────────────────────────────────────

class SkillsDiscoveryAgent(ISkillsDiscoveryAggregate):
    """Discovery-side agent: list / read / lint / catalog / discover."""

    def __init__(
        self,
        catalog: ISkillsCatalogProtocol,
        discover: ISkillsDiscoverProtocol,
        lister: ISkillsListerProtocol,
        reader: ISkillsReaderProtocol,
        default_root: DiscoveryRoot | None = None,
    ) -> None:
        self._catalog = catalog
        self._discover = discover
        self._lister = lister
        self._reader = reader
        self._default_root = default_root


    def _require(self, capability: T | None, name: str) -> T:
        if capability is None:
            raise SkillsRootError(f"discovery capability not wired: {name}")
        return capability

    def _root(self, request: DiscoveryRequest) -> DiscoveryRoot | None:
        return request.root or self._default_root

    # ─── Block 2: Module Contract ─────────────────────────────────────────
    def execute(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """Route *request* to the matching discovery capability."""
        verb_value = request.verb
        if not isinstance(verb_value, DiscoveryVerb):
            try:
                verb_value = DiscoveryVerb(verb_value)
            except ValueError:
                return DiscoveryResponse(
                    ok=False,
                    verb=DiscoveryVerb.LIST,
                    exit_code=2,
                    message=f"Unknown discovery verb: {request.verb}",
                )
        verb = verb_value

        try:
            handler = self._handler_for(verb)
        except KeyError:
            return DiscoveryResponse(
                ok=False,
                verb=verb,
                exit_code=2,
                message=f"Unknown discovery verb: {verb}",
            )

        try:
            if verb == DiscoveryVerb.CATALOG:
                return handler(
                    request,
                    check=str(request.flags.get("check", "")).lower() in ("1", "true"),
                    build=str(request.flags.get("build", "1")).lower() in ("1", "true"),
                    read=str(request.flags.get("read", "1")).lower() in ("1", "true"),
                )
            if verb == DiscoveryVerb.DISCOVER:
                limit_raw = request.flags.get("limit", "20") or "20"
                try:
                    limit = int(limit_raw)
                except (TypeError, ValueError):
                    return DiscoveryResponse(
                        ok=False,
                        verb=verb,
                        exit_code=2,
                        message=f"Invalid limit: {limit_raw!r}",
                    )
                return handler(request, limit=limit)
            return handler(request)
        except SkillsError as failure:
            return DiscoveryResponse(
                ok=False,
                verb=verb,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, verb: DiscoveryVerb
    ) -> Callable[..., DiscoveryResponse]:
        name = f"_execute_{verb.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[..., DiscoveryResponse], handler)

    # ─── Block 3: Module Helpers ──────────────────────────────────────────
    def _execute_list(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """LIST: enumerate every skill record."""
        lister = self._require(self._lister, "lister")
        root = self._root(request)
        records = lister.list_skills(root)
        return DiscoveryResponse(ok=True, verb=request.verb, records=records, root=root)

    def _execute_read(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """READ: show one skill's SKILL.md content."""
        reader = self._require(self._reader, "reader")
        root = self._root(request)
        if not request.query or not str(request.query).strip():
            return DiscoveryResponse(
                ok=False,
                verb=request.verb,
                exit_code=1,
                message="Skill name required",
            )
        content = reader.show_skill(
            DiscoveryQuery(str(request.query).strip()), root
        )
        if content is None:
            return DiscoveryResponse(
                ok=False,
                verb=request.verb,
                exit_code=1,
                message=f"Skill not found: {request.query}",
            )
        return DiscoveryResponse(ok=True, verb=request.verb, content=content, root=root)

    def _execute_lint(self, request: DiscoveryRequest) -> DiscoveryResponse:
        """Lint is a design-side op; delegate returns discovery-not-handled."""
        return DiscoveryResponse(
            ok=False,
            verb=request.verb,
            exit_code=2,
            message="lint is owned by the design agent",
        )

    def _execute_catalog(
        self,
        request: DiscoveryRequest,
        check: bool = False,
        build: bool = True,
        read: bool = True,
    ) -> DiscoveryResponse:
        """CATALOG: build/check/read the catalog.json artifact.

        Honors the tri-state build/read flags the CLI surface sends:
        ``build`` rebuilds the artifact from the live tree, ``read``
        returns the tracked bytes on the response. With neither flag set
        the verb answers a read-only view (no write), which keeps the
        read path non-destructive when a caller pins ``build=0``.
        """
        catalog = self._require(self._catalog, "catalog")
        root = self._root(request)
        if check:
            check_report = catalog.check(root)
            return DiscoveryResponse(
                ok=check_report.in_sync,
                verb=request.verb,
                exit_code=0 if check_report.in_sync else 3,
                catalog_check=check_report,
                root=root,
            )
        rebuild_report = catalog.rebuild(root) if build else None
        text = catalog.read(root) if read else None
        ok = True
        message = ""
        exit_code = 0
        if read and not text:
            # No tracked artifact: report through the same channel the CLI
            # read renderer consumes, so the surface can print its tip.
            ok = False
            exit_code = 1
            message = "catalog.json not found — run with --build first"
        return DiscoveryResponse(
            ok=ok,
            verb=request.verb,
            exit_code=exit_code,
            message=message,
            catalog_report=rebuild_report,
            catalog_text=text,
            root=root,
        )

    def _execute_discover(
        self, request: DiscoveryRequest, limit: int = 20
    ) -> DiscoveryResponse:
        """DISCOVER: BM25F-ranked search over catalog rows."""
        discover = self._require(self._discover, "discover")
        root = self._root(request)
        if not request.query or not str(request.query).strip():
            return DiscoveryResponse(
                ok=False,
                verb=request.verb,
                exit_code=2,
                message="Query required",
            )
        result = discover.discover(
            DiscoveryQuery(str(request.query).strip()), root, limit
        )
        return DiscoveryResponse(ok=True, verb=request.verb, discovery=result, root=root)

    def show_skill(
        self, name: str, root: DiscoveryRoot | None = None
    ) -> SkillContent | None:
        """Pass-through to the reader (used by the facade)."""
        reader = self._require(self._reader, "reader")
        return reader.show_skill(DiscoveryQuery(name), root)
