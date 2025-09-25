from processing_line import *

if __name__ == "__main__":
    print("==== Task 1: ProcessingLine — 20-Alert Test Suite ====")

    # ---------- helpers ----------
    def assert_sig_format(sig: str):
        assert isinstance(sig, str)
        assert len(sig) == 36, f"Signature length != 36: {len(sig)}"
        for ch in sig:
            assert ("a" <= ch <= "z") or ("0" <= ch <= "9"), f"Illegal char in signature: {ch}"

    def collect_users(iterable):
        return [t.from_user for t in iterable]

    # ---------- T1.1 sign() format & determinism ----------
    t = Transaction(123456789, "ALICE", "BoB")
    assert t.signature is None
    t.sign()
    s1 = t.signature
    assert_sig_format(s1)
    # call again should give same result
    t.sign()
    s2 = t.signature
    assert s1 == s2, "sign() should be deterministic"
    print("T1.1 OK")

    # ---------- T1.2 basic ordering (matches spec example) ----------
    C = Transaction(100, "C", "X")
    A1 = Transaction(90,  "A1", "X")   # before
    A2 = Transaction(80,  "A2", "X")   # before (added later -> closer to C)
    A3 = Transaction(110, "A3", "X")   # after
    A4 = Transaction(120, "A4", "X")   # after (added later -> closer to C)

    line = ProcessingLine(C)
    line.add_transaction(A3)
    line.add_transaction(A2)
    line.add_transaction(A4)
    line.add_transaction(A1)

    got = collect_users(line)
    expect = ["A2", "A1", "C", "A4", "A3"]
    assert got == expect, f"Order mismatch.\nGot:    {got}\nExpect: {expect}"
    print("T1.2 OK")

    # ---------- T1.3 equal timestamp goes BEFORE C ----------
    C2 = Transaction(100, "C2", "X")
    E1 = Transaction(100, "E1", "X")   # equal ts -> before C2
    E2 = Transaction(100, "E2", "X")   # added later -> closer to C2 than E1
    L2 = ProcessingLine(C2)
    L2.add_transaction(E1)
    L2.add_transaction(E2)
    got = collect_users(L2)
    expect = ['E1', 'E2', 'C2']
    assert got == expect, f"Equal-ts ordering wrong.\nGot {got}\nExpect {expect}"
    print("T1.3 OK")

    # ---------- T1.4 locking semantics ----------
    C3 = Transaction(50, "C3", "X")
    B1 = Transaction(10, "B1", "X")
    L3 = ProcessingLine(C3)
    L3.add_transaction(B1)
    it = iter(L3)  # locks here
    # adding after iter -> RuntimeError
    try:
        L3.add_transaction(Transaction(5, "Z", "X"))
        assert False, "Expected RuntimeError when adding after iter starts"
    except RuntimeError:
        pass
    # creating second iterator -> RuntimeError
    try:
        iter(L3)
        assert False, "Expected RuntimeError when creating second iterator"
    except RuntimeError:
        pass
    print("T1.4 OK")

    # ---------- T1.5 signing-on-iteration ----------
    C4 = Transaction(70, "C4", "X")
    P1 = Transaction(60, "P1", "X")
    P2 = Transaction(80, "P2", "X")
    L4 = ProcessingLine(C4)
    L4.add_transaction(P1)
    L4.add_transaction(P2)
    # all unsigned before iter
    assert C4.signature is None and P1.signature is None and P2.signature is None
    it4 = iter(L4)
    # each next() returns already-signed transaction
    a = next(it4); assert a.signature is not None; assert_sig_format(a.signature)
    b = next(it4); assert b.signature is not None; assert_sig_format(b.signature)
    c = next(it4); assert c.signature is not None; assert_sig_format(c.signature)
    try:
        next(it4)
        assert False, "Iterator should raise StopIteration at end"
    except StopIteration:
        pass
    print("T1.5 OK")

    print("All Task 1 tests passed ✅")
