/*
**package main

import (

	"fmt"

)

	type Person struct {
		Name string
		age  int
	}

func main() {

		person1 := Person{
			Name: "Abhi",
			age:  24,
		}
		fmt.Println("Person1 ", person1)
	}

package main

import "fmt"

	type Student struct {
		studName       string
		studRollNumber int32
	}

	func main() {
		stud1 := Student{"Rajesh", 1}
		stud2 := Student{"Ramesh", 2}
		fmt.Println("Student Name:", stud1.studName, "Roll:", stud1.studRollNumber)
		fmt.Println("Student Name:", stud2.studName, "Roll:", stud2.studRollNumber)
	}

package main

import (

	"fmt"
	"unsafe"

)

	type Student struct {
		studName       string
		studRollNumber int32
	}

	func main() {
		stud1 := Student{"Rajesh", 1}
		stud2 := Student{"Ramesh Kumar", 2}
		fmt.Println("Student Name:", stud1.studName, "Roll:", stud1.studRollNumber)
		fmt.Println("Student Name:", stud2.studName, "Roll:", stud2.studRollNumber)
		fmt.Println("Size of struct:", unsafe.Sizeof(stud1))
		fmt.Println("Offset of studName:", unsafe.Offsetof(stud1.studName))
		fmt.Println("Offset of studRollNumber:", unsafe.Offsetof(stud1.studRollNumber))
	}

package main
import (“encoding/json";"fmt";)

	type Student struct {
		// Capital variable Names are deliberate because in Go, only exported fields (capitalized names) can be accessed outside their package, including by the json package.
		FName  string `json:"fname"`
		LName  string `json:"lname"`
		RollNo int	`json:"rollno"`
	}

	func main() {
		stud1 := Student{"Vijay", "Mehta", 24}
		stud2 := Student{"Rajesh", "Gupta", 20}
		jsonData1, err := json.Marshal(stud1) // Convert struct to JSON
		if err != nil {
	    	fmt.Println("Error:", err)
		}
		fmt.Println(string(jsonData1)) // Output JSON
		//func MarshalIndent(v interface{}, prefix, indent string) ([]byte, error)
		jsonData2, err := json.MarshalIndent(stud2, "", "") // Pretty-print JSON
		if err != nil {
	    	fmt.Println("Error:", err)
		}
		fmt.Println(string(jsonData2)) // Output JSON
	}

package main

import "fmt"

	func add(fInput int16, sInput int16) int16 {
		return (fInput + sInput)
	}

	func main() {
		fmt.Print("Sum is:", add(2, 3))
	}

package main

import "fmt"

	func swap(fInput int16, sInput int16) (int16, int16) {
		return sInput, fInput
	}

	func divide(fInput, sInput int) (int, int) {
		quotient := fInput / sInput
		remainder := fInput % sInput
		return quotient, remainder
	}

	func main() {
		valAfterswap1, valAfterswap2 := swap(2, 3)
		fmt.Println("Value after Swap:", valAfterswap1, valAfterswap2)
		q, r := divide(76, 3)
		fmt.Println("Q and R is:", q, r)
	}

package main

import "fmt"

	func divide(fInput, sInput int) (quotient int, remainder int) {
		quotient = fInput / sInput
		remainder = fInput % sInput
		return
	}

	func main() {
		q, r := divide(76, 3)
		fmt.Println("Q and R is:", q, r)
	}**
*/
package main

import (
	"fmt"
)

type Student struct {
	name   string
	rollno int
}

func (s Student) PrintDetails() {
	fmt.Println("name:", s.name, "roll.no:", s.rollno)

}
func main() {
	stud1 := Student{
		name:   "ramesh",
		rollno: 122,
	}
	stud1.PrintDetails()
}
