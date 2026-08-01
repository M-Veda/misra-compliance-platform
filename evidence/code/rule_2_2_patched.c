#include <stdio.h>
int dead_code_func(int x) {
    if (x > 0) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}
int main(void) { return dead_code_func(1); }
