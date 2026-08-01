int func_with_return(void) { return 0; }

void caller(void) {
    int a = func_with_return(); /* Compliant */
    (void)func_with_return(); /* Compliant */
    
    func_with_return(); /* Non-compliant */
}
