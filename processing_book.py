from data_structures import ArrayR

from processing_line import Transaction


class ProcessingBook:
    LEGAL_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"

    def __init__(self, level=0):
        """
        Time complexity:
        best: O(1)
        worst: O(1)
        Justification: Initialising the fixed-length `ArrayR` of 36 pages and
        scalar counters is constant time at construction, establishing the
        trie-like structure one layer at a time.
        """
        self.level = level
        self.pages = ArrayR(len(ProcessingBook.LEGAL_CHARACTERS))
        self.total_count = 0
        self.error_count = 0
    
    def page_index(self, character):
        """
        Time complexity:
        best: O(1)
        worst: O(1)
        Justification: The lookup scans at most 36 legal characters within the
        pre-defined alphabet to translate a character into its page index.
        """
        return ProcessingBook.LEGAL_CHARACTERS.index(character)
    
    def __setitem__(self, transaction, amount):
        """
        Time complexity:
        best: O(1)
        worst: O(L)
        Justification: We bucket each signature by successive characters in a
        trie of nested `ProcessingBook` instances stored in fixed-size `ArrayR`
        pages; empty slots accept inserts immediately, while collisions descend
        at most L levels (L = signature length) before placing the tuple once the
        prefixes diverge.
        """
        sig = transaction.signature
        idx = self.page_index(sig[self.level])
        page = self.pages[idx]
        if page is None:
            self.pages[idx] = (transaction, amount)
            self.total_count += 1
            return True
        elif isinstance(page, tuple):
            existing_tr, existing_amt = page
            if existing_tr is transaction:
                if existing_amt != amount:
                    self.error_count += 1
                return False
            # collision
            new_book = ProcessingBook(level=self.level + 1)
            new_book[existing_tr] = existing_amt
            new_book[transaction] = amount
            self.pages[idx] = new_book
            self.total_count += 1
            return True
        elif isinstance(page, ProcessingBook):
            added = page[transaction] = amount
            if added:
                self.total_count += 1
            return added
    
    def __getitem__(self, transaction):
        """
        Time complexity:
        best: O(1)
        worst: O(L)
        Justification: Retrieval mirrors insertion: we index directly into the
        `ArrayR` page using the next signature character and only recur while a
        collision subtree exists, so resolution touches at most one node per
        character.
        """
        sig = transaction.signature
        idx = self.page_index(sig[self.level])
        page = self.pages[idx]
        if page is None:
            raise KeyError
        elif isinstance(page, tuple):
            tr, amt = page
            if tr is transaction:
                return amt
            else:
                raise KeyError
        elif isinstance(page, ProcessingBook):
            return page[transaction]
    
    def __delitem__(self, transaction):
        """
        Time complexity:
        best: O(1)
        worst: O(L)
        Justification: Deletion follows the same character-indexed path through
        the trie, removing at most one node per level and collapsing a child
        book only after scanning its 36 constant-size pages.
        """
        sig = transaction.signature
        idx = self.page_index(sig[self.level])
        page = self.pages[idx]
        if page is None:
            raise KeyError
        elif isinstance(page, tuple):
            tr, amt = page
            if tr is transaction:
                self.pages[idx] = None
                self.total_count -= 1
            else:
                raise KeyError
        elif isinstance(page, ProcessingBook):
            page.__delitem__(transaction)
            self.total_count -= 1
            if page.total_count == 1:
                for i in range(len(page.pages)):
                    if page.pages[i] is not None:
                        self.pages[idx] = page.pages[i]
                        break
    
    def __len__(self):
        """
        Time complexity:
        best: O(1)
        worst: O(1)
        Justification: We maintain the current population in `total_count`, so
        computing the size is a cached constant-time read.
        """
        return self.total_count
    
    def __iter__(self):
        """
        Time complexity:
        best: O(1)
        worst: O(N)
        Justification: Iteration scans the 36 fixed `ArrayR` pages in lexical
        order and yields each stored tuple exactly once, recursing into nested
        books so the total traversal is linear in the number of transactions.
        """
        for char in ProcessingBook.LEGAL_CHARACTERS:
            idx = self.page_index(char)
            page = self.pages[idx]
            if page is not None:
                if isinstance(page, tuple):
                    yield page
                elif isinstance(page, ProcessingBook):
                    yield from page
    
    def get_error_count(self):
        """
        Time complexity:
        best: O(1)
        worst: O(N)
        Justification: We accumulate the local error counter and recursively sum
        any nested books, so an empty page scan is constant while visiting every
        sub-book is linear in the number of stored substructures.
        """
        total = self.error_count
        for page in self.pages:
            if isinstance(page, ProcessingBook):
                total += page.get_error_count()
        return total
    
    def sample(self, required_size):
        """
        1054 Only - 1008/2085 welcome to attempt if you're up for a challenge, but no marks are allocated.
        Time complexity:
        best: O(1)
        worst: O(1)
        Justification: Currently unimplemented; the stub returns immediately
        without examining the stored transactions.
        """
        return None


if __name__ == "__main__":
    # Write tests for your code here...
    # We are not grading your tests, but we will grade your code with our own tests!
    # So writing tests is a good idea to ensure your code works as expected.

    # Let's create a few transactions
    tr1 = Transaction(123, "sender", "receiver")
    tr1.signature = "abc123"

    tr2 = Transaction(124, "sender", "receiver")
    tr2.signature = "0bbzzz"

    tr3 = Transaction(125, "sender", "receiver")
    tr3.signature = "abcxyz"

    # Let's create a new book to store these transactions
    book = ProcessingBook()

    book[tr1] = 10
    print(book[tr1])  # Prints 10

    book[tr2] = 20
    print(book[tr2])  # Prints 20

    book[tr3] = 30    # Ends up creating 3 other nested books
    print(book[tr3])  # Prints 30
    print(book[tr2])  # Prints 20

    book[tr2] = 40
    print(book[tr2])  # Prints 20 (because it shouldn't update the amount)

    del book[tr1]     # Delete the first transaction. This also means the nested books will be collapsed. We'll test that in a bit.
    try:
        print(book[tr1])  # Raises KeyError
    except KeyError as e:
        print("Raised KeyError as expected:", e)

    print(book[tr2])  # Prints 20
    print(book[tr3])  # Prints 30

    # We deleted T1 a few lines above, which collapsed the nested books.
    # Let's make sure that actually happened. We should be able to find tr3 sitting
    # in Page A of the book:
    print(book.pages[book.page_index('a')])  # This should print whatever details we stored of T3 and only T3
