#include <stdio.h>
int func_nonbool(int count) {
    if (count) {
        return 1;
    }
    return 0;
}
int main(void) { return func_nonbool(5); }
