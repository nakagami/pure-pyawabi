import sys
from argparse import ArgumentParser
from . import tokenizer

def main():
    parser = ArgumentParser()
    parser.add_argument('-N', '--nbest', type=int)
    args = parser.parse_args()

    t = tokenizer.Tokenizer()
    for s in sys.stdin.readlines():
        if args.nbest:
            for tokens in t.tokenize_n_best(s, args.nbest):
                for token in tokens:
                    print("{}	{}".format(token[0], token[1]))
                print("EOS")
        else:
            for token in t.tokenize(s):
                print("{}	{}".format(token[0], token[1]))
            print("EOS")

