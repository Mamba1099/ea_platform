export type EAStatus =
  | "STOPPED"
  | "STARTING"
  | "RUNNING"
  | "PAUSED"
  | "STOPPING"
  | "ERROR";

export interface BasketTelemetry {
  state: string;
  direction: string;
  positions: number;
  floating_pnl: number;
  average_entry: number;
  last_entry: number;
  thesis_score: number;
  recovery_score: number;
  opportunity_score: number;
  atr: number;
  atr_ratio: number;
  spread: number;
  current_price: number;
  daily_profit: number;
  daily_profit_locked: boolean;
  last_decision: string;
  last_reason: string;
}

export interface EAStatusResponse {
  registry: {
    ea_id: string;
    name: string;
    version: string;
    symbol: string;
    magic_number: number;
    status: EAStatus;
    enabled: boolean;
    heartbeat: string | null;
  };
  ea: {
    ea_id: string;
    name: string;
    version: string;
    symbol: string;
    magic_number: number;
    status: EAStatus;
    enabled: boolean;
    timestamp: string;
    terminal_connected: boolean;
    basket: BasketTelemetry;
    last_request_id: string | null;
    last_command_result: string | null;
    last_command_message: string | null;
  };
  health: {
    ea_id: string;
    status: EAStatus;
    enabled: boolean;
    status_available: boolean;
    file_age_seconds: number;
    healthy: boolean;
    stale: boolean;
    terminal_connected: boolean;
    message: string;
  };
  mt5: {
    running: boolean;
    pid: number;
    terminal: string;
  };
}

export interface EAEvent {
  id: number;
  ea_id: string;
  event_type: string;
  previous_status: string | null;
  current_status: string | null;
  message: string | null;
  created_at: string;
}

export interface Deployment {
  id: number;
  ea_id: string;
  version: string;
  source_path: string;
  target_path: string;
  file_hash: string;
  status: string;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}
