void func(void) {
    float f = 1.0f;
    
    double non_comp = 2.0;
    float f2 = non_comp; /* Narrowing double -> float */
    
    int x = 5;
    char c = x; /* Narrowing int -> char */
}
