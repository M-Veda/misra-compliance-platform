
int foo(int x) {
    if (x > 0) {
        return 1;
        return 99;   /* dead */
    }
    return 0;
}
