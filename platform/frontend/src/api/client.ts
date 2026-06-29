const BASE_URL = '/api/v1'

export interface Project {
  id: string
  requirement: string
  summary: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
  progress: PipelineProgress | null
  stats: ProjectStats | null
}

export type ProjectStatus =
  | 'pending'
  | 'analyzing'
  | 'generating_backend'
  | 'generating_frontend'
  | 'testing'
  | 'done'
  | 'failed'

export interface PipelineProgress {
  current_step: string | null
  steps: StepInfo[]
}

export interface StepInfo {
  name: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  duration_ms?: number
  summary?: string
}

export interface ProjectStats {
  total_files: number
  backend_files: number
  frontend_files: number
  test_files: number
  total_lines: number
  test_coverage: number
  tests_passed: number
  tests_failed: number
}

export interface RequirementSpec {
  project_name: string
  summary: string
  manifest: {
    planned: {
      entities: string[]
      endpoints: string[]
      pages: string[]
    }
  }
  entities: EntityDef[]
  api_endpoints: EndpointDef[]
  pages: PageDef[]
}

export interface EntityDef {
  id: string
  name: string
  display_name: string
  description?: string
  fields: FieldDef[]
  relationships?: RelationshipDef[]
}

export interface FieldDef {
  name: string
  display_name?: string
  type: string
  required?: boolean
  unique?: boolean
  max_length?: number
  enum_values?: string[]
  searchable?: boolean
  sortable?: boolean
  default?: unknown
}

export interface RelationshipDef {
  type: string
  target_entity: string
  foreign_key?: string
  nullable?: boolean
}

export interface EndpointDef {
  id: string
  method: string
  path: string
  description: string
  entity: string
  paginated?: boolean
  query_params?: QueryParamDef[]
  request_body?: string | null
  auth_required?: boolean
}

export interface QueryParamDef {
  name: string
  type: string
  required?: boolean
  default?: unknown
}

export interface PageDef {
  id: string
  name: string
  display_name: string
  route: string
  type: string
  entity?: string
  components?: string[]
  actions?: string[]
}

export interface FileTreeNode {
  name: string
  type: 'file' | 'directory'
  children?: FileTreeNode[]
  size?: number
  file_type?: string
}

export interface FileContent {
  path: string
  content: string
  language: string
  size: number
  file_type: string
}

export interface AgentRun {
  id: string
  agent_name: string
  status: string
  started_at: string | null
  finished_at: string | null
  duration_ms: number | null
  error_message: string | null
}

// --- API Functions ---

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }))
    throw new Error(err.error?.message || res.statusText)
  }
  const json = await res.json()
  return json.data as T
}

export async function createProject(data: {
  requirement: string
  template?: string | null
  language?: string
  constraints?: { database?: string }
}): Promise<Project> {
  return request<Project>('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function listProjects(page = 1, pageSize = 20) {
  return request<{ items: Project[]; total: number; page: number; page_size: number }>(
    `/projects?page=${page}&page_size=${pageSize}`
  )
}

export async function getProject(id: string): Promise<Project> {
  return request<Project>(`/projects/${id}`)
}

export async function deleteProject(id: string): Promise<void> {
  await request(`/projects/${id}`, { method: 'DELETE' })
}

export async function getSpec(id: string): Promise<{ requirement_spec: RequirementSpec }> {
  return request<{ requirement_spec: RequirementSpec }>(`/projects/${id}/spec`)
}

export async function updateSpec(id: string, requirement_spec: RequirementSpec): Promise<void> {
  await request(`/projects/${id}/spec`, {
    method: 'PUT',
    body: JSON.stringify({ requirement_spec }),
  })
}

export async function getFileTree(id: string): Promise<{ tree: FileTreeNode[] }> {
  return request<{ tree: FileTreeNode[] }>(`/projects/${id}/files`)
}

export async function getFileContent(id: string, filePath: string): Promise<FileContent> {
  const encodedPath = encodeURIComponent(filePath)
  return request<FileContent>(`/projects/${id}/files/${encodedPath}`)
}

export async function getAgentRuns(id: string): Promise<{ runs: AgentRun[] }> {
  return request<{ runs: AgentRun[] }>(`/projects/${id}/runs`)
}

export function getDownloadUrl(id: string): string {
  return `${BASE_URL}/projects/${id}/download`
}
