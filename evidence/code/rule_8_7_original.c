#include <stdio.h>
int global_single_use = 42;
int func_internal(void) { return global_single_use; }
int main(void) { return func_internal(); }
