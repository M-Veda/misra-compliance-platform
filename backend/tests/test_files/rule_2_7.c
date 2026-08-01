void compliant(int x) {
    x = x + 1;
}

void non_compliant(int x, int y) {
    x = x + 1; /* y is unused */
}
