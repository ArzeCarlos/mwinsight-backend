"""
utilities.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script is a collection of classes,functions(utilities) used in the main script

"""
from random import choices
from string import ascii_letters, digits
from argparse import ArgumentParser
from ..includes.defines import THREAD_TYPE_FETCHER, NUM_FETCHERS, NUM_SNMPERS, THREAD_TYPE_SNMPER


class Config(object):
    """
    Configuration class to manage the number of threads for different task types.

    This class allows storing and retrieving the number of threads assigned
    to different types of tasks in the application.
    """
    _threads: dict = {}

    @staticmethod
    def set_thread_num(task_type: str, value: int) -> None:
        """
        Sets the number of threads for a specific task type.

        Args:
            task_type (str): Type of the task (e.g., 'PINGER', 'SNMPPOLLER').
            value (int): Number of threads to be assigned to this task type.
        """
        Config._threads[task_type] = value

    @staticmethod
    def get_thread_num(task_type: str) -> int:
        """
        Gets the number of threads for a specific task type.

        Args:
            task_type (str): The task type to query.

        Returns:
            int: The number of threads assigned, or 0 if the task type is not found.
        """
        return Config._threads.get(task_type, 0)


# Command-line arguments processing
parser = ArgumentParser(description="Configure the number of threads for each task.")
parser.add_argument(
    '-f', '--startfetchers', default=NUM_FETCHERS, type=int,
    help='Number of fetchers threads to launch.'
)
parser.add_argument(
    '-s', '--startsnmpers', default=NUM_SNMPERS, type=int,
    help='Number of snmpers threads to launch.'
)

args = parser.parse_args()

Config.set_thread_num(THREAD_TYPE_FETCHER, args.startfetchers)
Config.set_thread_num(THREAD_TYPE_SNMPER, args.startsnmpers)

# Random ID generator
def random_string(length: int = 8) -> str:
    """
    Generates a random alphanumeric string.

    Args:
        length (int): Length of the generated string (default is 8).

    Returns:
        str: A randomly generated string containing letters and digits.
    """
    return ''.join(choices(ascii_letters + digits, k=length))
