package main

import (
	"fmt"
)

func main() {
	intCount := 0
outerLoop:
	for j := 0; j < 4; j++ {
	innerLoop:
		for i := 0; i < 4; i++ {
			intCount += i
			if i != j {
				continue innerLoop
			} else if i == j {
				continue outerLoop
			}

		}
	}
	fmt.Println("intcount is ", intCount)
}
