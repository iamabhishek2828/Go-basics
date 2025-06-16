package main

import (
	"fmt"
)

func factorial(n int) int {
	result := 1
	for i := 2; i <= n; i++ {
		result *= i
	}
	return result
}
func main() {
	num := 5
	fmt.Println("factorial of ", num, "is", factorial(num))

}
