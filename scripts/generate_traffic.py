import random
import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    plan = ["normal"] * 140 + ["slow"] * 40 + ["error"] * 20
    random.shuffle(plan)

    for kind in plan:
        try:
            if kind == "normal":
                requests.get(f"{BASE_URL}/work", params={"ms": 50})
            elif kind == "slow":
                requests.get(f"{BASE_URL}/work", params={"ms": 500})
            else:
                requests.get(f"{BASE_URL}/error")
        except Exception:
            pass

        time.sleep(random.uniform(0.01, 0.05))


if __name__ == "__main__":
    main()
