import concurrent.futures
import json
import subprocess
import threading
import time
import urllib.request

URL = "http://localhost:8003/pickup"

DURATION = 10

stats_samples = []
stop_monitor = False


def monitor_docker():
    while not stop_monitor:
        try:
            result = subprocess.run(
                [
                    "docker", "stats", "--no-stream",
                    "--format",
                    "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}"
                ],
                capture_output=True,
                text=True
            )

            for line in result.stdout.strip().splitlines():
                if line:
                    stats_samples.append(line)

        except Exception:
            pass

        time.sleep(0.5)


def send_request():
    data = json.dumps({
        "parcel_id": 1,
        "student_id": 1
    }).encode()

    request = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()

        end = time.perf_counter()

        return end - start, True

    except Exception:
        end = time.perf_counter()
        return end - start, False


def run_test(concurrency):
    global stop_monitor
    stats_samples.clear()
    stop_monitor = False

    monitor_thread = threading.Thread(target=monitor_docker)
    monitor_thread.start()

    results = []
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        while time.perf_counter() - start_time < DURATION:
            futures = [
                executor.submit(send_request)
                for _ in range(concurrency)
            ]

            for future in futures:
                results.append(future.result())

    stop_monitor = True
    monitor_thread.join()

    total_time = time.perf_counter() - start_time

    response_times = [r[0] for r in results]
    successful = sum(1 for r in results if r[1])
    failed = len(results) - successful

    average_response = (
        sum(response_times) / len(response_times)
        if response_times else 0
    )

    throughput = successful / total_time

    print()
    print("====================================")
    print(f"Concurrent Requests : {concurrency}")
    print(f"Total Requests      : {len(results)}")
    print(f"Successful          : {successful}")
    print(f"Failed              : {failed}")
    print(f"Avg Response Time   : {average_response:.4f} seconds")
    print(f"Throughput          : {throughput:.2f} requests/sec")
    print("====================================")

    print()
print("Peak Docker resources during test:")
print()

resource_data = {}

for sample in stats_samples:
    parts = sample.split("|")

    if len(parts) != 3:
        continue

    name = parts[0]
    cpu_text = parts[1].replace("%", "").strip()
    memory_text = parts[2].split("/")[0].strip()

    try:
        cpu = float(cpu_text)
    except ValueError:
        continue

    try:
        if "MiB" in memory_text:
            memory = float(memory_text.replace("MiB", "").strip())
        elif "GiB" in memory_text:
            memory = float(memory_text.replace("GiB", "").strip()) * 1024
        else:
            continue
    except ValueError:
        continue

    if name not in resource_data:
        resource_data[name] = {"cpu": 0, "memory": 0}

    resource_data[name]["cpu"] = max(
        resource_data[name]["cpu"], cpu
    )

    resource_data[name]["memory"] = max(
        resource_data[name]["memory"], memory
    )

for name, values in resource_data.items():
    print(
        f"{name}: "
        f"Peak CPU={values['cpu']:.2f}% | "
        f"Peak Memory={values['memory']:.2f} MiB"
    )


print("Campus Parcel Management Load Test")
print("Target:", URL)
print("Duration:", DURATION, "seconds")

run_test(16)
print()
print("Peak Docker resources during test:")
print()

resource_data = {}

for sample in stats_samples:
    parts = sample.split("|")

    if len(parts) != 3:
        continue

    name = parts[0]
    cpu_text = parts[1].replace("%", "").strip()
    memory_text = parts[2].split("/")[0].strip()

    try:
        cpu = float(cpu_text)
    except ValueError:
        continue

    try:
        if "MiB" in memory_text:
            memory = float(memory_text.replace("MiB", "").strip())
        elif "GiB" in memory_text:
            memory = float(memory_text.replace("GiB", "").strip()) * 1024
        else:
            continue
    except ValueError:
        continue

    if name not in resource_data:
        resource_data[name] = {"cpu": 0, "memory": 0}

    resource_data[name]["cpu"] = max(
        resource_data[name]["cpu"], cpu
    )

    resource_data[name]["memory"] = max(
        resource_data[name]["memory"], memory
    )

for name, values in resource_data.items():
    print(
        f"{name}: "
        f"Peak CPU={values['cpu']:.2f}% | "
        f"Peak Memory={values['memory']:.2f} MiB"
    )
