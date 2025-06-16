package main

import (
	"fmt"
)

//fmt.Println("Hello world)")

//var name string = "Abhi"
//fmt.Println("name is ", name)

//person := "Aadi"
//fmt.Println("person is", person)
//name := "abhi"
//age := 20
//height := 6.1
//fmt.Printf("Name:%s, Age:%d, height:%f\n", name, age, height)
//fmt.Println("hellow")
//var name string

//fmt.Scan(&name)
//fmt.Println("hello", name)

func simplefunc() {
	fmt.Println("this is simeple func")
}
func add(a, b int) int {
	return a + b
}
func divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, fmt.Errorf("Denominator must bot be zero")
	}
	return a / b, nil
}
func main() {
	fmt.Println("this is the:")
	simplefunc()
	ans := add(10, 20)
	fmt.Println("add of two number:", ans)

	fmt.Println("divide :")
	ans2, _ := divide(10, 0)
	fmt.Println("answer is ", ans2)

}
