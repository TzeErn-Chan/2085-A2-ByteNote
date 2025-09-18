from unittest import TestCase
import ast
import inspect

from tests.helper import CollectionsFinder

from processing_line import Transaction
from processing_book import ProcessingBook

from data_structures import ArrayR


class TestTask2Setup(TestCase):
    pass


class TestTask2(TestTask2Setup):
    def test_simple_operations(self):
        """
        #name(Test processing book works with 1 transaction)
        #hurdle
        """
        book = ProcessingBook()
        transaction = Transaction(1, "Alice", "Bob")
        transaction.signature = "xxxab"

        book[transaction] = 100
        self.assertEqual(book[transaction], 100)
    


class TestTask2Approach(TestTask2Setup):
    def test_python_built_ins_not_used(self):
        """
        #name(Test built-in collections not used)
        #hurdle
        """
        import processing_book
        modules = [processing_book]

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
    
    def test_book_has_pages(self):
        """
        #name(Test ProcessingBook has the pages attribute)
        #approach
        #score(1)
        """
        book = ProcessingBook()
        self.assertTrue(hasattr(book, "pages"), "ProcessingBook should have a 'pages' attribute.")
        self.assertIsInstance(book.pages, ArrayR, "ProcessingBook 'pages' should be an ArrayR.")

