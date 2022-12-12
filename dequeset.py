"""
An OrderedDequeSet is a custom MutableSet that remembers its order, so that every
entry has an index that can be looked up. It can also act like a Sequence. 

Interally, it maintains a deque allowing for addleft, popleft, and max length.
By default, items are popped off the left when adding to the right, and from the right
when adding to the left.

Based on a recipe originally posted to ActiveState Recipes by Raymond Hettiger,
and released under the MIT license. 

Tweaked by imbesci and rereleased under the MIT license.
"""
import itertools as it
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    MutableSet,
    AbstractSet,
    Sequence,
    Set,
    TypeVar,
    Union,
    overload,
)

from collections import deque

SLICE_ALL = slice(None)
__version__ = "4.1.0"


T = TypeVar("T")

# SetLike[T] is either a set of elements of type T, or a sequence, which
# we will convert to an OrderedDequeSet by adding its elements in order.
SetLike = Union[AbstractSet[T], Sequence[T]]
OrderedDequeSetInitializer = Union[AbstractSet[T], Sequence[T], Iterable[T]]


def _is_atomic(obj: Any) -> bool:
    """
    Returns True for objects which are iterable but should not be iterated in
    the context of indexing an OrderedDequeSet.

    When we index by an iterable, usually that means we're being asked to look
    up a list of things.

    However, in the case of the .index() method, we shouldn't handle strings
    and tuples like other iterables. They're not sequences of things to look
    up, they're the single, atomic thing we're trying to find.

    As an example, oset.index('hello') should give the index of 'hello' in an
    OrderedDequeSet of strings. It shouldn't give the indexes of each individual
    character.
    """
    return isinstance(obj, str) or isinstance(obj, tuple)


class OrderedDequeSet(MutableSet[T], Sequence[T]):
    """
    An OrderedDequeSet is a custom MutableSet that remembers its order so that
    every entry has an index that can be looked up. Additionally, it provides a
    maxlen parameter to specify the maximum size of the structure.

    Example:
        >>> OrderedDequeSet([1, 1, 2, 3, 2])
        OrderedDequeSet([1, 2, 3])
    """

    def __init__(self, initial: OrderedDequeSetInitializer[T] = None, maxlen=None):
        self.items: deque[T] = deque([], maxlen=maxlen)
        self.map: Dict[T, int] = {}
        self._maxlen = maxlen
        if initial is not None:
            # In terms of duck-typing, the default __ior__ is compatible with
            # the types we use, but it doesn't expect all the types we
            # support as values for `initial`.
            self |= initial  # type: ignore

    def __len__(self):
        """
        Returns the number of unique elements in the ordered set

        Example:
            >>> len(OrderedDequeSet([]))
            0
            >>> len(OrderedDequeSet([1, 2]))
            2
        """
        return len(self.items)

    @property
    def maxlen(self):
        return self._maxlen

    @maxlen.setter
    def maxlen(self, value: int):
        if not isinstance(value, int):
            raise TypeError("'maxlen' must be an integer")

        self._maxlen = value
        self.items = deque(self.items, maxlen=value)

    @overload
    def __getitem__(self, index: slice) -> "OrderedDequeSet[T]":
        ...

    @overload
    def __getitem__(self, index: Sequence[int]) -> List[T]:
        ...

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    # concrete implementation
    def __getitem__(self, index):
        """
        Get the item at a given index.

        If `index` is a slice, you will get back that slice of items, as a
        new OrderedDequeSet.

        If `index` is a list or a similar iterable, you'll get a list of
        items corresponding to those indices. This is similar to NumPy's
        "fancy indexing". The result is not an OrderedDequeSet because you may ask
        for duplicate indices, and the number of elements returned should be
        the number of elements asked for.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset[1]
            2
        """
        if isinstance(index, slice) and index == SLICE_ALL:
            return self.copy()
        elif isinstance(index, Iterable):
            return [self.items[i] for i in index]
        elif isinstance(index, slice) or hasattr(index, "__index__"):
            result = self.items[index]
            if isinstance(result, list):
                return self.__class__(result)
            else:
                return result
        else:
            raise TypeError("Don't know how to index an OrderedDequeSet by %r" % index)

    def copy(self) -> "OrderedDequeSet[T]":
        """
        Return a shallow copy of this object.

        Example:
            >>> this = OrderedDequeSet([1, 2, 3])
            >>> other = this.copy()
            >>> this == other
            True
            >>> this is other
            False
        """
        return self.__class__(self, maxlen=self.maxlen)

    # Define the gritty details of how an OrderedDequeSet is serialized as a pickle.
    # We leave off type annotations, because the only code that should interact
    # with these is a generalized tool such as pickle.
    def __getstate__(self):
        if len(self) == 0:
            # In pickle, the state can't be an empty list.
            # We need to return a truthy value, or else __setstate__ won't be run.
            #
            # This could have been done more gracefully by always putting the state
            # in a tuple, but this way is backwards- and forwards- compatible with
            # previous versions of OrderedDequeSet.
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key: Any) -> bool:
        """
        Test if the item is in this ordered set.

        Example:
            >>> 1 in OrderedDequeSet([1, 3, 2])
            True
            >>> 5 in OrderedDequeSet([1, 3, 2])
            False
        """
        return key in self.map

    def refresh_index(fn):
        """Decorator to refresh the index values to ensure correctness in self.map"""

        def _helper(self, *args, **kwargs):
            res = fn(self, *args, **kwargs)
            for i, key in enumerate(self.items):
                self.map[key] = i
            return res

        return _helper

    # Technically type-incompatible with MutableSet, because we return an
    # int instead of nothing. This is also one of the things that makes
    # OrderedDequeSet convenient to use.

    @refresh_index
    def add(self, key: T) -> int:
        """
        Add `key` as an item to this OrderedDequeSet, then return its index.

        If `key` is already in the OrderedDequeSet, return the index it already
        had.

        Example:
            >>> oset = OrderedDequeSet()
            >>> oset.append(3)
            0
            >>> print(oset)
            OrderedDequeSet([3])
        """
        if key not in self.map:
            self.map[key] = len(self.items)
            self.items.append(key)
        return self.map[key]

    @refresh_index
    def addleft(self, key: T) -> int:
        """
        Add `key` as an item to this OrderedDequeSet, then return its index.

        If `key` is already in the OrderedDequeSet, return the index it already
        had.

        Example:
            >>> oset = OrderedDequeSet([3, 4, 5])
            >>> oset.addleft(2)
            0
            >>> print(oset)
            OrderedDequeSet([2, 3, 4, 5])
        """
        if key not in self.map:
            self.items.appendleft(key)
            self.map[key] = 0
        return self.map[key]  # should always be 0

    def update(self, sequence: SetLike[T]) -> int:
        """
        Update the set with the given iterable sequence, then return the index
        of the last element inserted.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset.update([3, 1, 5, 1, 4])
            4
            >>> print(oset)
            OrderedDequeSet([1, 2, 3, 5, 4])
        """
        item_index = 0
        try:
            for item in sequence:
                item_index = self.add(item)
        except TypeError:
            raise ValueError("Argument needs to be an iterable, got %s" % type(sequence))
        return item_index

    @overload
    def index(self, key: Sequence[T]) -> List[int]:
        ...

    @overload
    def index(self, key: T) -> int:
        ...

    # concrete implementation
    def index(self, key):
        """
        Get the index of a given entry, raising an IndexError if it's not
        present.

        `key` can be an iterable of entries that is not a string, in which case
        this returns a list of indices.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset.index(2)
            1
        """
        if isinstance(key, Iterable) and not _is_atomic(key):
            return [self.index(subkey) for subkey in key]
        return self.map[key]

    # Provide some compatibility with pd.Index
    get_loc = index
    get_indexer = index

    def pop(self, index=-1) -> T:
        """
        Remove and return item at index (default last).

        Raises KeyError if the set is empty.
        Raises IndexError if index is out of range.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset.pop()
            3
        """
        if not self.items:
            raise KeyError("Set is empty")

        elem = self.items[index]
        del self.items[index]
        del self.map[elem]
        return elem

    @refresh_index
    def popleft(self):
        """
        Remove and return item at index 0.

        Raises KeyError if the set is empty.
        Raises IndexError if index is out of range.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset.popleft()
            1
            >>> oset
            OrderedDequeSet([2, 3])
        """
        elem = self.items.popleft()
        del self.map[elem]
        return elem

    def discard(self, key: T) -> None:
        """
        Remove an element.  Do not raise an exception if absent.

        The MutableSet mixin uses this to implement the .remove() method, which
        *does* raise an error when asked to remove a non-existent item.

        Example:
            >>> oset = OrderedDequeSet([1, 2, 3])
            >>> oset.discard(2)
            >>> print(oset)
            OrderedDequeSet([1, 3])
            >>> oset.discard(2)
            >>> print(oset)
            OrderedDequeSet([1, 3])
        """
        if key in self:
            i = self.map[key]
            del self.items[i]
            del self.map[key]
            for k, v in self.map.items():
                if v >= i:
                    self.map[k] = v - 1

    def clear(self) -> None:
        """
        Remove all items from this OrderedDequeSet.
        """
        del self.items[:]
        self.map.clear()

    def __iter__(self) -> Iterator[T]:
        """
        Example:
            >>> list(iter(OrderedDequeSet([1, 2, 3])))
            [1, 2, 3]
        """
        return iter(self.items)

    def __reversed__(self) -> Iterator[T]:
        """
        Example:
            >>> list(reversed(OrderedDequeSet([1, 2, 3])))
            [3, 2, 1]
        """
        return reversed(self.items)

    def __repr__(self) -> str:
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other: Any) -> bool:
        """
        Returns true if the containers have the same items. If `other` is a
        Sequence, then order is checked, otherwise it is ignored.

        Example:
            >>> oset = OrderedDequeSet([1, 3, 2])
            >>> oset == [1, 3, 2]
            True
            >>> oset == [1, 2, 3]
            False
            >>> oset == [2, 3]
            False
            >>> oset == OrderedDequeSet([3, 2, 1])
            False
        """
        if isinstance(other, Sequence):
            # Check that this OrderedDequeSet contains the same elements, in the
            # same order, as the other object.
            return list(self) == list(other)
        try:
            other_as_set = set(other)
        except TypeError:
            # If `other` can't be converted into a set, it's not equal.
            return False
        else:
            return set(self) == other_as_set

    def reverse(self):
        """Reverses the OrderedDequeSet and returns the instance"""
        l, r = 0, len(self.items) - 1
        while l < r:
            lkey, rkey = self.items[l], self.items[r]
            self.items[l] = rkey
            self.items[r] = lkey
            self.map[lkey] = r
            self.map[rkey] = l
            l += 1
            r -= 1
        return self

    def union(
        self,
        *sets: SetLike[T],
    ) -> "OrderedDequeSet[T]":
        """
        Combines all unique items.
        Each items order is defined by its first appearance.

        Example:
            >>> oset = OrderedDequeSet.union(OrderedDequeSet([3, 1, 4, 1, 5]), [1, 3], [2, 0])
            >>> print(oset)
            OrderedDequeSet([3, 1, 4, 5, 2, 0])
            >>> oset.union([8, 9])
            OrderedDequeSet([3, 1, 4, 5, 2, 0, 8, 9])
            >>> oset | {10}
            OrderedDequeSet([3, 1, 4, 5, 2, 0, 10])
        """
        cls: type = OrderedDequeSet
        if isinstance(self, OrderedDequeSet):
            cls = self.__class__
        containers = map(list, it.chain([self], sets))
        items = it.chain.from_iterable(containers)
        return cls(items, maxlen=self.maxlen)

    def __and__(self, other: SetLike[T]) -> "OrderedDequeSet[T]":
        # the parent implementation of this is backwards
        return self.intersection(other)

    def intersection(self, *sets: SetLike[T]) -> "OrderedDequeSet[T]":
        """
        Returns elements in common between all sets. Order is defined only
        by the first set.

        Example:
            >>> oset = OrderedDequeSet.intersection(OrderedDequeSet([0, 1, 2, 3]), [1, 2, 3])
            >>> print(oset)
            OrderedDequeSet([1, 2, 3])
            >>> oset.intersection([2, 4, 5], [1, 2, 3, 4])
            OrderedDequeSet([2])
            >>> oset.intersection()
            OrderedDequeSet([1, 2, 3])
        """
        cls: type = OrderedDequeSet
        items: OrderedDequeSetInitializer[T] = self
        if isinstance(self, OrderedDequeSet):
            cls = self.__class__
        if sets:
            common = set.intersection(*map(set, sets))
            items = (item for item in self if item in common)
        return cls(items, self.maxlen)

    def difference(self, *sets: SetLike[T]) -> "OrderedDequeSet[T]":
        """
        Returns all elements that are in this set but not the others.

        Example:
            >>> OrderedDequeSet([1, 2, 3]).difference(OrderedDequeSet([2]))
            OrderedDequeSet([1, 3])
            >>> OrderedDequeSet([1, 2, 3]).difference(OrderedDequeSet([2]), OrderedDequeSet([3]))
            OrderedDequeSet([1])
            >>> OrderedDequeSet([1, 2, 3]) - OrderedDequeSet([2])
            OrderedDequeSet([1, 3])
            >>> OrderedDequeSet([1, 2, 3]).difference()
            OrderedDequeSet([1, 2, 3])
        """
        cls = self.__class__
        items: OrderedDequeSetInitializer[T] = self
        if sets:
            other = set.union(*map(set, sets))
            items = (item for item in self if item not in other)
        return cls(items, maxlen=self.maxlen)

    def issubset(self, other: SetLike[T]) -> bool:
        """
        Report whether another set contains this set.

        Example:
            >>> OrderedDequeSet([1, 2, 3]).issubset({1, 2})
            False
            >>> OrderedDequeSet([1, 2, 3]).issubset({1, 2, 3, 4})
            True
            >>> OrderedDequeSet([1, 2, 3]).issubset({1, 4, 3, 5})
            False
        """
        if len(self) > len(other):  # Fast check for obvious cases
            return False
        return all(item in other for item in self)

    def issuperset(self, other: SetLike[T]) -> bool:
        """
        Report whether this set contains another set.

        Example:
            >>> OrderedDequeSet([1, 2]).issuperset([1, 2, 3])
            False
            >>> OrderedDequeSet([1, 2, 3, 4]).issuperset({1, 2, 3})
            True
            >>> OrderedDequeSet([1, 4, 3, 5]).issuperset({1, 2, 3})
            False
        """
        if len(self) < len(other):  # Fast check for obvious cases
            return False
        return all(item in self for item in other)

    def symmetric_difference(self, other: SetLike[T]) -> "OrderedDequeSet[T]":
        """
        Return the symmetric difference of two OrderedDequeSets as a new set.
        That is, the new set will contain all elements that are in exactly
        one of the sets.

        Their order will be preserved, with elements from `self` preceding
        elements from `other`.

        Example:
            >>> this = OrderedDequeSet([1, 4, 3, 5, 7])
            >>> other = OrderedDequeSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference(other)
            OrderedDequeSet([4, 5, 9, 2])
        """
        cls: type = OrderedDequeSet
        if isinstance(self, OrderedDequeSet):
            cls = self.__class__
        diff1 = cls(self, maxlen=self.maxlen).difference(other)
        diff2 = cls(other, maxlen=self.maxlen).difference(self)
        return diff1.union(diff2)

    def _update_items(self, items: list) -> None:
        """
        Replace the 'items' list of this OrderedDequeSet with a new one, updating
        self.map accordingly.
        """
        self.items = items
        self.map = {item: idx for (idx, item) in enumerate(items)}

    def difference_update(self, *sets: SetLike[T]) -> None:
        """
        Update this OrderedDequeSet to remove items from one or more other sets.

        Example:
            >>> this = OrderedDequeSet([1, 2, 3])
            >>> this.difference_update(OrderedDequeSet([2, 4]))
            >>> print(this)
            OrderedDequeSet([1, 3])

            >>> this = OrderedDequeSet([1, 2, 3, 4, 5])
            >>> this.difference_update(OrderedDequeSet([2, 4]), OrderedDequeSet([1, 4, 6]))
            >>> print(this)
            OrderedDequeSet([3, 5])
        """
        items_to_remove = set()  # type: Set[T]
        for other in sets:
            items_as_set = set(other)  # type: Set[T]
            items_to_remove |= items_as_set
        self._update_items([item for item in self.items if item not in items_to_remove])

    def intersection_update(self, other: SetLike[T]) -> None:
        """
        Update this OrderedDequeSet to keep only items in another set, preserving
        their order in this set.

        Example:
            >>> this = OrderedDequeSet([1, 4, 3, 5, 7])
            >>> other = OrderedDequeSet([9, 7, 1, 3, 2])
            >>> this.intersection_update(other)
            >>> print(this)
            OrderedDequeSet([1, 3, 7])
        """
        other = set(other)
        self._update_items([item for item in self.items if item in other])

    def symmetric_difference_update(self, other: SetLike[T]) -> None:
        """
        Update this OrderedDequeSet to remove items from another set, then
        add items from the other set that were not present in this set.

        Example:
            >>> this = OrderedDequeSet([1, 4, 3, 5, 7])
            >>> other = OrderedDequeSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference_update(other)
            >>> print(this)
            OrderedDequeSet([4, 5, 9, 2])
        """
        items_to_add = [item for item in other if item not in self]
        items_to_remove = set(other)
        self._update_items([item for item in self.items if item not in items_to_remove] + items_to_add)
