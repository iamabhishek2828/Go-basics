package main

import (
	"fmt"
	"unsafe"
)

func main() {
	arr := [5]int{1, 2, 3, 4, 5}
	ptr := &arr[0]
	fmt.Println("array", arr)
	fmt.Println("pointer to array", ptr)
	for i := 0; i < 5; i++ {
		fmt.Println("value of ptr is", *ptr)
		ptr = (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(ptr)) + uintptr(unsafe.Sizeof(ptr))))
	}
}
