from __future__ import annotations

"""
Helper class to help extract data from your ADTS
for testing purposes.

You cannot use methods in this file or you will recieve
a 0 for approach and test case marks.

"""
from typing import TypeVar, Union

import ast

from typing import TypeVar, Union

from data_structures.array_set import ArraySet
from data_structures.bit_vector_set import BitVectorSet
from data_structures.array_sorted_list import ArraySortedList
from data_structures.linked_stack import LinkedStack
from data_structures.linked_list import LinkedList
from data_structures.linked_queue import LinkedQueue
from data_structures.referential_array import ArrayR

T = TypeVar('T')

POSSIBLE_ADT_TYPES = Union[
    ArrayR, ArraySet, BitVectorSet, LinkedQueue,
    LinkedList, LinkedStack
]


class CollectionsFinder(ast.NodeVisitor):
    def __init__(self, filename, forbidden_types=None):
        self.filename = filename

        # These will keep track of which class and function we are in
        # so we can ignore certain functions if needed
        self.current_class = None
        self.current_function = None
        self.in_testing = False

        # Holds 4-tuples of (class, function, used type, error message)
        self.failures = []
        self.forbidden_types = forbidden_types or {"list", "set", "dict", "reversed", "sorted"}
        
    def add_failure(self, used_type, message):
        """
        Add a failure to the list of failures.
        """
        if self.in_testing:
            return
        self.failures.append(
            (
                self.current_class,
                self.current_function,
                used_type,
                message,
            )
        )

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        
        # Visit children
        self.generic_visit(node)
        
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        
        # Visit children
        self.generic_visit(node)
        
        self.current_function = old_function
        
    def visit_Assign(self, node: ast.Assign):
        if self.current_function in ("__str__", "__repr__"):
            return
        elif isinstance(node.value, (ast.List, ast.Set, ast.Dict)):
            self.add_failure(
                {
                    ast.List: list,
                    ast.Set: set,
                    ast.Dict: dict,
                }[type(node.value)],
                f"{self.filename} should not use built-in collections, but found usage at line {node.lineno}."
            )

        self.generic_visit(node)
        
    def visit_Call(self, node):
        if self.current_function in ("__str__", "__repr__"):
            return

        # Ignore print function calls
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            return
            
        if isinstance(node.func, ast.Name) and node.func.id in self.forbidden_types:
            self.add_failure(
                {
                    "list": list,
                    "set": set,
                    "dict": dict,
                    "reversed": reversed,
                    "sorted": sorted,
                }[node.func.id],
                f"{self.filename} should not use Python built-ins, but found '{node.func.id}()' at line {node.lineno}.",
            )

        self.generic_visit(node)
    
    def visit_ListComp(self, node: ast.ListComp):
        if "list" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            list,
            f"{self.filename} should not use built-in collections, but found a list comprehension at line {node.lineno}."
        )
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        if "set" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            set,
            f"{self.filename} should not use built-in collections, but found a set comprehension at line {node.lineno}."
        )
        self.generic_visit(node)
    
    def visit_DictComp(self, node: ast.DictComp):
        if "dict" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            dict,
            f"{self.filename} should not use built-in collections, but found a dict comprehension at line {node.lineno}."
        )
        self.generic_visit(node)
    
    def visit_List(self, node: ast.List):
        if "list" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            list,
            f"{self.filename} should not use built-in collections, but found a list at line {node.lineno}."
        )
        self.generic_visit(node)
    
    def visit_Set(self, node: ast.Set):
        if "set" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            set,
            f"{self.filename} should not use built-in collections, but found a set at line {node.lineno}."
        )
        self.generic_visit(node)
    
    def visit_Dict(self, node: ast.Dict):
        if "dict" not in self.forbidden_types or self.current_function in ("__str__", "__repr__"):
            return
        self.add_failure(
            dict,
            f"{self.filename} should not use built-in collections, but found a dict at line {node.lineno}."
        )
        self.generic_visit(node)
    
    def visit_If(self, node):
        try:
            if node.test.comparators[0].value == "__main__":
                self.in_testing = True
                self.generic_visit(node)
                self.in_testing = False
            else:
                self.generic_visit(node)
        except (AttributeError, IndexError):
            self.generic_visit(node)


def take_out_from_adt(adt: POSSIBLE_ADT_TYPES) -> ArrayR[T] | None:
    """
    Take out n elements from the ADT
    """
    if len(adt) == 0:
        return None

    output: ArrayR[T] = ArrayR(len(adt))

    # Some of the below methods mutate the ADT so we will make a copy of the ADT
    adt_type = type(adt)
    if adt_type in [LinkedQueue]:
        for index in range(len(adt)):
            output[index] = adt.serve()
            adt.append(output[index])

    elif adt_type == LinkedStack:
        temp_stack = LinkedStack()
        for index in range(len(adt)):
            output[index] = adt.pop()
            temp_stack.push(output[index])
        
        for index in range(len(temp_stack)):
            adt.push(temp_stack.pop())

    elif adt_type in [LinkedList, ArrayR]:
        for index in range(len(adt)):
            output[index] = adt[index]

    elif adt_type == ArraySortedList:
        for index in range(len(adt)):
            output[index] = adt[index]

    elif adt_type == ArraySet:
        output = adt.values()

    elif adt_type == BitVectorSet:
        output = adt.values()

    else:
        raise ValueError("Invalid ADT type")

    return output


def test_queue() -> None:
    """
    Test the take_out_from_adt function with a queue
    """
    queue: LinkedQueue = LinkedQueue()
    for i in range(1, 11):
        queue.append(i)
    # print(take_out_n_from_adt(queue, 5))
    # Test the queue is not modified
    for i in range(1, 11):
        assert queue.serve() == i, "The queue has been modified"
    print("Queue test passed")

def test_stack() -> None:
    """
    Test the take_out_from_adt function with a stack
    """
    stack: LinkedStack = LinkedStack()
    for i in range(1, 11):
        stack.push(i)
    # print(take_out_n_from_adt(stack, 5))
    # Test the stack is not modified
    for i in range(1, 11):
        assert stack.pop() == 11 - i, "The stack has been modified"
    print("Stack test passed")

def test_linked_list() -> None:
    """
    Test the take_out_from_adt function with a linked list
    """
    linked_list: LinkedList = LinkedList()
    for i in range(1, 11):
        linked_list.append(i)
    # print(take_out_n_from_adt(linked_list, 5))
    # Test the linked list is not modified
    for i in range(0, 10):
        assert linked_list[i] == i + \
            1, f"The linked list has been modified. Expected {i-1}, got {linked_list[i]} at index {i}"
    print("Linked list test passed")

def test_array_sorted_list() -> None:
    """
    Test the take_out_from_adt function with an ArraySortedList
    """
    sorted_list: ArraySortedList[T] = ArraySortedList(11)
    for i in range(1, 11):
        sorted_list.add(i)
    # print(take_out_n_from_adt(linked_list, 5))
    # Test the linked list is not modified
    for i in range(0, 10):
        assert sorted_list[i] == i + \
            1, f"The sorted list has been modified. Expected {i-1}, got {sorted_list[i]} at index {i}"
    print("Sorted list test passed")

def test_arrayR() -> None:
    """
    Test the take_out_from_adt function with an ArrayR
    """
    array: ArrayR[T] = ArrayR(10)
    for i in range(1, 11):
        array[i-1] = i
    # print(take_out_n_from_adt(array, 5))
    # Test the array is not modified
    for i in range(0, 10):
        assert array[i] == i+1, f"The array has been modified. Expected {i-1}, got {array[i]} at index {i}"
    print("ArrayR test passed")


if __name__ == "__main__":
    test_queue()
    test_stack()
    test_linked_list()
    test_array_sorted_list()
    test_arrayR()
