
#ifndef _LIST_H

#define _LIST_H

struct Node;
typedef struct Node * PtrToNode;
typedef PtrToNode List;
typedef PtrToNode Position;

List MakeEmpty(List L);
int IsEmpty(List L);
int IsLast(List L, Position P);
Position Find(List L, Node N);
void Delete(List L, Node N);
Position FindPrevious(List L, Node N);
void Insert(List L, Position P, Node N);
void DeleteList(List L);
Position Header(List L);
Position First(List L);
Position Advance(Position P);
Node Retrieve(Position P);

#endif  // _LIST_H

struct Node {
    int n
    Position next;
}


