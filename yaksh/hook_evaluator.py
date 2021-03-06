#!/usr/bin/env python
import sys
import traceback
import os

# Local imports
from .file_utils import copy_files, delete_files
from .base_evaluator import BaseEvaluator
from .grader import TimeoutException


class HookEvaluator(BaseEvaluator):
    def __init__(self, metadata, test_case_data):
        self.files = []

        # Set metadata values
        self.user_answer = metadata.get('user_answer')
        self.file_paths = metadata.get('file_paths')
        self.partial_grading = metadata.get('partial_grading')

        # Set test case data values
        self.hook_code = test_case_data.get('hook_code')
        self.weight = test_case_data.get('weight')

    def teardown(self):
        # Delete the created file.
        if self.files:
            delete_files(self.files)

    def check_code(self):
        """ Function evaluates user answer by running a python based hook code
        against it.
        Returns
        --------
        Returns a tuple (success, error, test_case_weight)

        success - Boolean, indicating if code was executed successfully, correctly
        mark_fraction - Float, indicating fraction of the weight to a test case
        error - String, error message if success is false

        returns (True, "Correct answer", 1.0) : If the student script passes all
        test cases/have same output, when compared to the instructor script

        returns (False, error_msg, 0.0): If the student script fails a single
        test/have dissimilar output, when compared to the instructor script.

        Returns (False, error_msg, 0.0): If mandatory arguments are not files or if
        the required permissions are not given to the file(s).
        """
        success = False
        mark_fraction = 0.0
        try:
            tb = None
            _tests = compile(self.hook_code, '<string>', mode='exec')
            hook_scope = {}
            exec(_tests, hook_scope)
            check = hook_scope["check_answer"]
            success, err, mark_fraction = check(self.user_answer)
        except TimeoutException:
            raise
        except Exception:
            msg = traceback.format_exc(limit=0)
            err = "Error in Hook code: {0}".format(msg)
        del tb
        return success, err, mark_fraction
 