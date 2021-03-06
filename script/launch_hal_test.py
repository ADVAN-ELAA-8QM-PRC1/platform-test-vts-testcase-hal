#!/usr/bin/env python
#
# Copyright 2017 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import os
import re
import sys

from build.vts_spec_parser import VtsSpecParser
from configure.test_case_creator import TestCaseCreator

HAL_PACKAGE_PREFIX = 'android.hardware.'
HAL_PACKAGE_NAME_PATTERN = '(([a-zA-Z_0-9]*)(?:[.][a-zA-Z_0-9]*)*)@([0-9]+)[.]([0-9]+)'
TEST_TIME_OUT_PATTERN = '(([0-9]+)(m|s|h))+'
"""Generate Android.mk and AndroidTest.xml files for given hal

Usage:
  python launch_hal_test.py [--test_type=host/target] [--time_out=estimated_test_time] [--enable_profiling] hal_package name

Example:
  python launch_hal_test.py android.hardware.nfc@1.0
  python launch_hal_test.py --enable_profiling android.hardware.nfc@1.0
  python launch_hal_test.py --test_type=host --time_out=5m android.hardware.nfc@1.0
"""


def main():
    parser = argparse.ArgumentParser(description='Initiate a test case.')
    parser.add_argument(
        '--test_type',
        dest='test_type',
        required=False,
        help='Test type, such as HidlHalTest, HostDrivenTest, etc.')
    parser.add_argument(
        '--time_out',
        dest='time_out',
        required=False,
        help='Timeout for the test, default is 1m.')
    parser.add_argument(
        '--enable_profiling',
        dest='enable_profiling',
        action='store_true',
        required=False,
        help='Whether to create profiling test.')
    parser.add_argument(
        '--replay',
        dest='is_replay',
        action='store_true',
        required=False,
        help='Whether this is a replay test.')
    parser.add_argument(
        '--disable_stop_runtime',
        dest='disable_stop_runtime',
        action='store_true',
        required=False,
        help='Whether to stop framework before the test.')
    parser.add_argument(
        'hal_package_name',
        help='hal package name (e.g. android.hardware.nfc@1.0).')
    args = parser.parse_args()

    regex = re.compile(HAL_PACKAGE_NAME_PATTERN)
    result = re.match(regex, args.hal_package_name)
    if not result:
        print 'Invalid hal package name. Exiting..'
        sys.exit(1)
    if not args.hal_package_name.startswith(HAL_PACKAGE_PREFIX):
        print 'hal package name does not start with android.hardware. Exiting...'
        sys.exit(1)

    if not args.test_type:
        args.test_type = 'target'
    elif args.test_type != 'target' and args.test_type != 'host':
        print 'Unsupported test type. Exiting...'
        sys.exit(1)
    elif args.test_type == 'host' and args.is_replay:
        print 'Host side replay test is not supported yet. Exiting...'
        sys.exit(1)

    if not args.time_out:
        args.time_out = '1m'
    else:
        regex = re.compile(TEST_TIME_OUT_PATTERN)
        result = re.match(regex, args.time_out)
        if not result:
            print 'Invalid test time out format. Exiting...'
            sys.exit(1)

    stop_runtime = False
    if args.test_type == 'target' and not args.disable_stop_runtime:
        stop_runtime = True

    vts_spec_parser = VtsSpecParser()
    test_case_creater = TestCaseCreator(vts_spec_parser, args.hal_package_name)
    if not test_case_creater.LaunchTestCase(
            args.test_type,
            args.time_out,
            is_replay=args.is_replay,
            stop_runtime=stop_runtime):
        print('Error: Failed to launch test for %s. Exiting...' %
              args.hal_package_name)
        sys.exit(1)

    # Create additional profiling test case if enable_profiling is specified.
    if (args.enable_profiling):
        if not test_case_creater.LaunchTestCase(
                args.test_type,
                args.time_out,
                is_replay=args.is_replay,
                is_profiling=True,
                stop_runtime=stop_runtime):
            print('Error: Failed to launch profiling test for %s. Exiting...' %
                  args.hal_package_name)
            sys.exit(1)


if __name__ == '__main__':
    main()
