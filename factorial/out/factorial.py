#!/usr/bin/env python3
import sys


def factorial(n: int) -> int:
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0] if argv else 'factorial'} <n>", file=sys.stderr)
        return 2

    try:
        n = int(argv[1])
    except ValueError:
        print(f"error: '{argv[1]}' is not an integer", file=sys.stderr)
        return 2

    if n < 0:
        print(f"error: n must be >= 0, got {n}", file=sys.stderr)
        return 1

    print(factorial(n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
