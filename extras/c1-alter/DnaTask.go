package main

import (
	"bufio"
	"io"
	"os"
	"time"
)

type DnaTasK struct {
	Id       int
	DnaDir   string
	BeginPos int
	EndPos   int
}
type DnaResult struct {
	Id     int
	Counts map[string]int
}

func (d *DnaTasK) Process(results chan *DnaResult) {
	println("Processing task ", d.Id, " from ", d.BeginPos, " to ", d.EndPos)
	localResult := &DnaResult{Id: d.Id, Counts: map[string]int{"A": 0, "C": 0, "G": 0, "T": 0, "errors": 0}}
	lines := 0
	file, err := os.Open(d.DnaDir)
	if err != nil {
		panic("error opening file")
	}
	defer file.Close()
	reader := bufio.NewReader(file)
	for {
		line, err := reader.ReadString('\n')
		lines++
		if lines < d.BeginPos {
			continue
		}
		if lines >= d.EndPos {
			break
		}
		if line[0] == '<' || line[0] == '>' {
			continue
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			panic("error reading file")
		}
		for _, ch := range line {
			switch ch {
			case 'A':
				localResult.Counts["A"]++
			case 'C':
				localResult.Counts["C"]++
			case 'G':
				localResult.Counts["G"]++
			case 'T':
				localResult.Counts["T"]++
			default:
				localResult.Counts["errors"]++
			}
		}
	}
	time.Sleep(2 * time.Second)
	results <- localResult
}
