package main

import (
	"bufio"
	"io"
	"os"
	"sync"
)

type WorkerPool struct {
	Tasks       []DnaTasK
	DnaDir      string
	Concurrency int
	TaskChan    chan DnaTasK
	Results     chan *DnaResult
	FinalResult DnaResult
	Wg          sync.WaitGroup
}

func (wp *WorkerPool) countLines() (*int, *error) {
	lines := 0
	file, err := os.Open(wp.DnaDir)
	if err != nil {
		panic("error opening file")
	}
	defer file.Close()
	reader := bufio.NewReader(file)
	for {
		_, err := reader.ReadString('\n')
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, &err
		}
		lines++
	}
	return &lines, nil
}
func (wp *WorkerPool) Prepare() {
	lines, err := wp.countLines()
	if err != nil {
		panic("error counting lines")
	}
	linesPerChunk := *lines / wp.Concurrency
	begin := 0
	end := linesPerChunk
	for i := 0; i < wp.Concurrency-1; i++ {
		newTask := DnaTasK{
			Id:       i,
			DnaDir:   wp.DnaDir,
			BeginPos: begin,
			EndPos:   end,
		}
		begin = begin + linesPerChunk
		end = end + linesPerChunk
		wp.Tasks = append(wp.Tasks, newTask)
	}
	wp.Tasks = append(wp.Tasks, DnaTasK{
		Id:       wp.Concurrency - 1,
		DnaDir:   wp.DnaDir,
		BeginPos: begin,
		EndPos:   *lines + 1,
	})
}
func (wp *WorkerPool) Worker() {
	for task := range wp.TaskChan {
		task.Process(wp.Results)
		wp.Wg.Done()
	}
}
func (wp *WorkerPool) ConsolidateResults() DnaResult {
	wp.FinalResult = DnaResult{
		Counts: make(map[string]int),
	}
	wp.FinalResult.Counts["A"] = 0
	wp.FinalResult.Counts["C"] = 0
	wp.FinalResult.Counts["G"] = 0
	wp.FinalResult.Counts["T"] = 0
	wp.FinalResult.Counts["errors"] = 0

	for result := range wp.Results {
		wp.FinalResult.Counts["A"] += result.Counts["A"]
		wp.FinalResult.Counts["C"] += result.Counts["C"]
		wp.FinalResult.Counts["G"] += result.Counts["G"]
		wp.FinalResult.Counts["T"] += result.Counts["T"]
		wp.FinalResult.Counts["errors"] += result.Counts["errors"]
	}
	return wp.FinalResult
}
func (wp *WorkerPool) Start() {
	wp.TaskChan = make(chan DnaTasK, len(wp.Tasks))
	wp.Results = make(chan *DnaResult, len(wp.Tasks))
	for i := 0; i < wp.Concurrency; i++ {
		go wp.Worker()
	}
	wp.Wg.Add(len(wp.Tasks))
	for _, task := range wp.Tasks {
		wp.TaskChan <- task
	}
	close(wp.TaskChan)
	wp.Wg.Wait()
	close(wp.Results)

}
