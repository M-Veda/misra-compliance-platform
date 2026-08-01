#include <stdio.h>
int func_nonbool(int count) {
    if (count != 0) {
        return 1;
    }
    return 0;
}
int main(void) { return func_nonbool(5); }
