import re
import os
import subprocess
from typing import Tuple, Optional
from pycparser import c_parser
from pycparser.c_ast import FileAST

# Standard C types and declarations to inject for parsing
FAKE_LIBC_DEFS = """typedef int size_t;
typedef int wchar_t;
typedef int ptrdiff_t;
typedef _Bool bool;
typedef int int8_t;
typedef unsigned char uint8_t;
typedef short int16_t;
typedef unsigned short uint16_t;
typedef int int32_t;
typedef unsigned int uint32_t;
typedef long long int64_t;
typedef unsigned long long uint64_t;

// Standard library function mocks
int printf(const char *format, ...);
int scanf(const char *format, ...);
void *malloc(size_t size);
void free(void *ptr);
void exit(int status);
void *memset(void *s, int c, size_t n);
void *memcpy(void *dest, const void *src, size_t n);
"""

FAKE_LIBC_LINE_COUNT = FAKE_LIBC_DEFS.count("\n")

def remove_includes(source_code: str) -> str:
    """
    Removes #include directives from the source code, replacing them with empty lines
    to maintain consistent line numbering.
    """
    lines = source_code.splitlines()
    processed_lines = []
    for line in lines:
        if re.match(r"^\s*#\s*include\b", line):
            processed_lines.append("")
        else:
            processed_lines.append(line)
    return "\n".join(processed_lines)

class CParserService:
    @staticmethod
    def preprocess_and_clean(source_code: str) -> Tuple[str, str]:
        """
        Cleans the C code for pycparser while strictly preserving line numbers:
        1. Prepend fake libc definitions.
        2. Replace #include and other preprocessor directives with blank lines.
        3. Replace multi-line and single-line comments with blank lines / newlines.
        """
        cleaned_source = remove_includes(source_code)
        full_code = FAKE_LIBC_DEFS + cleaned_source

        # Preserve line numbers by replacing single-line comments with spaces
        cleaned = re.sub(r'//.*', '', full_code)
        # Replace multi-line comments with equivalent number of newlines
        cleaned = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), cleaned, flags=re.DOTALL)
        # Blank out preprocessor directives (#define, #ifdef, etc.) keeping newlines
        cleaned = "\n".join([line if not re.match(r"^\s*#", line) else "" for line in cleaned.splitlines()])

        return cleaned, None

    @staticmethod
    def parse_code(source_code: str, file_name: str = "source.c") -> Tuple[Optional[FileAST], Optional[str]]:
        """
        Preprocesses and parses C source code into a pycparser FileAST.
        """
        if not source_code or not source_code.strip():
            return None, "Source file is empty."

        # Step 1: Preprocess and clean using system tools and fake libc include definitions
        preprocessed, prep_err = CParserService.preprocess_and_clean(source_code)
        if prep_err:
            return None, prep_err
            
        # Step 2: Parse using pycparser
        parser = c_parser.CParser()
        try:
            ast = parser.parse(preprocessed, filename=file_name)
            return ast, None
        except Exception as e:
            return None, f"C Parsing Error: {str(e)}"

    @staticmethod
    def adjust_line(line: int) -> int:
        """
        Adjusts AST line numbers back to the original source code lines
        by subtracting the injected fake libc header lines.
        """
        adjusted = line - FAKE_LIBC_LINE_COUNT
        return max(1, adjusted)
