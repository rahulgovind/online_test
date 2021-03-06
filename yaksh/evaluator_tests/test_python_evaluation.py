from __future__ import unicode_literals
import unittest
import os
import sys
import tempfile
import shutil
from textwrap import dedent

# Local import
from yaksh.grader import Grader
from yaksh.settings import SERVER_TIMEOUT


class EvaluatorBaseTest(unittest.TestCase):
    def assert_correct_output(self, expected_output, actual_output):
        actual_output_as_string = ''.join(actual_output)
        self.assertIn(expected_output, actual_output_as_string)


class PythonAssertionEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.test_case_data = [{"test_case_type": "standardtestcase", "test_case": 'assert(add(1,2)==3)', 'weight': 0.0},
                               {"test_case_type": "standardtestcase", "test_case": 'assert(add(-1,2)==1)', 'weight': 0.0},
                               {"test_case_type": "standardtestcase", "test_case":  'assert(add(-1,-2)==-3)', 'weight': 0.0},
                               ]
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a - b"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output('AssertionError  in:\n assert(add(1,2)==3)',
                        result.get('error')
                      )
        self.assert_correct_output('AssertionError  in:\n assert(add(-1,2)==1)',
                        result.get('error')
                      )
        self.assert_correct_output('AssertionError  in:\n assert(add(-1,-2)==-3)',
                        result.get('error')
                      )

    def test_partial_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn abs(a) + abs(b)"
        test_case_data = [{"test_case_type": "standardtestcase", "test_case": 'assert(add(-1,2)==1)', 'weight': 1.0},
                            {"test_case_type": "standardtestcase", "test_case":  'assert(add(-1,-2)==-3)', 'weight': 1.0},
                            {"test_case_type": "standardtestcase", "test_case": 'assert(add(1,2)==3)', 'weight': 2.0}
                               ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assertEqual(result.get('weight'), 2.0)
        self.assert_correct_output('AssertionError  in:\n assert(add(-1,2)==1)',
                        result.get('error')
                      )
        self.assert_correct_output('AssertionError  in:\n assert(add(-1,-2)==-3)',
                        result.get('error')
                      )

    def test_infinite_loop(self):
        # Given
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(self.timeout_msg, result.get('error'))

    def test_syntax_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b);
            return a + b
        """)
        syntax_error_msg = ["Traceback",
                            "call",
                            "File",
                            "line",
                            "<string>",
                            "SyntaxError",
                            "invalid syntax"
                            ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in syntax_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_indent_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
        return a + b
        """)
        indent_error_msg = ["Traceback", "call",
                            "File",
                            "line",
                            "<string>",
                            "IndentationError",
                            "indented block"
                            ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        err = result.get("error")[0].splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(5, len(err))
        for msg in indent_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_name_error(self):
        # Given
        user_answer = ""
        name_error_msg = ["Traceback",
                          "call",
                          "NameError",
                          "name",
                          "defined"
                          ]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(25, len(err))
        for msg in name_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_recursion_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
            return add(3, 3)
        """)
        recursion_error_msg = ["Traceback", 
                               "maximum recursion depth exceeded"
                               ]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        for msg in recursion_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_type_error(self):
        # Given
        user_answer = dedent("""
        def add(a):
            return a + b
        """)
        type_error_msg = ["Traceback",
                          "call",
                          "TypeError",
                          "argument"
                          ]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(25, len(err))
        for msg in type_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_value_error(self):
        # Given
        user_answer = dedent("""
        def add(a, b):
            c = 'a'
            return int(a) + int(b) + int(c)
        """)
        value_error_msg = ["Traceback",
                           "call",
                           "ValueError",
                           "invalid literal",
                           "base"
                           ]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(28, len(err))
        for msg in value_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_file_based_assert(self):
        # Given
        self.test_case_data = [{"test_case_type": "standardtestcase", "test_case": "assert(ans()=='2')", "weight": 0.0}]
        self.file_paths = [('/tmp/test.txt', False)]
        user_answer = dedent("""
            def ans():
                with open("test.txt") as f:
                    return f.read()[0]
            """)

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_single_testcase_error(self):
        # Given
        """ Tests the user answer with just an incorrect test case """

        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case_type": "standardtestcase",
                             "test_case": 's="abbb"\nasert palindrome(s)==False',
                             "weight": 0.0
                            }
                          ]
        syntax_error_msg = ["Traceback",
                            "call",
                            "File",
                            "line",
                            "<string>",
                            "SyntaxError",
                            "invalid syntax"
                            ]

        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(13, len(err))
        for msg in syntax_error_msg:
            self.assert_correct_output(msg, result.get("error"))


    def test_multiple_testcase_error(self):
        """ Tests the user answer with an correct test case
         first and then with an incorrect test case """
        # Given
        user_answer = "def palindrome(a):\n\treturn a == a[::-1]"
        test_case_data = [{"test_case_type": "standardtestcase",
                             "test_case": 'assert(palindrome("abba")==True)',
                             "weight": 0.0
                            },
                          {"test_case_type": "standardtestcase",
                             "test_case": 's="abbb"\nassert palindrome(S)==False',
                             "weight": 0.0
                            }
                          ]
        name_error_msg = ["Traceback",
                          "call",
                          "NameError",
                          "name 'S' is not defined"
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        error_as_str = ''.join(result.get("error"))
        err = error_as_str.splitlines()

        # Then
        self.assertFalse(result.get("success"))
        self.assertEqual(11, len(err))
        for msg in name_error_msg:
            self.assert_correct_output(msg, result.get("error"))

    def test_unicode_literal_bug(self):
        # Given
        user_answer = dedent("""\
                             def strchar(s):
                                a = "should be a string"
                                return type(a)
                            """)
        test_case_data = [{"test_case_type": "standardtestcase",
                             "test_case": 'assert(strchar("hello")==str)',
                             "weight": 0.0
                            },]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get("success"))


class PythonStdIOEvaluationTestCases(EvaluatorBaseTest):
    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        self.file_paths = None
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path

    def test_correct_answer_integer(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1\n2",
                                "expected_output": "3",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a+b)
                             """
                             )
        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_correct_answer_list(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1,2,3\n5,6,7",
                                "expected_output": "[1, 2, 3, 5, 6, 7]",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                from six.moves import input
                                input_a = input()
                                input_b = input()
                                a = [int(i) for i in input_a.split(',')]
                                b = [int(i) for i in input_b.split(',')]
                                print(a+b)
                             """
                             )

        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_correct_answer_string(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": ("the quick brown fox jumps over the lazy dog\nthe"),
                                "expected_output": "2",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                from six.moves import input
                                a = str(input())
                                b = str(input())
                                print(a.count(b))
                             """
                             )

        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer_integer(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "1\n2",
                                "expected_output": "3",
                                "weight": 0.0
                                }]
        user_answer = dedent("""
                                a = int(input())
                                b = int(input())
                                print(a-b)
                             """
                             )
        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(
            "ERROR:\nExpected:\n3\nGiven:\n-1\n\nError in line 1 of output.",
            result.get('error')
        )

    def test_file_based_answer(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                                "expected_input": "",
                                "expected_output": "2",
                                "weight": 0.0
                                }]
        self.file_paths = [('/tmp/test.txt', False)]

        user_answer = dedent("""
                            with open("test.txt") as f:
                                a = f.read()
                                print(a[0])
                             """
                             )
        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_infinite_loop(self):
        # Given
        self.test_case_data = [{"test_case_type": "stdiobasedtestcase",
                            "expected_input": "1\n2",
                            "expected_output": "3",
                            "weight": 0.0
                            }]
        timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        user_answer = "while True:\n\tpass"

        kwargs = {'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': self.test_case_data
                }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assert_correct_output(timeout_msg, result.get('error'))
        self.assertFalse(result.get('success'))


    def test_unicode_literal_bug(self):
        # Given
        user_answer = dedent("""\
                             a = "this should be a string."
                             print(type(a).__name__)
                            """)
        test_case_data = [{"test_case_type": "stdiobasedtestcase",
                           "expected_input": "",
                           "expected_output": "str",
                           "weight": 0.0
                           }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                }
        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)
        # Then
        self.assertTrue(result.get("success"))


class PythonHookEvaluationTestCases(EvaluatorBaseTest):

    def setUp(self):
        with open('/tmp/test.txt', 'wb') as f:
            f.write('2'.encode('ascii'))
        tmp_in_dir_path = tempfile.mkdtemp()
        self.in_dir = tmp_in_dir_path
        self.timeout_msg = ("Code took more than {0} seconds to run. "
                            "You probably have an infinite loop in"
                            " your code.").format(SERVER_TIMEOUT)
        self.file_paths = None

    def tearDown(self):
        os.remove('/tmp/test.txt')
        shutil.rmtree(self.in_dir)

    def test_correct_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                            )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code,"weight": 1.0
                            }]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))

    def test_incorrect_answer(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a - b"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                            )

        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code,"weight": 1.0
                            }]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output('Incorrect Answer', result.get('error'))

    def test_assert_with_hook(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        assert_test_case = "assert add(1,2) == 3"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a + b" in user_answer:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                            )

        test_case_data = [{"test_case_type": "standardtestcase",
                           "test_case": assert_test_case, 'weight': 1.0},
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code, 'weight': 1.0},
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 2.0)

    def test_multiple_hooks(self):
        # Given
        user_answer = "def add(a,b):\n\treturn a + b"
        hook_code_1 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                if "return a + b" in user_answer:
                                    success, err, mark_fraction = True, "", 0.5
                                return success, err, mark_fraction
                            """
                            )
        hook_code_2 = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                            )


        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code_1, 'weight': 1.0},
                          {"test_case_type": "hooktestcase",
                           "hook_code": hook_code_2, 'weight': 1.0},
                          ]
        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': True,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get("weight"), 1.5)

    def test_infinite_loop(self):
        # Given
        user_answer = "def add(a, b):\n\twhile True:\n\t\tpass"
        hook_code = dedent("""\
                            def check_answer(user_answer):
                                success = False
                                err = "Incorrect Answer"
                                mark_fraction = 0.0
                                exec(user_answer, globals())
                                if add(1,2) == 3:
                                    success, err, mark_fraction = True, "", 1.0
                                return success, err, mark_fraction
                            """
                            )
        test_case_data = [{"test_case_type": "hooktestcase",
                           "hook_code": hook_code,"weight": 1.0
                            }]

        kwargs = {
                  'metadata': {
                    'user_answer': user_answer,
                    'file_paths': self.file_paths,
                    'partial_grading': False,
                    'language': 'python'
                    },
                    'test_case_data': test_case_data,
                  }

        # When
        grader = Grader(self.in_dir)
        result = grader.evaluate(kwargs)

        # Then
        self.assertFalse(result.get('success'))
        self.assert_correct_output(self.timeout_msg, result.get('error'))


if __name__ == '__main__':
    unittest.main()
