import argparse
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="normal")
    args = parser.parse_args()
    request_count = 0

    for raw_line in sys.stdin:
        request_count += 1
        if args.mode == "exit":
            return 7
        if args.mode == "timeout":
            time.sleep(1.0)
            continue
        if args.mode == "malformed":
            print("{not-json", flush=True)
            continue

        request = json.loads(raw_line)
        actions = ["move_left"]
        if args.mode == "hard_drop":
            actions = ["hard_drop"]
        elif args.mode == "illegal_action":
            actions = ["teleport"]

        print(
            json.dumps(
                {
                    "type": "result",
                    "request_id": request["request_id"],
                    "actions": actions,
                    "diagnostics": {
                        "request_count": str(request_count),
                        "active": request["observation"]["active"]["kind"],
                    },
                },
                separators=(",", ":"),
            ),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
