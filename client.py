import os
import time
import random
import requests

SERVER = os.getenv("SERVER", "http://localhost:8000")
WORKER_ID = os.getenv(
    "WORKER_ID",
    f"worker-{random.randint(1000, 9999)}"
)


def detect_hardware():
    try:
        import torch

        if torch.cuda.is_available():
            return "gpu", torch.cuda.get_device_name(0)

    except Exception:
        pass

    return "cpu", "CPU"


DEVICE, DEVICE_NAME = detect_hardware()

print(f"Worker: {WORKER_ID}")
print(f"Hardware: {DEVICE_NAME}")


def register():
    requests.post(
        f"{SERVER}/workers",
        json={
            "worker_id": WORKER_ID,
            "device": DEVICE,
            "device_name": DEVICE_NAME
        },
        timeout=10
    )


def calculate(job):
    """
    DEMONSTRATION ONLY.

    This random value is NOT an Alzheimer's prediction
    and must not be interpreted as medical evidence.

    Replace this function with a validated scientific
    computational workload.
    """

    if DEVICE == "gpu":
        time.sleep(1)
    else:
        time.sleep(2)

    return random.random()


register()

while True:
    try:
        response = requests.get(
            f"{SERVER}/jobs/next",
            timeout=10
        )

        job = response.json()["job"]

        if job is None:
            time.sleep(2)
            continue

        print(f"Running {job['job_id']} on {DEVICE}")

        score = calculate(job)

        requests.post(
            f"{SERVER}/results",
            json={
                "job_id": job["job_id"],
                "worker_id": WORKER_ID,
                "score": score
            },
            timeout=10
        )

        print(f"Completed: {score:.4f}")

    except Exception as error:
        print("Error:", error)
        time.sleep(5)

