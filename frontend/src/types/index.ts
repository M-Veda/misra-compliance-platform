// ─── Patch lifecycle states ────────────────────────────────────────────────
export type PatchState =
  | 'DETECTED'
  | 'PREVIEW_READY'
  | 'PATCH_FAILED'
  | 'MANUAL_REQUIRED'
  | 'ACCEPTED'
  | 'APPLIED'
  | 'VERIFIED'
  | 'CLOSED';

export type PatchType = 'AUTO_PATCH' | 'TEMPLATE_PATCH' | 'AI_SUGGESTED_PATCH' | 'MANUAL_REVIEW_REQUIRED';

export interface PatchPreview {
  violation_id: string;
  rule_number: string;
  file: string;
  line: number;
  column: number;
  original_start_line: number;
  original_end_line: number;
  original_source: string;
  replacement_source: string;
  unified_diff: string;
  explanation: string;
  confidence: number;
  patch_type: PatchType;
  applies_cleanly: boolean;
  can_autopatch: boolean;
  affected_lines: number[];
  compliance_gain: number;

  // Backward compatibility fields
  rule_name?: string;
  original_snippet?: string;
  proposed_snippet?: string;
  diff?: string;
  expected_compliance_improvement?: number;
  no_patch_reason?: string;
}

// ─── Violation ─────────────────────────────────────────────────────────────
export interface RuleViolation {
  rule_number: string;
  rule_name: string;
  severity: 'Mandatory' | 'Required' | 'Advisory';
  category: string;
  file: string;
  line: number;
  column: number;
  message: string;
  code_snippet: string;
  reason: string;
  suggested_fix: string;
  confidence: number;
  // Semantic context for stable ID (populated by backend)
  ast_node_type?: string;
  scope_name?: string;
  // Stable ID provided by backend (location-independent)
  stable_id?: string;
  // Structured preview object attached to every violation
  patch_preview?: PatchPreview;
}


// ─── Stable violation key ──────────────────────────────────────────────────
/**
 * Location-independent stable identifier derived from semantic content.
 * Uses stable_id if the backend provided it, otherwise derives from
 * rule_number + normalised snippet hash (no line/column dependency).
 *
 * Uses a djb2-style hash instead of btoa() to safely handle non-Latin1
 * characters that may appear in C code snippets or comments.
 */
function hashStr(s: string): string {
  let h = 5381;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h) ^ s.charCodeAt(i);
    h = h >>> 0; // keep unsigned 32-bit
  }
  return h.toString(36).padStart(7, '0').slice(0, 8);
}

export function violationStableKey(v: RuleViolation): string {
  if (v.stable_id) return v.stable_id;
  // Fallback: rule + ast_node_type + scope + normalised snippet hash
  const normalised = v.code_snippet.replace(/\s+/g, ' ').trim().slice(0, 64);
  const nodeType = v.ast_node_type || 'Unknown';
  const scope    = v.scope_name    || '__global__';
  return `${v.rule_number.replace('.', '_')}_${nodeType}_${scope}_${hashStr(normalised)}`;
}

// ─── Analysis result ────────────────────────────────────────────────────────
export interface AnalysisResult {
  success: boolean;
  file_name: string;
  source_code: string;
  violations: RuleViolation[];
  compliance_score: number;
  error?: string;
}

// ─── Rule metadata ──────────────────────────────────────────────────────────
export interface RuleInfo {
  rule_number: string;
  rule_name: string;
  severity: string;
  category: string;
  description: string;
  example_violation?: string;
  compliant_example?: string;
}

export const ALL_10_MISRA_RULES: RuleInfo[] = [
  { rule_number: '2.2', rule_name: 'No dead code', severity: 'Required', category: 'Unused Code', description: 'There shall be no dead or unreachable code.' },
  { rule_number: '2.7', rule_name: 'No unused function parameters', severity: 'Advisory', category: 'Unused Code', description: 'There shall be no unused parameters in functions.' },
  { rule_number: '7.1', rule_name: 'Octal constants shall not be used', severity: 'Required', category: 'Literals', description: 'Octal constants and octal escape sequences shall not be used.' },
  { rule_number: '8.4', rule_name: 'Visible prototype required', severity: 'Required', category: 'Declarations', description: 'A compatible declaration shall be visible when an object or function with external linkage is defined.' },
  { rule_number: '8.7', rule_name: 'Block scope or internal linkage', severity: 'Advisory', category: 'Declarations', description: 'Functions and objects should be declared at block scope if accessed by only one function.' },
  { rule_number: '10.3', rule_name: 'No implicit narrowing type conversion', severity: 'Required', category: 'Types', description: 'The value of an expression shall not be assigned to an object with a narrower essential type.' },
  { rule_number: '12.1', rule_name: 'Explicit operator precedence', severity: 'Advisory', category: 'Expressions', description: 'The precedence of operators within expressions should be made explicit using parentheses.' },
  { rule_number: '14.4', rule_name: 'Controlling expression essentially Boolean', severity: 'Required', category: 'Control Flow', description: 'The controlling expression of an if statement and iteration statement shall be essentially Boolean.' },
  { rule_number: '16.3', rule_name: 'Switch clause missing break', severity: 'Required', category: 'Control Flow', description: 'An unconditional break statement shall terminate every non-empty switch clause.' },
  { rule_number: '16.4', rule_name: 'Every switch statement shall have a default clause', severity: 'Required', category: 'Control Flow', description: 'Every switch statement shall have a default clause.' },
];

// ─── Decision types ─────────────────────────────────────────────────────────
export type DecisionType = 'Accept' | 'Reject' | 'Skip' | 'Manual';

// ─── Synchronized analysis metrics (single source of truth) ─────────────────
export interface AnalysisMetrics {
  /** Immutable baseline: number of violations detected on first analysis */
  total_detected: number;
  /** Violations with decision === 'Accept' AND patch was successfully applied */
  accepted: number;
  /** Violations with decision === 'Reject' */
  rejected: number;
  /** Violations with decision === 'Skip' */
  skipped: number;
  /** Violations with decision === 'Manual' */
  manual: number;
  /** total_detected - (accepted + rejected + skipped + manual) */
  remaining: number;
  /** Authoritative compliance score derived from baseline */
  compliance_score: number;
}

// ─── App settings ───────────────────────────────────────────────────────────
export interface AppSettings {
  // Appearance
  theme: 'dark' | 'light';
  fontSize: number;
  showLineNumbers: boolean;
  wordWrap: boolean;

  // Review Preferences
  confirmBulkActions: boolean;
  confirmReanalysis: boolean;
  autoScrollNextViolation: boolean;

  // AI
  enableAIExplanations: boolean;

  // Generated Code
  filenameSuffix: string;

  // Reports
  defaultReportFormat: 'pdf' | 'json' | 'both';
  autoOpenReport: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'dark',
  fontSize: 14,
  showLineNumbers: true,
  wordWrap: true,
  confirmBulkActions: true,
  confirmReanalysis: false,
  autoScrollNextViolation: true,
  enableAIExplanations: true,
  filenameSuffix: '_fixed',
  defaultReportFormat: 'pdf',
  autoOpenReport: false,
};

// ─── Per-file session state ─────────────────────────────────────────────────
export interface FileAnalysisItem {
  file_name: string;
  /** Original uploaded source — NEVER modified */
  original_code: string;
  /** Current authoritative working copy — only source for Generated Code & Reports */
  working_code: string;
  /** Alias kept for API compat — always equals working_code */
  source_code: string;
  /** Alias kept for Reports/Downloads — always equals working_code */
  corrected_code: string;
  /** Immutable baseline violations snapshot from first analysis — NEVER replaced */
  all_violations: RuleViolation[];
  /** Active remaining violations (subset of all_violations) */
  violations: RuleViolation[];
  decisions: Record<string, DecisionType>;
  manual_codes: Record<string, string>;
  compliance_score: number;
  is_finalized?: boolean;
  total_accepted_count?: number;
}
