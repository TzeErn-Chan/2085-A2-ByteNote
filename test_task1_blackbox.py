
import math
import random
import re
import unittest

# Import the student's Task 1 module
# Assumes the scaffold has processing_line.py in the import path
from processing_line import Transaction, ProcessingLine

ALNUM36_RE = re.compile(r'^[a-z0-9]+$')

def min_len_for_span(span_target=10**56, alphabet_size=36):
    """Small helper for the test: find the minimal L such that alphabet_size**L >= span_target."""
    L = 1
    power = alphabet_size
    while power < span_target:
        L += 1
        power *= alphabet_size
    return L

class TestTransactionSign(unittest.TestCase):
    def test_signature_properties_and_span(self):
        # Create several different transactions
        txs = [
            Transaction(1, "alice", "bob"),
            Transaction(2, "alice", "bob"),     # different timestamp must change signature
            Transaction(1, "alicex", "bob"),    # different sender must change signature
            Transaction(1, "alice", "bobb"),    # different receiver must change signature
        ]
        # Sign all and collect signatures
        sigs = []
        for t in txs:
            self.assertIsNone(t.signature, "Transactions should start unsigned (signature None).")
            t.sign()
            self.assertIsNotNone(t.signature, "sign() must set a signature.")
            sig = t.signature
            sigs.append(sig)
            # All signatures must be strings, same length, only [a-z0-9]
            self.assertIsInstance(sig, str, "Signature must be a string.")
            self.assertRegex(sig, ALNUM36_RE, "Signature must only contain lowercase letters and digits.")

        # All signatures must have the same length
        lengths = {len(s) for s in sigs}
        self.assertEqual(len(lengths), 1, "All transaction signatures must have the same length.")
        L = lengths.pop()

        # The length must be sufficient to achieve at least 1e56 span with alphabet size 36
        min_L = min_len_for_span(10**56, 36)
        self.assertGreaterEqual(L, min_L, f"Signature length must be >= {min_L} to reach 36^L >= 1e56.")

        # Changing any field should change the signature
        self.assertNotEqual(sigs[0], sigs[1], "Different timestamp must change signature.")
        self.assertNotEqual(sigs[0], sigs[2], "Different sender must change signature.")
        self.assertNotEqual(sigs[0], sigs[3], "Different receiver must change signature.")

    def test_sign_is_deterministic_and_idempotent(self):
        t = Transaction(123456, "satoshi", "hal")
        t.sign()
        first = t.signature
        # Calling sign again should not produce a different signature
        t.sign()
        second = t.signature
        self.assertEqual(first, second, "sign() should be deterministic/idempotent for the same transaction.")

class TestProcessingLine(unittest.TestCase):
    def make_tx(self, ts, a="a", b="b"):
        return Transaction(ts, a, b)

    def assert_all_signed(self, seq):
        for t in seq:
            self.assertIsInstance(t.signature, str, "All yielded transactions must be signed before being returned.")
            self.assertRegex(t.signature, ALNUM36_RE, "Signature must only contain lowercase letters and digits.")

    def test_iteration_order_basic(self):
        # Critical C at time 10
        C = self.make_tx(10, "c", "c2")
        line = ProcessingLine(C)

        # Add mixed transactions around the critical; adding order A3, A2, A4, A1 per spec example
        A3 = self.make_tx(13, "x", "y")
        A2 = self.make_tx(9,  "p", "q")
        A4 = self.make_tx(11, "m", "n")
        A1 = self.make_tx(8,  "u", "v")

        line.add_transaction(A3)
        line.add_transaction(A2)
        line.add_transaction(A4)
        line.add_transaction(A1)

        it = iter(line)
        got = [next(it), next(it), next(it), next(it), next(it)]

        # Expected order: A2, A1, C, A4, A3
        self.assertEqual(got, [A2, A1, C, A4, A3])
        self.assert_all_signed(got)

    def test_equal_timestamp_goes_before(self):
        # Critical time 100; equal timestamps belong to "before/equal" side
        C = self.make_tx(100)
        line = ProcessingLine(C)
        B1 = self.make_tx(100, "a", "b")
        B2 = self.make_tx(50, "c", "d")
        A1 = self.make_tx(150, "e", "f")

        # Add in some order
        line.add_transaction(A1)
        line.add_transaction(B1)
        line.add_transaction(B2)

        # Order inside each side is "more recently added closer to C"
        # before/equal side added order B1 (later), then B2 (earlier) -> iteration gives B1, B2 before C
        # after side only A1 -> appears after C
        got = list(iter(line))
        self.assertEqual(got, [B1, B2, C, A1])
        self.assert_all_signed(got)

    def test_signing_happens_on_the_fly(self):
        C = self.make_tx(10)
        line = ProcessingLine(C)
        T1 = self.make_tx(1)
        T2 = self.make_tx(20)

        line.add_transaction(T1)
        line.add_transaction(T2)

        # Before iteration, none should be signed
        self.assertIsNone(C.signature)
        self.assertIsNone(T1.signature)
        self.assertIsNone(T2.signature)

        it = iter(line)
        first = next(it)
        # First yielded must be signed now, others may still be unsigned until yielded
        self.assertIsNotNone(first.signature)
        # Ensure at least one of the remaining is still unsigned (depends on order)
        remaining = [t for t in (C, T1, T2) if t is not first]
        self.assertTrue(any(t.signature is None for t in remaining), "Transactions should be signed one-by-one upon yielding.")
        # Exhaust iteration and ensure all signed at the end
        rest = list(it)
        for t in [first] + rest:
            self.assertIsNotNone(t.signature)

    def test_lock_after_iteration_starts(self):
        C = self.make_tx(10)
        line = ProcessingLine(C)

        # Start iterating: creating the first iterator should lock the line
        it = iter(line)

        # Attempting to create a second iterator should raise RuntimeError
        with self.assertRaises(RuntimeError):
            iter(line)

        # Attempting to add a transaction after iteration started should raise RuntimeError
        with self.assertRaises(RuntimeError):
            line.add_transaction(self.make_tx(1))

        # We can still iterate with the existing iterator
        collected = list(it)
        self.assertTrue(len(collected) >= 1)
        self.assert_all_signed(collected)

    def test_only_critical_transaction(self):
        C = self.make_tx(999)
        line = ProcessingLine(C)
        got = list(iter(line))
        self.assertEqual(got, [C], "If no other transactions are added, iterator must yield only the critical transaction.")
        self.assert_all_signed(got)

    def test_multiple_waves_of_additions_before_iter(self):
        # Build a more complex scenario with waves of additions (but still before iteration)
        C = self.make_tx(100)
        line = ProcessingLine(C)

        before = [self.make_tx(ts) for ts in (10, 20, 50, 100)]  # <= C
        after  = [self.make_tx(ts) for ts in (101, 150, 200)]    # > C

        # Add some, then some more
        for t in [after[0], before[0], after[1], before[1], before[2], after[2], before[3]]:
            line.add_transaction(t)

        # Expected order:
        # - "before/equal" side appears in reverse of insertion order among those <=100
        #   We added: before[0](10), before[1](20), before[2](50), before[3](100) in that order
        #   So before-side iteration: before[3], before[2], before[1], before[0]
        # - then C
        # - "after" side in reverse insertion order among those >100
        #   We added: after[0](101), after[1](150), after[2](200) -> iteration: after[2], after[1], after[0]
        expected = [before[3], before[2], before[1], before[0], C, after[2], after[1], after[0]]
        got = list(iter(line))
        self.assertEqual(got, expected)
        self.assert_all_signed(got)


if __name__ == "__main__":
    # Allow running directly: python tests/test_task1_blackbox.py
    unittest.main()
