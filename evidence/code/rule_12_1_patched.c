#include <stdio.h>
int func_precedence(int x, int y, int z) {
    int res = x + (y * z);
    return res;
}
int main(void) { return func_precedence(1, 2, 3); }
