from unittest import TestCase
import ast
import inspect

from tests.helper import CollectionsFinder

from data_structures import ArrayR

from processing_line import Transaction
from fraud_detection import FraudDetection


def to_array(lst):
    """
    Helper function to create an ArrayR from a list.
    """
    lst = [to_array(item) if isinstance(item, list) else item for item in lst]
    return ArrayR.from_list(lst)


def from_array(arr):
    """
    Helper function to convert an ArrayR to a regular list.
    """
    return [from_array(item) if isinstance(item, ArrayR) else item for item in arr]


class TestTask3Setup(TestCase):
    pass
    
class TestTask3(TestTask3Setup):
    def test_simple_operations(self):
        """
        #name(Test the block detection function runs)
        #hurdle
        """
        single_transaction = Transaction(1, "Alice", "Bob")
        single_transaction.signature = "abcde"
        transactions = to_array([single_transaction])
        fraud_detection = FraudDetection(transactions)
        blocks_response = fraud_detection.detect_by_blocks()
        self.assertIsInstance(blocks_response, tuple, "detect_by_blocks should return a tuple.")
        self.assertEqual(len(blocks_response), 2, "detect_by_blocks should return a tuple of two integers.")
        self.assertIsInstance(blocks_response[0], int, "detect_by_blocks should return a tuple of two integers.")
        self.assertIsInstance(blocks_response[1], int, "detect_by_blocks should return a tuple of two integers.")
        self.assertGreater(blocks_response[0], 0, "Block size should be greater than 0.")
        self.assertGreaterEqual(blocks_response[1], 1, "Suspicion score for this example is 1, because there is only one transaction.")



class TestTask3Approach(TestTask3Setup):
    def test_python_built_ins_not_used(self):
        """
        #name(Test built-in collections not used)
        #hurdle
        """
        import fraud_detection
        modules = [fraud_detection]

        for f in modules:
            # Get the source code
            f_source = inspect.getsource(f)
            filename = f.__file__
            
            tree = ast.parse(f_source)
            visitor = CollectionsFinder(filename)
            visitor.visit(tree)
            
            # Report any failures
            for failure in visitor.failures:
                klass, func, used_type, message = failure
                if klass is None and (func is None or (func == 'to_array' and used_type is list)):
                    # Ignore as this it's in the global scope, probably for testing
                    continue
                self.fail(message)

