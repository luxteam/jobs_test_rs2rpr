import argparse
import sys
import os
import subprocess
import psutil
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

    if not os.path.exists(args.scene_path):
        main_logger.error("Can't found converted scene")
        report['test_status'] = 'error'
        return 1, report
    if not os.path.exists(args.output_dir):
        main_logger.error("Wasn't found work dir")
        report['test_status'] = 'error'
        return 1, report

    cmd_script = """
    set PATH="C:\\Program Files\\Autodesk\\Maya2018\\bin";%PATH%
    set MAYA_RENDER_DESC_PATH="C:\\Program Files\\AMD\\RadeonProRenderPlugins\\Maya\\renderDesc";%MAYA_RENDER_DESC_PATH%
    "{render_path}" -r FireRender -log "{render_log_path}" -rd "{output_img_dir}" -im {output_file_name} -of {output_file_ext} "{scene_path}"
    """.format(**vars(args))

    cmd_script_path = os.path.join(args.output_dir, 'renderRPR.bat')

    try:
        with open(cmd_script_path, 'w') as file:
            file.write(cmd_script)
        with open(args.render_log_path, 'w') as file:
            pass
    except OSError as err:
        report['test_status'] = 'error'
        main_logger.error(str(err))
        return 1, report
    else:
        rc = -1
        os.chdir(args.output_dir)
        p = psutil.Popen(cmd_script_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        try:
            rc = p.wait()
        except psutil.TimeoutExpired as err:
            rc = -1
            for child in reversed(p.children(recursive=True)):
                child.terminate()
            p.terminate()
        else:
            report['test_status'] = 'passed'

        return rc, report


if __name__ == "__main__":
    args = createArgsParser().parse_args()
    report = {}
    if not os.path.exists(os.path.join(args.output_dir, 'report.json')):
        exit(1)
    with open(os.path.join(args.output_dir, 'report.json'), 'r+') as file:
        report = json.loads(file.read())
    rc, report = main(args, report)
    report['rpr_render_log'] = args.render_log_path
    with open(os.path.join(args.output_dir, 'report_compare.json'), 'w') as file:
        json.dump(report, file, indent=4)
    exit(rc)
