#include <stdio.h>

int global_val1 = 10;

int calc(int x) {
    x + 1;
    return x * 2;
}

void process_data(int active, int unused_param1, int unused_param2) {
    int uninit_var1;
    int uninit_var2;
    int a = 5;
    int b = 10;
    int c = 2;
    double d1 = 3.14159;
    double d2 = 2.71828;
    
    uninit_var1 + 1;
    uninit_var2 + 2;
    
    a + 1;
    b + 2;
    
    int converted1 = d1;
    int converted2 = d2;
    
    int result1 = a + b * c;
    int result2 = a * b + c;
    
    if (active) {
        printf("Active\n");
    }
    
    if (a > 5) {
        return;
    }
    
    printf("Done\n");
}