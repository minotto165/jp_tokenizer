package main

import (
	"fmt"
	"log"
	"os"
	"slices"
	"strings"
	"sync"
)

type word struct {
	word  string
	count int
}

func main() {
	// var dictionary = make(map[string]int)
	var dictionary []string

	src, err := os.ReadFile("testdata/wiki.txt")
	if err != nil {
		log.Fatal(err)
	}

	srcStr := string(src)

	text := []rune(srcStr)

	var wg sync.WaitGroup
	var mu sync.Mutex

	srcLength := len(text)

	for i := 0; i < srcLength; i++ {
		wg.Add(1)
		fmt.Println("a")
		go func() {
			word := scan(i, text)
			mu.Lock()
			if !slices.Contains(dictionary, word) {
				dictionary = append(dictionary, word)
			}
			mu.Unlock()
			wg.Done()
		}()

		//fmt.Printf("%v %% Done.\n", float64(i)/float64(srcLength)*100)
	}

	// scan(1, text, &dictionary)
	wg.Wait()
	fmt.Println(dictionary)
}

func scan(idx int, src []rune) string {
	fmt.Println(idx, "started.")
	srcStr := string(src)
	var scores []int //0
	var words []string
	var t string   //""
	var length int //0

	for i := idx; i < len(src); i++ {

		length++
		t = string(src[idx : i+1])        //コ
		count := strings.Count(srcStr, t) //4
		if count > 1 || length == 1 {
			scores = append(scores, length*count*count) //[4]
			words = append(words, t)
			// fmt.Print(t, ":", "長", length, " 数", count, " ,  ")
		}
		fmt.Println(idx, ":", length, "done.")
	}
	// fmt.Println(scores, words)
	// fmt.Println(words[len(scores)-1])

	fmt.Println(idx, "done with", words[len(scores)-1])
	return words[len(scores)-1]

}

// func unique(src *[]string) {
// 	for i, v := range *src {

// 	}
// }
