
#include <stdio.h>
#include "list.h"

void test_list() {
    List* l = new List();

    for(int i=0; i<10; i++) {
        (*l).insert(NULL, i);
    }
    (*l).travel();

}

int main() {
    test_list();
}

