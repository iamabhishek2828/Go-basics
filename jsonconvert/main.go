package main

import (
	"encoding/json"
	"fmt"
)

type Person struct {
	Name   string `json:"name"`
	Age    int    `json:"age"`
	RollNo int    `json:"rollno"`
}

func main() {
	P1 := Person{
		Name:   "Abhi",
		Age:    24,
		RollNo: 101,
	}
	fmt.Println("Person", P1)

	jsonData, err := json.Marshal(P1)
	if err != nil {
		fmt.Println("error in conversion", err)
		return
	}
	fmt.Println("json data ", string(jsonData))

	var P1Converted Person
	err = json.Unmarshal(jsonData, &P1Converted)
	if err != nil {
		fmt.Println("error in conversion", err)
		return
	}
	fmt.Println("converted person", P1Converted)

}
