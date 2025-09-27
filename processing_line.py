from data_structures.linked_stack import LinkedStack


class Transaction:
    _SIGNATURE_LENGTH = 36
    _SIGNATURE_BASE = 36
    _SIGNATURE_MODULUS = 36 ** _SIGNATURE_LENGTH
    _DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
    _SEED = 1469598103934665603
    _MULTIPLIER_A = 11400714819323198485
    _MULTIPLIER_B = 1099511628211

    def __init__(self, timestamp, from_user, to_user):
        self.timestamp = timestamp
        self.from_user = from_user
        self.to_user = to_user
        self.signature = None
    
    def sign(self):
        """
        Time complexity:
        best: O(u + v + t), where u = len(self.from_user), v = len(self.to_user), and t is the digit count of `timestamp` when rendered as a string.
        worst: O(u + v + t), with u, v, and t defined as above for the same transaction.

        Justification: We fold each character of the sender and receiver names
        and every digit of the timestamp string exactly once into a rolling
        36-bit style hash, guaranteeing a 36-character base-36 signature. The
        fixed-length signature (36^36 span) ensures negligible collision risk
        while the rolling hash never stores the raw data beyond the running
        integer.
        """
        hashed_value = Transaction._SEED ^ self.timestamp
        hashed_value *= Transaction._MULTIPLIER_A

        hashed_value ^= len(self.from_user) << 8
        hashed_value *= Transaction._MULTIPLIER_B

        for char in self.from_user:
            hashed_value ^= ord(char)
            hashed_value *= Transaction._MULTIPLIER_A
            hashed_value += Transaction._MULTIPLIER_B

        timestamp_str = str(self.timestamp)
        for char in timestamp_str:
            hashed_value ^= ord(char) << 4
            hashed_value *= Transaction._MULTIPLIER_B
            hashed_value += Transaction._MULTIPLIER_A

        hashed_value ^= len(self.to_user) << 16
        hashed_value *= Transaction._MULTIPLIER_A

        for char in self.to_user:
            hashed_value ^= ord(char)
            hashed_value *= Transaction._MULTIPLIER_B
            hashed_value += Transaction._MULTIPLIER_A

        hashed_value %= Transaction._SIGNATURE_MODULUS

        signature = ""
        value = hashed_value
        if value == 0:
            signature = "0"
        else:
            while value > 0:
                remainder = value % Transaction._SIGNATURE_BASE
                value = value // Transaction._SIGNATURE_BASE
                signature = Transaction._DIGITS[remainder] + signature

        while len(signature) < Transaction._SIGNATURE_LENGTH:
            signature = "0" + signature

        self.signature = signature


class ProcessingLine:
    def __init__(self, critical_transaction):
        """
        Time complexity:
        best: O(1), where the bound is constant regardless of stored transactions.
        worst: O(1), under the same constant bound.

        Justification: Dedicated stacks partition the pre-critical and
        post-critical transactions, with the former kept in timestamp-sorted
        order and the latter operating as a simple LIFO buffer, preventing
        external random access.
        """
        self._critical_transaction = critical_transaction
        self._before_stack = LinkedStack()
        self._after_stack = LinkedStack()
        self._locked = False

    def add_transaction(self, transaction):
        """
        Time complexity:
        best: O(1), because inserting ahead of smaller timestamps requires no
        reordering.
        worst: O(b), where b is the number of stored pre-critical transactions
        (all of which might be cycled through to maintain timestamp order).

        Justification: Pre-critical transactions are kept on a stack sorted by
        timestamp so that closer timestamps appear nearer to the critical item,
        while post-critical transactions remain in a simple LIFO buffer.
        """
        if self._locked:
            raise RuntimeError("Processing line locked during iteration")

        if transaction.timestamp <= self._critical_transaction.timestamp:
            buffer = LinkedStack()
            while len(self._before_stack) > 0 and \
                    self._before_stack.peek().timestamp >= transaction.timestamp:
                buffer.push(self._before_stack.pop())

            self._before_stack.push(transaction)

            while len(buffer) > 0:
                self._before_stack.push(buffer.pop())
        else:
            self._after_stack.push(transaction)

    def __iter__(self):
        """
        Time complexity:
        best: O(1), as returning the iterator toggles a flag only.
        worst: O(1), identical constant work.

        Justification: Producing the iterator simply flips the processing lock
        and hands back a lightweight iterator object without touching the stored
        transactions.
        """
        if self._locked:
            raise RuntimeError("Processing line already processing")

        self._locked = True
        return _ProcessingLineIterator(self)


class _ProcessingLineIterator:
    def __init__(self, processing_line):
        self._processing_line = processing_line

    def __iter__(self):
        return self

    def __next__(self):
        """
        Time complexity:
        best: O(1), when the transaction already carries a signature.
        worst: O(1 + s), where s = u + v + t for the transaction being signed (see `sign`).
        
        Justification: Serving from the before-stack or after-stack is constant time thanks to
        their linked implementations; if the transaction is unsigned we incur an
        extra O(s) call to `sign`, where s covers the combined identifier
        lengths.
        """
        before_stack = self._processing_line._before_stack
        after_stack = self._processing_line._after_stack

        if len(before_stack) > 0:
            transaction = before_stack.pop()
        elif self._processing_line._critical_transaction is not None:
            transaction = self._processing_line._critical_transaction
            self._processing_line._critical_transaction = None
        elif len(after_stack) > 0:
            transaction = after_stack.pop()
        else:
            raise StopIteration

        if transaction.signature is None:
            transaction.sign()

        return transaction


if __name__ == "__main__":
    # Write tests for your code here...
    # We are not grading your tests, but we will grade your code with our own tests!
    # So writing tests is a good idea to ensure your code works as expected.
    
    # Here's something to get you started...
    transaction1 = Transaction(50, "alice", "bob")
    transaction2 = Transaction(100, "bob", "dave")
    transaction3 = Transaction(120, "dave", "frank")

    line = ProcessingLine(transaction2)
    line.add_transaction(transaction3)
    line.add_transaction(transaction1)

    print("Let's print the transactions... Make sure the signatures aren't empty!")
    line_iterator = iter(line)
    while True:
        try:
            transaction = next(line_iterator)
            print(f"Processed transaction: {transaction.from_user} -> {transaction.to_user}, "
                  f"Time: {transaction.timestamp}\nSignature: {transaction.signature}")
        except StopIteration:
            break
