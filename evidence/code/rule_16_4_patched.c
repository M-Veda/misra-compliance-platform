#include <stdio.h>
int func_no_default(int mode) {
    int res = 0;
    switch (mode) {
        default:
            break;
        case 1:
            res = 10;
            break;
        case 2:
            res = 20;
            break;
    }
    return res;
}
int main(void) { return func_no_default(1); }
