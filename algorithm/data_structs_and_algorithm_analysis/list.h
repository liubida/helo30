#ifndef _LIST_H

#define _LIST_H

#include <iostream>
#include <string.h>

using namespace std;

class Node;
typedef Node * Position;

class Node {
public:
    int n;
    Position next;
    Node() {
        n = 0;
        next = NULL;
    }

    Node(int x) {
        n = x;
        next = NULL;
    }
};

class List {

private:
    Position header;
    
public:
    List() {
        header = new Node();
    }

    ~List() {
        if (NULL == header) {
            return;
        }
    
        Position p = header->next;
        while (NULL != p) {
            header->next = p->next;
            delete p;
            p = header->next;
        }
    }
    
    void insert(Position p, int n) {
        Position q = new Node(n);

        if (NULL == p) {
            q->next = header->next;
            header->next = q;
        } else {
            q->next = p->next;
            p->next = q;
        }
    }
    
    void Delete(int n) {
        Position p = FindPrevious(n);
        if (NULL == p || NULL == p->next) {
            return;
        }
    
        Position q = p->next;
        p->next = q->next;
        delete q;
    
        return;
    }

    int IsEmpty() {
        return header->next == NULL;
    }
    
    Position Find(int n) {
        if (NULL == header) {
            return NULL;
        }
    
        Position p = header->next;
        while (NULL != p && p->n != n) {
            p = p->next;
        }
    
        return p;
    }
    
    Position FindPrevious(int n) {
        if (NULL == header) {
            return NULL;
        }
    
        Position p = header->next;
        while (NULL != p && NULL != p->next && p->next->n != n) {
            p = p->next;
        }
    
        return p;
    }

    void travel() {
        if (NULL == header) {
            return;
        }
        Position p = header->next;
        while (NULL != p) {
            cout << p->n << ',';
            p = p->next;
        }
    }
    //
    //int Retrieve(Position P);

};


#endif  // _LIST_H

