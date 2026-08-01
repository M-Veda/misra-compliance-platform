#include <stdio.h>
int no_proto_func(int val);
int no_proto_func(int val) { return val + 1; }
int main(void) { return no_proto_func(5); }
