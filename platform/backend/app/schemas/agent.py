"""Pydantic schemas for agent input/output validation (Agent Protocol v0.1)."""

from pydantic import BaseModel, Field
from typing import Optional


# ── NaturalLanguageSpec (user input) ──

class Constraints(BaseModel):
    target_framework: str = "fastapi"
    target_frontend: str = "react"
    database: str = "sqlite"
    auth_required: bool = False
    max_entities: int = 10


class NaturalLanguageSpec(BaseModel):
    requirement: str = Field(..., min_length=10, max_length=2000)
    template: Optional[str] = None  # crud_admin | rest_api | dashboard
    language: str = "zh"
    constraints: Constraints = Field(default_factory=Constraints)
    design_spec: Optional[dict] = None


# ── RequirementSpec (Requirement Agent output) ──

class FieldDef(BaseModel):
    name: str
    display_name: Optional[str] = None
    type: str  # string | integer | float | boolean | datetime | text | enum | file
    required: bool = False
    unique: bool = False
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default: Optional[object] = None
    enum_values: Optional[list[str]] = None
    searchable: bool = False
    sortable: bool = False


class RelationshipDef(BaseModel):
    type: str  # belongs_to | has_many | many_to_many
    target_entity: str
    foreign_key: Optional[str] = None
    nullable: bool = False


class EntityDef(BaseModel):
    id: str  # ent_001
    name: str  # PascalCase
    display_name: Optional[str] = None
    description: Optional[str] = None
    fields: list[FieldDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)


class QueryParamDef(BaseModel):
    name: str
    type: str = "string"
    required: bool = False
    default: Optional[object] = None


class EndpointDef(BaseModel):
    id: str  # ep_001
    method: str  # GET | POST | PUT | PATCH | DELETE
    path: str
    description: str
    entity: Optional[str] = None
    query_params: list[QueryParamDef] = Field(default_factory=list)
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    paginated: bool = False
    auth_required: bool = False


class PageDef(BaseModel):
    id: str  # page_001
    name: str  # PascalCase component name
    display_name: Optional[str] = None
    route: str
    type: str  # list | detail | form | dashboard
    entity: Optional[str] = None
    components: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class ManifestPlanned(BaseModel):
    entities: list[str] = Field(default_factory=list)
    endpoints: list[str] = Field(default_factory=list)
    pages: list[str] = Field(default_factory=list)


class RequirementSpec(BaseModel):
    project_name: str
    summary: str
    manifest: dict = Field(default_factory=dict)  # { planned: { entities: [...], ... } }
    entities: list[EntityDef] = Field(default_factory=list)
    api_endpoints: list[EndpointDef] = Field(default_factory=list)
    pages: list[PageDef] = Field(default_factory=list)


# ── Completion Manifest ──

class ManifestItem(BaseModel):
    ref_id: str  # ent_001 / ep_001 / page_001
    ref_type: str  # entity | endpoint | page
    status: str  # completed | partial | skipped | deferred
    detail: Optional[str] = None
    output_files: list[str] = Field(default_factory=list)
    skip_reason: Optional[str] = None


class ManifestStats(BaseModel):
    total_planned: int = 0
    completed: int = 0
    partial: int = 0
    skipped: int = 0
    deferred: int = 0


class CompletionManifest(BaseModel):
    summary: str
    items: list[ManifestItem] = Field(default_factory=list)
    stats: ManifestStats = Field(default_factory=ManifestStats)
