#include <stdio.h>
int func_with_unused(int active, int unused_param) {
    (void)unused_param;
    return active + 5;
}
int main(void) { return func_with_unused(1, 2); }
