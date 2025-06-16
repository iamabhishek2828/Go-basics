package main

import (
	"fmt"
)

func main() {

	slice := []int{1, 2, 3, 4}
	slice = append(slice, 5)
	fmt.Println(slice)
	arr := [200]int{1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 22, 3, 44, 66, 77, 89}
	for i := 0; i < 100; i++ {
		fmt.Println(arr[i])
	}

}
