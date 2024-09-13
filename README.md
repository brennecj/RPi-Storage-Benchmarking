# RPi-Storage-Benchmarking
A small utility for benchmarking read / write throughput (both sequential and random) of storage medium(s) on a Raspberry Pi running Linux.

## Overview

This Python script performs benchmarking of a storage drive's read and write performance, intedned to be run on a Raspberry Pi 4B. The benchmarking uses both `fio` for synthetic I/O performance tests and custom tests simulating real-world operations like writing and reading CSV files. The results are saved to a CSV file and also printed to the console.

## Installation and Setup

### Prerequisites

Make sure you have the following installed:
- Python 3.x
- `fio` for benchmarking:
    ```bash
    sudo apt-get install fio
    ```
- `pyyaml` for reading the configuration file:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Before running the script, configure the `benchmark_config.yaml` file:

```yaml
test_hw: "RPi_4B_USB_flash_drive"  # Hardware identifier for the test (enter your own)
test_data_sizes_mB: [10, 100, 1000]  # Data sizes to benchmark in MB
num_runs: 1  # Number of runs for each test
```

- `test_hw`: A string identifying the hardware (e.g., "RPi_4B_USB_flash_drive"). This is required to generate the results folder.
- `test_data_sizes_mB`: A list of data sizes in megabytes that will be used in the tests.
- `num_runs`: The number of times each test will be repeated to average the results.

## Running the Benchmark

1. Ensure you have configured the `benchmark_config.yaml` file.
2. Run the benchmark script:
    ```bash
    python run_benchmark.py
    ```

The script will attempt to install `fio` if it is not installed. If the automatic installation fails, you will be prompted to manually install it using:

```bash
sudo apt install fio
```

The results will be saved to `benchmark_results.csv` in a folder named `hw_benchmark_results_<your_test_hw>`.

## Example Output

Example results in `benchmark_results.csv`:
| Test Type         | Data Size (MB) | Run | Result       |
|-------------------|----------------|-----|--------------|
| Sequential Write  | 10.00          | 1   | 50.12 MB/s   |
| Sequential Read   | 10.00          | 1   | 52.34 MB/s   |
| Random Write      | 10.00          | 1   | 1.42 MB/s    |
| Random Read       | 10.00          | 1   | 1.37 MB/s    |
| Custom CSV Write  | 10.00          | 1   | 0.87 seconds |
| Custom CSV Read   | 10.00          | 1   | 0.45 seconds |
