export interface Role {
  id: number
  name: string
  description: string | null
}

export interface RegisteredUser {
  id: number
  username: string
  role: Role | null
}

export interface JwtPayload {
  sub: string
  role: string
  exp: number
}

export const AVAILABLE_DESTINATIONS = ['slack', 'discord'] as const
export type Destination = (typeof AVAILABLE_DESTINATIONS)[number]

export interface Delivery {
  service: string
  status: 'success' | 'failed' | 'pending' | string
  provider_response: string | null
  attempt: number
}

export interface Message {
  id: number
  content: string
  created_at: string
  deliveries: Delivery[]
}

export interface AdminDelivery {
  service: string
  status: string
  provider_response: string | null
}

export interface AdminMessage {
  id: number
  user: string
  content: string
  created_at: string
  deliveries: AdminDelivery[]
}

export interface MessageFilters {
  status?: string
  service?: string
  from_date?: string
  to_date?: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export interface UserMetric {
  user_id: number
  username: string
  role: string
  is_active: boolean
  daily_limit: number
  total_messages: number
  messages_today: number
  remaining_today: number
  deliveries: {
    total: number
    successful: number
    failed: number
  }
}

export interface DailyMetric {
  dia: string
  total_mensajes: number
  deliveries_exitosas: number
  deliveries_fallidas: number
}

export interface LimitsResponse {
  global_limit: number
  users: {
    user_id: number
    username: string
    custom_limit: number | null
    effective_limit: number
  }[]
}

export interface AuditRecord {
  changed_by: string
  target: string
  old_limit: number
  new_limit: number
  changed_at: string
}

export interface ActionResult {
  message: string
  [key: string]: unknown
}

export interface ApiErrorBody {
  detail?: string
}
