export type Candidate = {
  id: number;
  name: string | null;
  phone: string | null;
  email: string | null;
  school: string | null;
  major: string | null;
  degree: string | null;
  graduation_date: string | null;
  applied_position: string | null;
  resume_source: string;
  current_stage: string;
  department: string | null;
  hr_owner: string | null;
  interviewer: string | null;
  interview_time: string | null;
  current_status: string;
  is_overdue: boolean;
  resume_file_path: string | null;
  ai_summary: string | null;
  skills: string[];
  matching_points: string[];
  risk_points: string[];
  interview_questions: string[];
  confidence: number;
  created_at: string;
  updated_at: string;
};

export type ResumeFile = {
  id: number;
  filename: string;
  sha256: string;
  parse_status: string;
  extracted_text: string;
  parsed_payload: Record<string, unknown> | null;
  duplicate_candidate_id: number | null;
  candidate_id: number | null;
  created_at: string;
};

export type EventLog = {
  id: number;
  event_type: string;
  candidate_id: number | null;
  actor: string;
  old_stage: string | null;
  new_stage: string | null;
  note: string | null;
  created_at: string;
};

export type Metrics = {
  total_candidates: number;
  new_this_week: number;
  pending_screening: number;
  pending_interview_schedule: number;
  pending_feedback: number;
  overdue: number;
  offers: number;
};

export type ChartPoint = {
  name: string;
  value: number;
};

export type Trends = {
  recent_seven_days: ChartPoint[];
  position_counts: ChartPoint[];
  stage_distribution: ChartPoint[];
  average_stage_hours: ChartPoint[];
};

export type Task = {
  candidate_id: number;
  candidate_name: string | null;
  stage: string;
  department: string | null;
  overdue_hours: number;
  reminder_text: string;
};
