from processing_line import Transaction
from data_structures import ArrayR
from data_structures.hash_table_linear_probing import LinearProbeTable
from data_structures.array_sorted_list import ArraySortedList


class FraudDetection:
    def __init__(self, transactions):
        """
        Time complexity:
        best/worst: O(1) as it stores a direct reference to the provided transaction array without iteration.
        """
        self.transactions = transactions

    def detect_by_blocks(self):
        """
        Time complexity:
        best: O(N * L^2 * log L) where N = len(self.transactions) and L is the signature length.
        worst: O(N * L^3 + N^2 * L^2) where N = len(self.transactions) and L is the signature length.
        For each block size we sort the extracted blocks using `ArraySortedList` and linearly scan existing groups, 
        giving quadratic costs in the favourable case and cubic-plus-quadratic behaviour when every insertion shuffles 
        and every lookup scans all prior groups.
        """
        if len(self.transactions) == 0:
            return 1, 1
        L = len(str(self.transactions[0].signature))
        max_product = 1
        best_S = 1
        for S in range(1, L + 1):
            groups = ArrayR(len(self.transactions))
            index = 0
            for tr in self.transactions:
                sig = str(tr.signature)
                blocks = ArraySortedList()
                for i in range(0, len(sig) - (len(sig) % S), S):
                    blocks.add(sig[i:i + S])
                remainder = sig[len(sig) - (len(sig) % S):]
                key = ''.join(blocks) + remainder
                found = False
                for i in range(index):
                    if groups[i][0] == key:
                        groups[i] = (key, groups[i][1] + 1)
                        found = True
                        break
                if not found:
                    groups[index] = (key, 1)
                    index += 1
            product = 1
            for i in range(index):
                product *= groups[i][1]
            if product > max_product:
                max_product = product
                best_S = S
        return best_S, max_product

    def rectify(self, functions):
        """
        Time complexity:
        best: O(F * N^2) where F is the number of candidate hash functions and N the transaction count.
        worst: O(F * (N^2 + N * M^2)) where F is the number of candidate hash functions and N the transaction count, M = max hash value + 1 for the function.
        For each function we bubble-sort the hashes (quadratic) and simulate linear probing, which stays constant per insert when slots are free 
        but can wrap the table repeatedly under heavy collisions.
        """
        def sort_array(arr, reverse=False):
            n = len(arr)
            for i in range(n):
                for j in range(0, n - i - 1):
                    if (arr[j] > arr[j + 1]) if not reverse else (arr[j] < arr[j + 1]):
                        arr[j], arr[j + 1] = arr[j + 1], arr[j]
        
        best_function = None
        min_mpcl = float('inf')
        for func in functions:
            hashes = ArrayR(len(self.transactions))
            i = 0
            for tr in self.transactions:
                hashes[i] = func(tr)
                i += 1
            if len(hashes) == 0:
                continue
            sort_array(hashes, reverse=True)
            M = max(hashes) + 1
            occupied = LinearProbeTable()
            max_probe = 0
            for idx in range(len(hashes)):
                h = hashes[idx]
                count = 0
                current = h
                while True:
                    try:
                        if occupied[str(current)] is not None:
                            count += 1
                            current = (current + 1) % M
                        else:
                            break
                    except KeyError:
                        break
                    if count >= M:
                        break
                probe = count
                max_probe = max(max_probe, probe)
                occupied[str(h)] = True
            if max_probe < min_mpcl:
                min_mpcl = max_probe
                best_function = func
        return best_function, min_mpcl


if __name__ == "__main__":
    # Write tests for your code here...
    # We are not grading your tests, but we will grade your code with our own tests!
    # So writing tests is a good idea to ensure your code works as expected.
    
    def to_array(lst):
        """
        Helper function to create an ArrayR from a list.
        """
        lst = [to_array(item) if isinstance(item, list) else item for item in lst]
        return ArrayR.from_list(lst)

    # Here is something to get you started with testing detect_by_blocks
    print("<------- Testing detect_by_blocks! ------->")
    # Let's create 2 transactions and set their signatures
    tr1 = Transaction(1, "Alice", "Bob")
    tr2 = Transaction(2, "Alice", "Bob")

    # I will intentionally give the signatures that would put them in the same groups
    # if the block size was 1 or 2.
    tr1.signature = "aabbcc"
    tr2.signature = "ccbbaa"

    # Let's create an instance of FraudDetection with these transactions
    fd = FraudDetection([tr1, tr2])

    # Let's test the detect_by_blocks method
    block_size, suspicion_score = fd.detect_by_blocks()

    # We print the result, hopefully we should see either 1 or 2 for block size, and 2 for suspicion score.
    print(f"Block size: {block_size}, Suspicion score: {suspicion_score}")

    # I'm putting this line here so you can find where the testing ends in the terminal, but testing is by no means
    # complete. There are many more scenarios you'll need to test. Follow what we did above.
    print("<--- Testing detect_by_blocks finished! --->\n")

    # ----------------------------------------------------------

    # Here is something to get you started with testing rectify
    print("<------- Testing rectify! ------->")
    # I'm creating 4 simple transactions...
    transactions = [
        Transaction(1, "Alice", "Bob"),
        Transaction(2, "Alice", "Bob"),
        Transaction(3, "Alice", "Bob"),
        Transaction(4, "Alice", "Bob"),
    ]

    # Then I create two functions and to make testing easier, I use the timestamps I
    # gave to transactions to return the value I want for each transaction.
    def function1(transaction):
        return [2, 1, 1, 50][transaction.timestamp - 1]

    def function2(transaction):
        return [1, 2, 3, 4][transaction.timestamp - 1]

    # Now I create an instance of FraudDetection with these transactions
    fd = FraudDetection(to_array(transactions))

    # And I call rectify with the two functions
    result = fd.rectify(to_array([function1, function2]))

    # The expected result is (function2, 0) because function2 will give us a max probe chain of 0.
    # This is the same example given in the specs
    print(result)
    
    # I'll also use an assert statement to make sure the returned function is indeed the correct one.
    # This will be harder to verify by printing, but can be verified easily with an `assert`:
    assert result == (function2, 0), f"Expected (function2, 0), but got {result}"

    print("<--- Testing rectify finished! --->")
