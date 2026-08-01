# MISRA C:2012 Static Analyzer — Known Limitations & Future Work

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. Documented Scope & Known Limitations

1. **Rule 10.3 Partial Auto-Patch Policy**:
   - **Safe Cases**: Automatically inserts explicit casts `(target_type)expr` for return statement type mismatches.
   - **Manual Review Cases**: Conversions involving numeric literal suffixing (e.g. `0` vs `0U`) or implicit narrowing in variable initializations are intentionally left for manual developer review to prevent accidental runtime side effects.

2. **Pre-processor Macro Expansions**:
   - The pycparser AST engine requires standard C declarations. Code heavily relying on non-standard compiler attributes or complex macro wrappers should be pre-processed before analysis.

3. **10 Supported Rules Baseline**:
   - This release baseline is frozen for the 10 implemented MISRA C:2012 rules (`2.2`, `2.7`, `7.1`, `8.4`, `8.7`, `10.3`, `12.1`, `14.4`, `16.3`, `16.4`). Additional MISRA rules belong to future engineering cycles.

---

## 2. Future Work & Roadmap

1. **Rule Expansion**: Implement AST checkers for additional MISRA C:2012 rules (e.g. pointer arithmetic, control flow bounds).
2. **Clang / LLVM AST Integration**: Add Clang libclang binding for C11/C17 parsing compatibility.
3. **IDE Integration**: Build VS Code / CLion extensions exposing live AST violation diagnostics and pre-filled manual fix popups directly in the editor.
