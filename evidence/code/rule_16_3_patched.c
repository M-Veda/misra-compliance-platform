#include <stdio.h>
int func_no_break(int mode) {
    int res = 0;
    switch (mode) {
        case 1:
            res = 10;
            break;
        case 2:
            res = 20;
            break;
        default:
            res = 0;
            break;
    }
    return res;
}
int main(void) { return func_no_break(1); }
