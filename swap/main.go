package main

import (
	"fmt"
)

/*
	**func swap(a, b int) (int, int) {
		temp := a
		a = b
		b = temp
		fmt.Println("inside swap", a, b)
		return a, b
	}

	func main() {
		a := 10
		b := 20
		fmt.Println("before swap values", a, b)
		a, b = swap(a, b)
		fmt.Println("after swap values", a, b)

}**
*/
func swaptr(aptr, bptr *int) {
	temp := *aptr
	*aptr = *bptr
	*bptr = temp

}
func main() {
	a := 10
	b := 20
	fmt.Println("before swap values", a, b)
	swaptr(&a, &b)
	fmt.Println("after swap values", a, b)

}
