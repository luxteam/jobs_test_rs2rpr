set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set PYTHONPATH=..\jobs_launcher\;%PYTHONPATH%

python ..\jobs_launcher\common\scripts\generate_baselines.py --results_root ..\Work\Results\rs2rpr --baseline_root ..\Work\Baseline --case_suffix _RS.json