import shutil
import argparse


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--original_scene', required=True)
    argparser.add_argument('--converted_scene', required=True)
    args = argparser.parse_args()

    # TODO: implement conversion
    shutil.copyfile(args.original_scene, args.converted_scene)


if __name__ == '__main__':
    main()
