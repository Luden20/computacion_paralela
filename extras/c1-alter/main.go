package main

import (
	"runtime"
	"time"
)

// TIP <p>To run your code, right-click the code and select <b>Run</b>.</p> <p>Alternatively, click
// the <icon src="AllIcons.Actions.Execute"/> icon in the gutter and select the <b>Run</b> menu item from here.</p>
func main() {
	startTime := time.Now()
	cores := runtime.NumCPU()
	runtime.GOMAXPROCS(cores)
	wp := WorkerPool{DnaDir: "C:\\DevStuff\\University\\computaion_paralela\\colaborativo1\\GCF_000001405.40_GRCh38.p14_genomic.fna", Concurrency: cores}
	wp.Prepare()
	wp.Start()
	res := wp.ConsolidateResults()
	elapsed := time.Since(startTime)
	println(elapsed/time.Second, "s time taken")
	println(res.Counts["A"])
}
