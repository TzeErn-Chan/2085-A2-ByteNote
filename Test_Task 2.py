from processing_book import *

if __name__ == "__main__":
    print("==== Task 2: ProcessingBook — 20-Alert Test Suite ====")

    # ---------- helpers ----------
    def mk_tx(sig: str, ts: int = 1, s="s", r="r"):
        t = Transaction(ts, s, r)
        t.signature = sig
        return t

    # ---------- T2.1 insert & get without collisions ----------
    b = ProcessingBook()
    t1 = mk_tx("a00000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")  # starts with a
    t2 = mk_tx("b00000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")  # starts with b
    t3 = mk_tx("0zzzzz000000000000000000000000000000")  # starts with 0
    b[t1] = 11
    b[t2] = 22
    b[t3] = 33
    assert b[t1] == 11 and b[t2] == 22 and b[t3] == 33
    assert len(b) == 3
    print("T2.1 OK")

    # ---------- T2.2 deep collisions & nested books ----------
    # collide on first few chars: abc123... vs abcxyz...
    c1 = mk_tx("abc123xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    c2 = mk_tx("abcxyzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    b[c1] = 100
    b[c2] = 200
    assert b[c1] == 100 and b[c2] == 200
    # top level 'a' page should now hold a nested book OR directly a tuple (after future collapses)
    # here仅检查能读回即可
    print("T2.2 OK")

    # ---------- T2.3 same amount update is allowed; different amount counts error ----------
    err0 = b.get_error_count()
    b[c1] = 100              # same amount (no error)
    assert b.get_error_count() == err0
    b[c1] = 999              # different amount (count error, value unchanged)
    assert b[c1] == 100
    assert b.get_error_count() == err0 + 1
    print("T2.3 OK")

    # ---------- T2.4 deletion collapses ----------
    before = len(b)
    del b[c1]
    assert len(b) == before - 1
    try:
        _ = b[c1]
        assert False, "Expected KeyError after deletion"
    except KeyError:
        pass
    # the nested chain should collapse so that 'a' page holds just c2 now
    assert b[c2] == 200
    print("T2.4 OK")

    # ---------- T2.5 delete non-existent & get non-existent ----------
    ghost = mk_tx("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
    try:
        del b[ghost]
        assert False, "Expected KeyError on deleting non-existent transaction"
    except KeyError:
        pass
    try:
        _ = b[ghost]
        assert False, "Expected KeyError on reading non-existent transaction"
    except KeyError:
        pass
    print("T2.5 OK")

    # ---------- T2.6 iteration order (a..z then 0..9), and tuples (t, amount) ----------
    # Example from spec:
    T1 = mk_tx("aab0aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"); b[T1] = 12
    T2 = mk_tx("aaa0aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"); b[T2] = 20
    T3 = mk_tx("bbb1bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"); b[T3] = 83
    T4 = mk_tx("babbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"); b[T4] = 14
    T5 = mk_tx("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"); b[T5] = 57
    seq = list(b)  # iterator yields (transaction, amount)
    # pull just (sig, amt) and check relative order of the five we care about:
    pick = [(t.signature, a) for (t, a) in seq if t in (T1, T2, T3, T4, T5)]
    expected = [
        (T5.signature, 57),
        (T2.signature, 20),
        (T1.signature, 12),
        (T4.signature, 14),
        (T3.signature, 83),
    ]
    assert pick == expected, f"Iteration order mismatch.\nGot: {pick}\nExpect: {expected}"
    print("T2.6 OK")

    # ---------- T2.7 page_index sanity (a=0..z=25, 0=26..9=35) ----------
    assert b.page_index('a') == 0
    assert b.page_index('z') == 25
    assert b.page_index('0') == 26
    assert b.page_index('9') == 35
    print("T2.7 OK")

    print("All Task 2 tests passed ✅")
