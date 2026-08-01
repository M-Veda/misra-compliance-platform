void compliant(void) {
    int x = 5;
    x = x + 1;
}

void non_compliant(void) {
    int x = 5;
    return;
    x = x + 1; /* Dead code */
}
