# Originally derived from http://code.activestate.com/recipes/576694/
# Some major additions were made, namely __*item__ methods and
# difference_update and update.

import collections


class OrderedSet(collections.MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def __getitem__(self, index):
        if isinstance(index, slice):
            retval = list()
            iter = index.indices(len(self))

            # XXX - blah, ugly, but I'm lazy
            in_map = set()
            for k in range(*iter):
                in_map.add(k)

            for i, k in enumerate(self):
                if i in in_map:
                    retval.append(k)

            return retval
        else:
            for i, k in enumerate(self):
                if index == i:
                    return k

        raise IndexError('Index out of range')

    def __setitem__(self, index, key):
        node = self.map.pop(self[index])
        node[0] = key
        self.map[key] = node

    def __delitem__(self, index):
        self.remove(self[index])

    def index(self, key):
        for i, k in enumerate(self):
            if k == key:
                return i

        raise KeyError('key not in set')

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def update(self, keys):
        for key in keys:
            self.add(key)

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def remove(self, key):
        if key not in self.map:
            raise KeyError(key)

        self.discard(key)

    def difference_update(self, keys):
        for key in keys:
            self.discard(key)

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


if __name__ == '__main__':
    s = OrderedSet('abracadaba')
    t = OrderedSet('simsalabim')
    print(s | t)
    print(s & t)
    print(s - t)
