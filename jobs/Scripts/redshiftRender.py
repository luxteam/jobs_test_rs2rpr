import argparse
import sys
import os
import subprocess
import psutil
import datetime
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from jobs_launcher.core.config import main_logger


def createArgsParser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--render_path', required=True, metavar="<path>")
    parser.add_argument('--scene_path', required=True, metavar="<path")
    parser.add_argument('--render_log_path', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--output_img_dir', required=True)
    parser.add_argument('--output_file_name', required=True)
    parser.add_argument('--output_file_ext', required=True)
    return parser


def main(args, report):
    try:
        os.makedirs(args.output_img_dir)
    except OSError as err:
        main_logger.error(str(err))
        report['test_status'] = 'error'
        return 1, report

    cmd_script = '"{render_path}" -r redshift -log "{render_log_path}" -rd "{output_img_dir}" -im {output_file_name} -of {output_file_ext} "{scene_path}"'.format(**vars(args))
    cmd_script_path = os.path.join(args.output_dir, 'renderRedshift.bat')

    try:
        with open(cmd_script_path, 'w') as file:
            file.write(cmd_script)
        with open(args.render_log_path, 'w') as file:
            pass
    except OSError as err:
        main_logger.error(str(err))
        report['test_status'] = 'error'
        return 1, report
    else:
        rc = -1
        os.chdir(args.output_dir)
        p = psutil.Popen(cmd_script_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        try:
            rc = p.wait()
        except psutil.TimeoutExpired as err:
            main_logger.error("Terminated by timeout")
            report['test_status'] = 'error'
            rc = -1
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        return rc, report


if __name__ == "__main__":
    args = createArgsParser().parse_args()
    report = {"datetime": datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
              "scene_name": os.path.basename(args.scene_path),
              "test_status": "works",
              "redshift_render_log": os.path.basename(args.render_log_path),
              }
    rc, report = main(args, report)

    with open(os.path.join(args.output_dir, 'report.json'), 'w') as file:
        json.dump(report, file, indent=4)

    exit(rc)
