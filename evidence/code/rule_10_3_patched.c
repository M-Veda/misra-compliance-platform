#include <stdio.h>
int func_narrowing(void) {
    unsigned int u = (unsigned int)300u;
    int s = u;
    return s;
}
int main(void) { return func_narrowing(); }
