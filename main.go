package main

import (
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

func main() {
	var dictionary = make(map[string]struct{})
	// var dictionary []string

	src, err := os.ReadFile("testdata/wiki.txt")
	if err != nil {
		log.Fatal(err)
	}

	srcStr := string(src)

	srcRunes := []rune(srcStr)

	s := time.Now()

	srcLength := len(srcRunes)

	for i := 0; i < srcLength; i++ {
		wLength, word := scan(i, srcRunes, srcStr)

		if _, ok := dictionary[word]; !ok {
			dictionary[word] = struct{}{}
		}

		i += wLength
		fmt.Printf("%v %% Done.\n", float64(i)/float64(srcLength)*100)
	}

	// scan(10, srcRunes, srcStr)

	fmt.Printf("dictionary generated: %s\n", time.Since(s))

	os.WriteFile("output.txt", render(srcStr, dictionary), 0755)

	fmt.Printf("rendered: %s\n", time.Since(s))

}

func scan(idx int, src []rune, srcStr string) (int, string) {
	// fmt.Println(idx, "started.")
	var scores []int //0
	var words []string
	var t string   //""
	var length int //0
	found := false

	for i := idx; i < len(src) && !found; i++ {

		length++
		t = string(src[idx : i+1])        //コ
		count := strings.Count(srcStr, t) //4
		if count > 1 || length == 1 {
			scores = append(scores, length*length*length*length*length*count) //[4]
			words = append(words, t)
			// fmt.Print(t, ":", "長", length, " 数", count, " ,  ")
		} else {
			found = true
		}
		// fmt.Println(idx, ":", length, "done.")
	}
	fmt.Println(scores, words)
	maxIdx := 0
	for i := 1; i < len(scores); i++ {
		if scores[i] > scores[maxIdx] {
			maxIdx = i
		}
	}
	fmt.Println(idx, "done with", words[maxIdx])
	return maxIdx, words[maxIdx]

}

func render(src string, dictMap map[string]struct{}) []byte {

	srcRunes := []rune(src)
	var result []string

	for i := 0; i < len(srcRunes); {
		found := false
		var l int
		if len(srcRunes)-i < 10 {
			l = len(srcRunes) - i
		} else {
			l = 10
		}

		for length := l; length > 0; length-- {
			target := string(srcRunes[i : i+length])
			if _, ok := dictMap[target]; ok {
				result = append(result, target)
				i += length
				found = true
				break
			}
		}

		if !found {
			result = append(result, string(srcRunes[i]))
			i++
		}
	}

	return []byte(fmt.Sprint(strings.Join(result, "/")))
}

// func unique(src *[]string) {
// 	for i, v := range *src {

// 	}
// }
