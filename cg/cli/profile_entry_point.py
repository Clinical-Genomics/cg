import cProfile
import sys
from cg.cli.base import base


def main():
    profiler = cProfile.Profile()

    try:
        profiler.runcall(base)
        profiler.print_stats(sort="cumulative")
    except Exception as e:
        profiler.print_stats(sort="cumulative")


if __name__ == "__main__":
    main()
