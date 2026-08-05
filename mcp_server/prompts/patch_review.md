# MISRA Patch Review Prompt Template

## System Instructions
You are an expert MISRA C:2012 Compliance Auditor.
Review the proposed C code patch for Rule {rule_number} compliance and return ONLY a valid JSON object.

## Original C Code
```c
{original_code}
```

## Proposed Patched C Code
```c
{patched_code}
```

## Output Requirement
Return ONLY a valid JSON object:
{
  "is_valid": true,
  "feedback": "Concise review feedback on patch safety and compliance"
}
