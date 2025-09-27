
import unittest
import re

from processing_line import Transaction
from processing_book import ProcessingBook

ALNUM36_RE = re.compile(r'^[a-z0-9]+$')

def tx(sig, ts=1, s='a', r='b'):
    """Create a Transaction with a forced signature (Task 2 assumes signatures are already set)."""
    t = Transaction(ts, s, r)
    t.signature = sig
    return t

# Helper: custom lexicographic order where letters a-z come before digits 0-9 at every position
def lex36_key(sig):
    def char_key(c):
        if 'a' <= c <= 'z':
            return ord(c) - ord('a')  # 0..25
        return 26 + (ord(c) - ord('0'))  # 26..35
    return tuple(char_key(c) for c in sig)

class TestProcessingBookBasic(unittest.TestCase):
    def test_set_get_single_no_collision(self):
        book = ProcessingBook()
        t1 = tx("abc123")
        book[t1] = 10
        self.assertEqual(book[t1], 10)
        self.assertEqual(len(book), 1)

    def test_collision_recursive_insert_and_get(self):
        book = ProcessingBook()
        t1 = tx("abc123", ts=10)
        t2 = tx("abcxyz", ts=11)
        t3 = tx("abcyzz", ts=12)  # collides first two letters then diverges later

        book[t1] = 10
        book[t2] = 20
        book[t3] = 30

        self.assertEqual(book[t1], 10)
        self.assertEqual(book[t2], 20)
        self.assertEqual(book[t3], 30)
        self.assertEqual(len(book), 3)

    def test_setting_same_amount_is_ok_but_different_increments_error(self):
        book = ProcessingBook()
        t = tx("aaaa")
        book[t] = 5
        self.assertEqual(book.get_error_count(), 0)

        # Setting same amount should be a no-op and not count as error
        book[t] = 5
        self.assertEqual(book[t], 5)
        self.assertEqual(book.get_error_count(), 0)

        # Setting different amount should not change value but increment error counter
        book[t] = 7
        self.assertEqual(book[t], 5)
        self.assertEqual(book.get_error_count(), 1)

    def test_missing_key_raises(self):
        book = ProcessingBook()
        t = tx("zzzz")
        with self.assertRaises(KeyError):
            _ = book[t]

class TestProcessingBookDeletion(unittest.TestCase):
    def test_delete_and_collapse(self):
        book = ProcessingBook()
        t1 = tx("abc123", ts=1)
        t2 = tx("abcxyz", ts=2)
        t3 = tx("abcyzz", ts=3)

        book[t1] = 10
        book[t2] = 20
        book[t3] = 30

        # Delete one and ensure remaining are accessible
        del book[t1]
        self.assertEqual(len(book), 2)
        with self.assertRaises(KeyError):
            _ = book[t1]
        self.assertEqual(book[t2], 20)
        self.assertEqual(book[t3], 30)

        # Delete another; structure should collapse further but access must still work
        del book[t2]
        self.assertEqual(len(book), 1)
        self.assertEqual(book[t3], 30)

        # Delete last -> empty
        del book[t3]
        self.assertEqual(len(book), 0)
        with self.assertRaises(KeyError):
            _ = book[t3]

class TestProcessingBookIteration(unittest.TestCase):
    def test_iter_returns_tuples_in_sorted_page_order(self):
        book = ProcessingBook()
        # Mix letters/digits, same length
        pairs = [
            ("aab0", 12),
            ("aaa0", 20),
            ("bbb1", 83),
            ("babb", 14),
            ("aaaa", 57),
            ("0zzz", 3),
            ("z000", 8),
            ("9abc", 99),
        ]
        txs = [tx(sig, ts=i+1) for i, (sig, _) in enumerate(pairs)]
        for t, (_, amt) in zip(txs, pairs):
            book[t] = amt

        # Expected lexicographic (letters before digits) by full signature
        expected_sigs = sorted([sig for sig, _ in pairs], key=lex36_key)
        got = list(iter(book))
        # Validate shape and ordering by signature
        got_sigs = [t.signature for (t, amt) in got]
        self.assertEqual(got_sigs, expected_sigs)

        # Validate tuple content and amounts map back correctly
        amounts_by_sig = {sig: amt for sig, amt in pairs}
        for t, amt in got:
            self.assertEqual(amt, amounts_by_sig[t.signature])
            self.assertRegex(t.signature, r'^[a-z0-9]+$')

    def test_len_reflects_current_count(self):
        book = ProcessingBook()
        t1, t2, t3 = tx("a000"), tx("a001"), tx("b000")
        for t, v in ((t1, 1), (t2, 2), (t3, 3)):
            book[t] = v
        self.assertEqual(len(book), 3)
        del book[t2]
        self.assertEqual(len(book), 2)
        del book[t1]
        self.assertEqual(len(book), 1)

class TestProcessingBookSamplingOptional(unittest.TestCase):
    def test_sampling_optional(self):
        # Only run if sample method exists (FIT1054 only)
        if not hasattr(ProcessingBook, 'sample'):
            self.skipTest("sample() not required for FIT1008/2085; skipping.")
        book = ProcessingBook()
        t1 = tx("ab12")
        t2 = tx("aa23")
        t3 = tx("bcde")
        t4 = tx("023z")
        for t, v in ((t1, 1), (t2, 2), (t3, 3), (t4, 4)):
            book[t] = v

        # size 1: any one signature valid
        s1 = book.sample(1)
        self.assertEqual(len(s1), 1)

        # size 2: forbidden pair is {"ab12","aa23"} (same 'a' at pos 0)
        s2 = book.sample(2)
        self.assertEqual(len(s2), 2)
        s2_set = set(s2[i] for i in range(len(s2)))
        self.assertNotEqual(s2_set, {"ab12", "aa23"})

        # size 3: must be one of the two allowed triplets
        s3 = book.sample(3)
        allowed = [set(["ab12","bcde","023z"]), set(["aa23","bcde","023z"])]
        s3_set = set(s3[i] for i in range(len(s3)))
        self.assertIn(s3_set, allowed)

        # size 4: impossible
        s4 = book.sample(4)
        self.assertIsNone(s4)

if __name__ == "__main__":
    unittest.main()
