import pytest


if __name__ == '__main__':
    # pytest.main(['-v', '-m smoke', './testcases', '--html=./report/report.html'])
    # python -m pytest  -vs -m smoke

    casefile_list = [
        'testcases/test_class_demo.py',
        'testcases/u2_cases/test_class_demo2.py'
    ]
    pytest.main(['-v', '-m smoke', *casefile_list, '--html=./report/report.html'])