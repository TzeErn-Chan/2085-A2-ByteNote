from fraud_detection import *

if __name__ == "__main__":
    print("==== Task 3: FraudDetection — 20-Alert Test Suite ====")

    # ---------- helpers ----------
    from data_structures.referential_array import ArrayR
    from processing_line import Transaction

    def to_array(pylist):
        return ArrayR.from_list(pylist)

    def mk_tx(sig: str, ts: int = 1, s="s", r="r"):
        t = Transaction(ts, s, r)
        t.signature = sig
        return t

    # ---------- T3.1 detect_by_blocks — example in spec (block_size=1, score=6) ----------
    tx = [
        mk_tx("abc", 1), mk_tx("acb", 2), mk_tx("xyz", 3),
        mk_tx("bac", 4), mk_tx("zyx", 5), mk_tx("abb", 6),
    ]
    fd = FraudDetection(to_array(tx))
    bs, score = fd.detect_by_blocks()
    assert score == 6, f"Suspicion score should be 6; got {score}"
    assert bs == 1, f"Most suspicious block size should be 1; got {bs}"
    print("T3.1 OK")

    # ---------- T3.2 detect_by_blocks — leftover handling (S=2 permits block moves, tail fixed) ----------
    # base: 'abcdefg' -> blocks of 2: ab cd ef ; leftover: g
    t1 = mk_tx("abcdefg", 11)
    t2 = mk_tx("cdabefg", 12)  # moving blocks only; leftover 'g' stays
    t3 = mk_tx("efcdabg", 13)
    fd2 = FraudDetection(to_array([t1, t2, t3]))
    bs2, score2 = fd2.detect_by_blocks()
    assert score2 >= 2, f"Should detect some grouping with S=2; got score {score2}"
    print("T3.2 OK")

    # ---------- T3.3 detect_by_blocks — no grouping at all -> score==1 ----------
    ux = [mk_tx("a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"),
          mk_tx("b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8")]
    fd3 = FraudDetection(to_array(ux))
    bs3, score3 = fd3.detect_by_blocks()
    assert score3 == 1, f"When no grouping exists, score should be 1; got {score3}"
    print("T3.3 OK")

    # ---------- T3.4 rectify — spec example (best has MPCL=0) ----------
    tx4 = [Transaction(1, "A", "B"),
           Transaction(2, "A", "B"),
           Transaction(3, "A", "B"),
           Transaction(4, "A", "B")]
    def f1(tr): return [2, 1, 1, 50][tr.timestamp - 1]
    def f2(tr): return [1, 2, 3, 4][tr.timestamp - 1]
    fd4 = FraudDetection(to_array(tx4))
    best_f, mpcl = fd4.rectify(to_array([f1, f2]))
    assert mpcl == 0 and best_f is f2, f"Expected (f2,0); got ({best_f},{mpcl})"
    print("T3.4 OK")

    # ---------- T3.5 rectify — N > table_size protection (all map to 0) ----------
    tx5 = [Transaction(i+1, "A", "B") for i in range(5)]
    def f_const(tr): return 0
    fd5 = FraudDetection(to_array(tx5))
    bf2, mp2 = fd5.rectify(to_array([f_const]))
    assert mp2 == 1, f"With table_size=1 and N=5, MPCL must be table_size (=1); got {mp2}"
    print("T3.5 OK")

    # ---------- T3.6 rectify — mixed collisions sanity ----------
    # hashes: [0,0,1,1,2,3] -> table_size = max+1 = 4 ; N=6 > 4 triggers cap path or guarded probing
    tx6 = [Transaction(i+1, "A", "B") for i in range(6)]
    def f_mix(tr): return [0,0,1,1,2,3][tr.timestamp-1]
    fd6 = FraudDetection(to_array(tx6))
    bf3, mp3 = fd6.rectify(to_array([f_mix]))
    # MPCL should be <= table_size, and in our guarded logic it's table_size (=4) due to N>size
    assert 0 <= mp3 <= 4
    print("T3.6 OK")

    print("All Task 3 tests passed ✅")
