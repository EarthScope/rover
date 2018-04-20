
from .args import RoverArgumentParser

def main():
    argparse = RoverArgumentParser()
    args = argparse.parse_args()
    print("hello world")
    print(args)