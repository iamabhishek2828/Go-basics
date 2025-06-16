package main

import (
	"fmt"
)

func main() {
	p := new(int)
	fmt.Println("value pf p is", *p)
	*p = 42
	fmt.Println("value after assigning", *p)

	type student struct {
		name   string
		rollno int
	}
	studentptr := new(student)
	studentptr.name = "Abhi"
	studentptr.rollno = 101
	fmt.Println("student ", studentptr)
}
