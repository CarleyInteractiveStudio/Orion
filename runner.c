#include <stdio.h>

// Declare the external main function from our Orion code
extern int orion_main();

int main(int argc, char** argv) {
    int result = orion_main();
    printf("Orion main function returned: %d\n", result);
    return 0;
}
