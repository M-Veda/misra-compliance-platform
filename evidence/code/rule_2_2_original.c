#include <stdio.h>
int dead_code_func(int x) {
    if (x > 0) {
        return 1;
        return 99;   /* dead */
    }
    return 0;
}
int main(void) { return dead_code_func(1); }
