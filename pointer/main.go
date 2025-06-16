package main

import (
	"fmt"
)

/*
	**func swap(first *int, second *int) {
		temp := *first
		*first = *second
		*second = temp
	}**
*/
func double(ptrArr [3]*int) {
	for i := 0; i < len(ptrArr); i++ {
		*ptrArr[i] *= 2

	}

}

func main() {
	/***var intVal int = 10
	var p *int
	p = &intVal
	fmt.Println("Value of intVal is ", intVal)
	fmt.Println("Value of p is ", p)
	fmt.Println("Value of *p is ", *p)
	fmt.Println("value of p:", &p)
	*p = 20
	fmt.Println("Value of intVal after changing value of p is ", intVal)
	fmt.Println("Value of p after changing value of p is ", p)
	fmt.Println("Value of *p after changing value of p is ", *p)
	fmt.Println("value of p after changing value of p:", &p)
	var intVal1, intVal2 int = 10, 20
	fmt.Println("value before swapping", intVal1, intVal2)
	swap(&intVal1, &intVal2)
	fmt.Println("value after swapping", intVal1, intVal2)
	var intVal1, intVal2 *int = new(int), new(int)
	fmt.Println("values of pointer before giving values", *intVal1, *intVal2)
	fmt.Println("value storeed in pointer", intVal1, intVal2)
	*intVal1 = 10
	*intVal2 = 20
	fmt.Println("values of pointer after giving values", *intVal1, *intVal2)
	fmt.Println("value stored in pointer", intVal1, intVal2)
	fmt.Println("Address of pointer", &intVal1, &intVal2)
	var intVal int = 9
	intPtr := &intVal
	intDoublePtr := &intPtr

	fmt.Println("value of intval is", intVal)
	fmt.Println("Address of intVal is", &intVal)

	fmt.Println("value of intPtr is", intPtr)
	fmt.Println("value of pointer by pointer is", *intPtr)
	fmt.Println("Address of intPtr is", &intPtr)

	fmt.Println("value of intDoublePtr is", intDoublePtr)
	fmt.Println("value of pointer by pointer is", *intDoublePtr)
	fmt.Println("value of pointer by pointer by pointer is", **intDoublePtr)
	fmt.Println("Address of intDoublePtr is", &intDoublePtr)
	arr := [10]int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	var ptr *[10]int = &arr
	p := &arr[1]
	fmt.Println("array", arr)
	fmt.Println("pointer to array", ptr)
	fmt.Println("address of first element ", &arr[0])
	fmt.Println("address of ptr", &ptr)
	fmt.Println("address of first element of pointer", &ptr[0])
	fmt.Println("address of second element of pointer", &ptr[1])
	fmt.Println("value of second element of pointer", ptr[1])
	fmt.Println("First element via pointer:", (*ptr)[0])
	fmt.Println("Value Stored in Pointer to array element:", p)
	fmt.Println("Value pointed by p:", *p)
	fmt.Println("Entire Array via pointer:", (*ptr))

	firstVar, secondVar, thirdVar := 1, 2, 3
	ptrArr := [3]*int{&firstVar, &secondVar, &thirdVar} // Array of pointers
	fmt.Println("Value of Each variable through Array of Pointers:")
	for i := 0; i < len(ptrArr); i++ {
		fmt.Println(*ptrArr[i]) // Dereferencing pointer
	}***/
	firstVar, secondVar, thirdVar := 1, 2, 3
	ptrArr := [3]*int{&firstVar, &secondVar, &thirdVar} // Array of pointers
	fmt.Println("Value of Each variable through Array of Pointers:")
	for i := 0; i < len(ptrArr); i++ {
		fmt.Println(*ptrArr[i])
	}
	fmt.Println("Value of Each variable through Array of Pointers after doubling:")
	double(ptrArr)
	for i := 0; i < len(ptrArr); i++ {
		fmt.Println(*ptrArr[i])
	}

}
