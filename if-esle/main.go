package main

import (
	"fmt"
)

func main() {
	x := 10
	if x > 5 {
		fmt.Println("X is grester than 5")
	} else if x < 5 {
		fmt.Println("X is less than 5")
	} else {
		fmt.Println("x is equal to 5")
	}

	y := 20
	if x > 5 {
		fmt.Println("x is greaterr")
	} else if x > 5 && y < 20 {
		fmt.Println("x is greater but less than 20")
	} else {
		fmt.Println("x is equalt ott 5")

	}
}
