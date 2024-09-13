import csv
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import List

import yaml


def run_fio_test(
    name: str,
    filename: Path,
    block_size: str,
    io_depth: int,
    rw_mode: str,
    size: int,
    num_jobs: int,
) -> float:
    """
    Runs an fio benchmark with the specified parameters and returns the average bandwidth (MB/s).

    :param name: Name of the test.
    :param filename: Path to the file being tested.
    :param block_size: Block size to use for the test (e.g., '1M' or '4K').
    :param io_depth: I/O depth.
    :param rw_mode: Read/write mode (e.g., 'read', 'write', 'randread', 'randwrite').
    :param size: Total size of the data to test in bytes.
    :param num_jobs: Number of parallel streams.
    :return: Average bandwidth in MB/s.
    """
    result = subprocess.run(
        [
            "fio",
            "--name",
            name,
            "--filename",
            str(filename),
            "--size",
            str(size),
            "--time_based",
            "--runtime=60s",
            "--ramp_time=2s",
            "--ioengine=libaio",
            "--direct=1",
            "--verify=0",
            "--bs",
            block_size,
            "--iodepth",
            str(io_depth),
            "--rw",
            rw_mode,
            "--numjobs",
            str(num_jobs),
            "--group_reporting",
        ],
        capture_output=True,
        text=True,
    )

    output = result.stdout
    mib_to_mb = float(1024) / float(1000)

    for line in output.splitlines():
        if "BW=" in line:
            bw_value = line.split("BW=")[1].split()[0].replace("/s", "").strip()
            # Check if the bandwidth is in MiB/s and convert to MB/s
            if "MiB" in bw_value:
                bandwidth = float(bw_value.replace("MiB", "").strip()) * mib_to_mb
            elif "MB" in bw_value:
                bandwidth = float(bw_value.replace("MB", "").strip())
            return bandwidth
    return 0.0


def write_csv_test(filepath: Path, size_in_bytes: int) -> float:
    """
    Benchmarking function simulating writing to CSV files.

    :param filepath: Path to the file being written.
    :param size_in_bytes: The size of data to write in bytes.
    :return: Bandwidth used to write the data in MB/s.
    """
    start_time = time.monotonic()
    bytes_written = 0

    with filepath.open("w") as f:
        header = "id,name\n"
        f.write(header)
        bytes_written += len(header)

        i = 0
        while bytes_written < size_in_bytes:
            write_str = f"{i},sample_{i}\n"
            f.write(write_str)
            bytes_written += len(write_str)
            i += 1

    elapsed_time = time.monotonic() - start_time

    # Get the actual file size in bytes for accuracy
    final_size_in_bytes = filepath.stat().st_size
    size_in_mb = final_size_in_bytes / (1024 * 1024)

    return size_in_mb / elapsed_time


def read_csv_test(filepath: Path) -> float:
    """
    Benchmarking function simulating reading from CSV files.

    :param filepath: Path to the file being read.
    :return: Bandwidth used to read the data in MB/s.
    """
    size_in_bytes = filepath.stat().st_size
    start_time = time.monotonic()
    with filepath.open("r") as f:
        for _ in f:
            pass
    elapsed_time = time.monotonic() - start_time
    size_in_mb = size_in_bytes / (1024 * 1024)
    return size_in_mb / elapsed_time


def save_results_to_csv(results: List[tuple], results_file: Path) -> None:
    """
    Saves benchmark results to a CSV file.

    :param results: A list of tuples containing test name, size, run number, and result.
    :param results_file: Path to the CSV file where results will be saved.
    """
    headers = ["Test Type", "Data Size (MB)", "Run", "Result (MB/s)"]

    with results_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(results)


def run_benchmarks(
    test_dir: Path, sizes: List[int], num_runs: int, results_file: Path
) -> None:
    """
    Runs a series of benchmarks using both fio and custom functions, and saves the results to a CSV file.

    :param test_dir: Directory where the test files will be created.
    :param sizes: List of sizes (in bytes) for the tests.
    :param num_runs: Number of times each test will be run.
    :param results_file: Path to the CSV file where results will be saved.
    """
    test_dir.mkdir(exist_ok=True)

    # List to store all results before saving to CSV
    all_results = []

    for size in sizes:
        size_mb = size / 1024**2
        print(f"\nTesting with size: {size_mb:.2f} MB\n")

        for run in range(num_runs):
            print(f"Run {run + 1} of {num_runs}")

            # Sequential write
            write_bw = run_fio_test(
                "sequential_write",
                test_dir / "seq_write_test",
                "1M",
                64,
                "write",
                size,
                4,
            )
            print(f"Sequential Write Bandwidth: {write_bw} MB/s")
            all_results.append(("Sequential Write", size_mb, run + 1, write_bw))

            # Sequential read
            read_bw = run_fio_test(
                "sequential_read", test_dir / "seq_read_test", "1M", 64, "read", size, 4
            )
            print(f"Sequential Read Bandwidth: {read_bw} MB/s")
            all_results.append(("Sequential Read", size_mb, run + 1, read_bw))

            # Random write
            rand_write_bw = run_fio_test(
                "random_write",
                test_dir / "rand_write_test",
                "4K",
                64,
                "randwrite",
                size,
                4,
            )
            print(f"Random Write Bandwidth: {rand_write_bw} MB/s")
            all_results.append(("Random Write", size_mb, run + 1, rand_write_bw))

            # Random read
            rand_read_bw = run_fio_test(
                "random_read",
                test_dir / "rand_read_test",
                "4K",
                64,
                "randread",
                size,
                4,
            )
            print(f"Random Read Bandwidth: {rand_read_bw} MB/s")
            all_results.append(("Random Read", size_mb, run + 1, rand_read_bw))

            # Custom CSV write test
            write_time = write_csv_test(test_dir / f"custom_write_{size}.csv", size)
            print(f"Custom CSV Write Time: {write_time:.2f} seconds")
            all_results.append(("Custom CSV Write", size_mb, run + 1, write_time))

            # Custom CSV read test
            read_time = read_csv_test(test_dir / f"custom_write_{size}.csv")
            print(f"Custom CSV Read Time: {read_time:.2f} seconds")
            all_results.append(("Custom CSV Read", size_mb, run + 1, read_time))

    # Save all results to CSV file
    save_results_to_csv(all_results, results_file)


def check_fio_installed() -> bool:
    """
    Check if 'fio' is installed on the system. If not, attempt to install it.
    :return: True if fio is installed or successfully installed, False otherwise.
    """
    try:
        subprocess.run(
            ["fio", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Fio is not installed. Attempting to install it via apt...")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "fio"], check=True)
            print("Fio was successfully installed.")
            return True
        except subprocess.CalledProcessError:
            print(
                "ERROR: Could not install 'fio'. Please install it manually using 'sudo apt install fio'."
            )
            return False


if __name__ == "__main__":
    if platform.system() != "Linux":
        print("ERROR: This script is only supported on Linux. Exiting.")
        sys.exit(1)

    if not check_fio_installed():
        sys.exit(1)

    CONFIG_FILE = Path(__file__).resolve().parent / "benchmark_config.yaml"

    with open(CONFIG_FILE, "r") as file:
        config = yaml.safe_load(file)

    TEST_HW = config.get("test_hw", "")
    if not TEST_HW:
        print(
            "ERROR: Please specify a hardware identifier in the 'test_hw' field of the config file."
        )
        sys.exit(1)

    TEST_DIR = Path(__file__).resolve().parent / f"hw_benchmark_results_{TEST_HW}"
    TEST_SIZES_MB = config["test_data_sizes_mB"]
    TEST_SIZES = [size_mb * 1024**2 for size_mb in TEST_SIZES_MB]  # Convert MB to bytes
    NUM_RUNS = config["num_runs"]

    # Run benchmarks
    run_benchmarks(TEST_DIR, TEST_SIZES, NUM_RUNS, TEST_DIR / "benchmark_results.csv")
