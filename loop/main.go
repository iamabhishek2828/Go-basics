package main

import (
	"fmt"
)

func main() {
	for i := 0; i < 10; i++ {
		fmt.Println("hello")
	}
	numbers := []int{1, 2, 3, 4, 5, 6, 7, 8, 9}
	for index, value := range numbers {
		fmt.Println("index is ", index, "value is ", value)
	}
	studentgrade := make(map[string]int)
	studentgrade["Abhi"] = 90
	studentgrade["Aadi"] = 80

	fmt.Println("student grade is ", studentgrade)
}
