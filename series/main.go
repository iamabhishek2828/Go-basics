package main

import (
	"fmt"
)

func sumofSquares(n int, fn func(int) int) int {
	total := 0
	for i := 0; i <= n; i++ {
		total += fn(i)

	}
	return total
}
func square(i int) int {
	return i * i

}
func cube(i int) int {
	return i * i * i
}
func main() {
	n := 5
	fmt.Println("sum of squares is", sumofSquares(n, square))
	fmt.Println("sum of cube is", sumofSquares(n, cube))
}
