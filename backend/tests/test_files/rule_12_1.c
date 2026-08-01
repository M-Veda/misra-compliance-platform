void func(void) {
    int a = 1, b = 2, c = 3;
    int comp = (a + b) * c;
    int non_comp = a + b * c; /* Precedence issue */
}
