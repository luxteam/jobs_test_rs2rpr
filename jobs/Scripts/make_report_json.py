import argparse
import os
import json
from shutil import copyfile
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
import jobs_launcher.core.config as config


parser = argparse.ArgumentParser()
parser.add_argument('--work_dir', required=True)

args = parser.parse_args()
directory = args.work_dir

files = os.listdir(directory)
json_files = list(filter(lambda x: x.endswith('RPR.json'), files))
# build report.json if was launched render_or.bat
if not json_files:
    json_files = list(filter(lambda x: x.endswith('RS.json'), files))
result_json = ""

for file in range(len(json_files)):

    if (len(json_files) == 1):
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        result_json += text
        break

    if (file == 0):
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        text = text[:-2]
        text = text + "," + "\r\n"
        result_json += text

    elif (file == (len(json_files))-1):
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        text = text[2:]
        result_json += text

    else:
        f = open(os.path.join(directory, json_files[file]), 'r')
        text = f.read()
        f.close()
        text = text[2:]
        text = text[:-2]
        text = text + "," + "\r\n"
        result_json += text

with open(os.path.join(directory, "report.json"), 'w') as file:
    file.write(result_json)

result_json = json.loads(result_json)

for case in result_json:
    baseline_path_tr = os.path.join(
        'c:/TestResources/rpr_blender_autotests_baselines', args.testType)

    baseline_path = os.path.join(
        directory, os.path.pardir, os.path.pardir, os.path.pardir, 'Baseline', args.testType)

    if not os.path.exists(baseline_path):
        os.makedirs(baseline_path)
        os.makedirs(os.path.join(baseline_path, 'Color'))

    try:
        copyfile(os.path.join(baseline_path_tr, case['case'] + config.CASE_REPORT_SUFFIX),
                    os.path.join(baseline_path, case['case'] + config.CASE_REPORT_SUFFIX))

        with open(os.path.join(baseline_path, case['case'] + config.CASE_REPORT_SUFFIX)) as baseline:
            baseline_json = json.load(baseline)

        for thumb in list(set().union([''], config.THUMBNAIL_PREFIXES)):
            if thumb + 'render_color_path' and os.path.exists(os.path.join(baseline_path_tr, baseline_json[thumb + 'render_color_path'])):
                copyfile(os.path.join(baseline_path_tr, baseline_json[thumb + 'render_color_path']),
                            os.path.join(baseline_path, baseline_json[thumb + 'render_color_path']))
    except:
        config.main_logger.error('Failed to copy baseline ' +
                                        os.path.join(baseline_path_tr, case['case'] + config.CASE_REPORT_SUFFIX))
