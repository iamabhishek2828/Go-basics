package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

type Todo struct {
	UserID    int    `json:"userId"`
	ID        int    `json:"id"`
	Title     string `json:"title"`
	Completed bool   `json:"completed"`
}

func performPostRequest() {
	todo := Todo{
		UserID:    1,
		ID:        1,
		Title:     "Sample Todo",
		Completed: false,
	}

	jsonData, err := json.Marshal(todo)
	if err != nil {
		fmt.Println("error in marshal", err)
		return
	}
	jsonString := string(jsonData)
	jsonReader := strings.NewReader(jsonString)

	myUrl := "https://jsonplaceholder.typicode.com/todos"
	res, err := http.Post(myUrl, "application/json", jsonReader)
	if err != nil {
		fmt.Println("error in post", err)
		return
	}
	defer res.Body.Close()

	fmt.Println("response staus:", res.Status)
}

func main() {
	fmt.Println("starting with crud")
}
