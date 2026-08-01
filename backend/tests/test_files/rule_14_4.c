void func(void) {
    int b = 1;
    if (b != 0) {} /* compliant */
    if (b) {} /* non-compliant */
}
