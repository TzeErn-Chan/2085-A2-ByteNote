from unittest import TestCase
import ast
import inspect

from tests.helper import CollectionsFinder


from processing_line import ProcessingLine, Transaction


class TestTask1Setup(TestCase):
    pass


class TestTask1(TestTask1Setup):
    def test_line_basics(self):
        """
        #name(Basic functionality of ProcessingLine)
        #hurdle
        """
        transaction1 = Transaction(50, "alice", "bob")
        transaction2 = Transaction(100, "bob", "dave")
        transaction3 = Transaction(120, "dave", "frank")

        line = ProcessingLine(transaction2)
        line.add_transaction(transaction3)
        line.add_transaction(transaction1)

        line_iterator = iter(line)
        expected_transactions = iter([transaction1, transaction2, transaction3])
        counter = 0
        while True:
            try:
                transaction = next(line_iterator)
                self.assertIsInstance(transaction, Transaction, "Iterator should return Transaction objects.")
                counter += 1
            except StopIteration:
                break

            try:
                self.assertEqual(transaction, next(expected_transactions), "Unexpected transaction returned by iterator.")
            except StopIteration:
                self.fail("Iterator returned more transactions than expected.")
        
        self.assertEqual(counter, 3, "Line iterator should've returned exactly 3 transactions.")
    

class TestTask1Approach(TestTask1Setup):
    def test_python_built_ins_not_used(self):
        """
        #name(Test built-in collections not used)
        #hurdle
        """
        import processing_line
        modules = [processing_line]

        for f in modules:
            # Get the source code
            f_source = inspect.getsource(f)
            filename = f.__file__
            
            tree = ast.parse(f_source)
            visitor = CollectionsFinder(filename)
            visitor.visit(tree)
            
            # Report any failures
            for failure in visitor.failures:
                self.fail(failure[3])
        
