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
  detection_logic?: string;
  auto_fix_policy?: string;
  example_violation?: string;
  compliant_example?: string;
}

export interface ScanHistory {
  id: number;
  file: string;
  score: number;
  time: string;
  status: string;
  violations?: number;
}

export const ALL_10_MISRA_RULES: RuleInfo[] = [
  {
    rule_number: '2.2',
    rule_name: 'No dead code',
    severity: 'Required',
    category: 'Unused Code',
    description: 'There shall be no dead or unreachable code.',
    detection_logic: 'Identifies statements without side effects (e.g. x + 1;) or statements executed after an unconditional return.',
    auto_fix_policy: 'Auto-Patchable: Removes the side-effect-free statement or unreachable line.',
    example_violation: 'int test(int x) {\n    x + 1; // Violation: statement has no side effect\n    return x;\n    x = 10; // Violation: unreachable code\n}',
    compliant_example: 'int test(int x) {\n    int y = x + 1;\n    return y;\n}',
  },
  {
    rule_number: '2.7',
    rule_name: 'No unused function parameters',
    severity: 'Advisory',
    category: 'Unused Code',
    description: 'There shall be no unused parameters in functions.',
    detection_logic: 'Scans function definitions for parameters not referenced within the function body.',
    auto_fix_policy: 'Auto-Patchable: Inserts (void)param; at the start of the function body.',
    example_violation: 'void foo(int a, int b) {\n    (void)a;\n    // Parameter b is unused\n}',
    compliant_example: 'void foo(int a, int b) {\n    (void)a;\n    (void)b;\n}',
  },
  {
    rule_number: '7.1',
    rule_name: 'Octal constants shall not be used',
    severity: 'Required',
    category: 'Literals',
    description: 'Octal constants and octal escape sequences shall not be used.',
    detection_logic: 'Detects integer literals starting with a leading zero (e.g. 077).',
    auto_fix_policy: 'Auto-Patchable: Converts octal literal to decimal representation (e.g. 63).',
    example_violation: 'int mask = 077; // Violation: octal literal',
    compliant_example: 'int mask = 63; // Compliant: decimal literal',
  },
  {
    rule_number: '8.4',
    rule_name: 'Visible prototype required',
    severity: 'Required',
    category: 'Declarations',
    description: 'A compatible declaration shall be visible when an object or function with external linkage is defined.',
    detection_logic: 'Checks global functions and variables for a preceding visible prototype declaration.',
    auto_fix_policy: 'Auto-Patchable: Prepends a matching prototype declaration above the definition.',
    example_violation: 'int add(int a, int b) { return a + b; } // Violation: missing prototype',
    compliant_example: 'int add(int a, int b);\nint add(int a, int b) { return a + b; }',
  },
  {
    rule_number: '8.7',
    rule_name: 'Block scope or internal linkage',
    severity: 'Advisory',
    category: 'Declarations',
    description: 'Functions and objects should be declared at block scope if accessed by only one function.',
    detection_logic: 'Identifies global variables accessed only within a single function scope.',
    auto_fix_policy: 'Auto-Patchable: Prepends the static storage class specifier to limit scope.',
    example_violation: 'int file_local_var = 0; // Violation: single-use global',
    compliant_example: 'static int file_local_var = 0; // Compliant: internal linkage',
  },
  {
    rule_number: '10.3',
    rule_name: 'No implicit narrowing type conversion',
    severity: 'Required',
    category: 'Types',
    description: 'The value of an expression shall not be assigned to an object with a narrower essential type.',
    detection_logic: 'Detects implicit narrowing assignments where expression value is assigned to a smaller essential type.',
    auto_fix_policy: 'Partial Auto-Patch: Safe explicit casts (target_type)expr applied automatically; semantic conversions left for manual review.',
    example_violation: 'int x = 1000;\nshort s = x; // Violation: implicit narrowing cast',
    compliant_example: 'int x = 1000;\nshort s = (short)x; // Compliant: explicit cast',
  },
  {
    rule_number: '12.1',
    rule_name: 'Explicit operator precedence',
    severity: 'Advisory',
    category: 'Expressions',
    description: 'The precedence of operators within expressions should be made explicit using parentheses.',
    detection_logic: 'Identifies binary operator expressions with mixed precedence lacking explicit parentheses.',
    auto_fix_policy: 'Auto-Patchable: Wraps sub-expressions in explicit parentheses ((a * b) + c).',
    example_violation: 'int res = a + b * c; // Violation: implicit operator precedence',
    compliant_example: 'int res = a + (b * c); // Compliant: explicit parentheses',
  },
  {
    rule_number: '14.4',
    rule_name: 'Controlling expression essentially Boolean',
    severity: 'Required',
    category: 'Control Flow',
    description: 'The controlling expression of an if statement and iteration statement shall be essentially Boolean.',
    detection_logic: 'Checks controlling expressions of if statements to ensure they are essentially Boolean.',
    auto_fix_policy: 'Auto-Patchable: Transforms integer controlling expressions if (expr) to if ((expr) != 0).',
    example_violation: 'if (status) { do_something(); } // Violation: integer controlling expression',
    compliant_example: 'if (status != 0) { do_something(); } // Compliant: explicit comparison',
  },
  {
    rule_number: '16.3',
    rule_name: 'Switch clause missing break',
    severity: 'Required',
    category: 'Control Flow',
    description: 'An unconditional break statement shall terminate every non-empty switch clause.',
    detection_logic: 'Checks non-empty switch clause terminations for an unconditional break; statement.',
    auto_fix_policy: 'Auto-Patchable: Appends break; at the end of the non-empty switch clause.',
    example_violation: 'switch(mode) {\n  case 1: x = 5; // Violation: missing break\n  case 2: y = 10; break;\n}',
    compliant_example: 'switch(mode) {\n  case 1: x = 5; break;\n  case 2: y = 10; break;\n}',
  },
  {
    rule_number: '16.4',
    rule_name: 'Every switch statement shall have a default clause',
    severity: 'Required',
    category: 'Control Flow',
    description: 'Every switch statement shall have a default clause.',
    detection_logic: 'Verifies that every switch statement contains a default clause.',
    auto_fix_policy: 'Auto-Patchable: Appends default:\\n    break; to the switch statement body.',
    example_violation: 'switch(val) {\n  case 1: break; // Violation: missing default clause\n}',
    compliant_example: 'switch(val) {\n  case 1: break;\n  default:\n    break;\n}',
  },
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
