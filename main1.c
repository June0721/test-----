#include <stdio.h>

int main(){
    int a=0;
    int *pa=&a;
    printf("请输入：");
    scanf("%d",pa);
    printf("%d",*pa);
}