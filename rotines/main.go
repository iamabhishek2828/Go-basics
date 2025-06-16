package main

import (
	"fmt"
	"time"
)

func sayHello() {
	fmt.Println("Heloo world")
	time.Sleep(100 * time.Millisecond)
}
func sayHi() {
	fmt.Println("Hi")
}
func main() {
	fmt.Println("hello from main")
	go sayHello()
	sayHi()

	time.Sleep(1000 * time.Millisecond)

}
