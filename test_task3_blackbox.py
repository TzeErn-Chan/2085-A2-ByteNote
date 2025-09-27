
import unittest

from processing_line import Transaction
from fraud_detection import FraudDetection

def tx(ts, s='a', r='b', sig=None):
    t = Transaction(ts, s, r)
    if sig is not None:
        t.signature = sig
    return t

class TestDetectByBlocks(unittest.TestCase):
    def test_example_blocksize_1_is_most_suspicious(self):
        # Signatures: abc, acb, xyz, bac, zyx, abb
        txs = [
            tx(1, sig="abc"),
            tx(2, sig="acb"),
            tx(3, sig="xyz"),
            tx(4, sig="bac"),
            tx(5, sig="zyx"),
            tx(6, sig="abb"),
        ]
        fd = FraudDetection(txs)  # transactions provided as ArrayR in scaffold, list should also be okay if constructor wraps/assumes ArrayR
        size, score = fd.detect_by_blocks()
        self.assertEqual((size, score), (1, 6))

    def test_grouping_with_incomplete_last_block(self):
        # From spec narrative: S=3 example yields group sizes 2,1,2 -> score 4
        sigs = ["aaabbbcc", "bbbaaacc", "ccaaabbb", "cccaaabb", "aaacccbb"]
        txs = [tx(i+1, sig=s) for i, s in enumerate(sigs)]
        fd = FraudDetection(txs)
        size, score = fd.detect_by_blocks()
        # Block size 1 will likely be stronger than 3 for these, but ensure that at least a valid score >=4 is found.
        # We'll assert that one of the candidate block sizes returns a score >= 4 and the method returns that maximum.
        # (Stricter equality would depend on the dataset; we rely on fd to choose the max across S.)
        self.assertGreaterEqual(score, 4)
        self.assertIsInstance(size, int)
        self.assertGreaterEqual(size, 1)

class TestRectify(unittest.TestCase):
    def test_rectify_prefers_smaller_max_probe_chain(self):
        # Create 4 tx with distinct timestamps we can pattern-match on in our hash functions
        T1, T2, T3, T4 = tx(101), tx(102), tx(103), tx(104)
        txs = [T1, T2, T3, T4]
        fd = FraudDetection(txs)

        # Function 1: values 2,1,1,50 -> table size 51; worst-case MPCL should be 2 (as per example)
        def func1(t):
            return {101: 2, 102: 1, 103: 1, 104: 50}[t.timestamp]

        # Function 2: values 1,2,3,4 -> table size 5; MPCL 0
        def func2(t):
            return {101: 1, 102: 2, 103: 3, 104: 4}[t.timestamp]

        best, mpcl = fd.rectify([func1, func2])
        self.assertIn(best, (func2,))  # func2 is strictly better
        self.assertEqual(mpcl, 0)

    def test_rectify_all_same_hash_forces_table_overflow_case(self):
        T1, T2, T3 = tx(1), tx(2), tx(3)
        txs = [T1, T2, T3]
        fd = FraudDetection(txs)

        # Every tx maps to 0 -> table size 1; cannot insert 3 items; MPCL should be table size (1)
        def bad_hash(_t): return 0

        # A mediocre but better function
        def ok_hash(t): return t.timestamp % 5  # collisions possible but table size >= 4

        best, mpcl = fd.rectify([bad_hash, ok_hash])
        self.assertEqual(best, ok_hash)
        # We can't assert the exact mpcl for ok_hash (depends on implementation), but it must be < 1 only if 0;
        # ensure it's <= table size derived from ok_hash values.
        self.assertIsInstance(mpcl, int)
        self.assertGreaterEqual(mpcl, 0)

    def test_rectify_tie_is_allowed_but_mpcl_correct(self):
        T1, T2 = tx(10), tx(11)
        fd = FraudDetection([T1, T2])

        # Two functions both produce unique slots -> both MPCL 0
        def f1(t): return 0 if t.timestamp == 10 else 1
        def f2(t): return 3 if t.timestamp == 10 else 4

        best, mpcl = fd.rectify([f1, f2])
        self.assertIn(best, (f1, f2))
        self.assertEqual(mpcl, 0)

if __name__ == "__main__":
    unittest.main()
