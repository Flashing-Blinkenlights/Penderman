"""A collection of classes for representing abstract structures."""

from copy import deepcopy
from logging import error
from typing import Callable, Sequence

import numpy as np
from gdpc.block import Block
from gdpc.vector_tools import Vec3bLike, Vec3iLike
from numpy.typing import NDArray

EMPTY_BLOCK = Block(id=None)


class Palette:
    """Provides paletting functionality using a block look-up table.

    This is a wrapper of list which aims to minimise the number of times
        a value changes its index. To achieve this, the following
        strategies are employed:

        1. There may be no duplicate values (other than `None`).
        2. Empty spaces (`None`) are created where values are removed.
        3. Every mutating operation returns a minimal update map, e.g.
            {5: 3, 9: 4} (old index: new index)
        4. The palette is unordered unless specified otherwise (`keep_order`).
        5. The palette contains gaps unless specified otherwise (`keep_small`).

        It should be noted that the default settings optimise for computational
            efficiency and usability, and these settings should only be adjusted
            if you're *sure* this is what you want.
    """

    # ====
    # Generic methods
    # ====

    def __init__(
        self,
        blocks: Sequence[Block] = [EMPTY_BLOCK],
        keep_order: bool = False,
        keep_small: bool = False,
    ) -> None:
        """Create a Palette, by default with a "nothing" Block at index 0."""
        if type(blocks) is Block:
            blocks = [blocks]
        self._blut: list[Block] = list(blocks)  # Block Look-Up Table
        self.keep_order: bool = keep_order
        self.keep_small: bool = keep_small

    def __bool__(self):
        """Contains at least one block and that block is not empty."""
        if (
            len(self._blut) < 1
            or len(self._blut) == 1
            and self._blut[0] == EMPTY_BLOCK
        ):
            return False
        return True

    def __len__(self):
        """Return the number of unique blocks in the list (excludes gaps)."""
        return len([None for v in self._blut if v is not None])

    # ====
    # List-centric methods
    # ====

    def _map_leftshift(self, index1: int, index2: int):
        """Return a dict showing the index changes after a leftshift."""
        # make index positive
        if index1 < 0:
            index1 += len(self)
        if index2 < 0:
            index2 += len(self)

        shifted_map = {i: i - 1 for i in range(index1, index2 + 1)}
        if 0 in shifted_map:
            if len(self) - 1 in shifted_map:
                shifted_map[0] = len(self) - 1
            else:
                shifted_map[0] = None

        return shifted_map

    def _map_rightshift(self, index1: int, index2: int):
        """Return a dict showing the index changes after a rightshift."""

    def __getitem__(self, index: int) -> Block | None:
        """Return the block (or gap) at the given index."""
        return self._blut[index]

    def __setitem__(self, index: int, value: Block) -> None:
        """Overwrite the block at a given index (NOT RECOMMENDED).

        This WILL set the prior entries of the block (if they exist) to None,
            and may cause other indexes to be silently modified
            if `keep_order` is True!
        Use `palette.replace_block()` for a less radical alternative!
        """
        if value is not None:
            try:
                index = self.index(value)
                del self[index]
            except ValueError:  # value does not already exist
                pass

        self._blut[index] = value

    def __delitem__(self, index: int) -> None:
        """Insert a gap or delete the object at the index (NOT RECOMMENDED)."""
        if self.keep_small:
            # delete the entry, causing all successive entries to shift left!
            del self._blut[index]
        else:
            # insert a gap, maintaining the other indexes
            self._blut[index] = None

    def __iter__(self):
        """Iterate through the palette (including its gaps)."""
        yield from self._blut

    def __add__(self, other):
        """Concatenate two palettes, preferring the index of the original."""
        other_type = type(other)
        if other_type is not Palette and other_type is not Sequence:
            raise TypeError(
                f"can only concatenate Palette or Sequence "
                f'(not "{other_type}" to Palette)'
            )

        for i, block in enumerate(other):
            self.append(block)

    def __radd__(self, other):
        """Override in case of compatible type on the left."""
        return self + other

    def __iadd__():
        """Implement `+=` functionality."""
        raise NotImplementedError

    def __contains__(self, value: Block):
        """Indicate whether a value is in the palette."""
        return value in self._blut

    def append(self, block: Block, force: bool = False):
        """Append block to palette if it does not exist.

        Use `force` to ensure it is appended (deletes duplicates).
        """
        index = None
        try:
            index = self._blut.index(block)
            if force:
                del self[index]
        except ValueError:
            pass

        self._blut.append(block)

    def clear(self) -> None:
        """Irreversibly clear the palette."""
        self._blut.clear()

    def copy(self) -> "Palette":
        """Return a copy of the palette."""
        return Palette(deepcopy(self._blut), self.keep_order, self.keep_small)

    def count(self, block: Block | None, force_count=False) -> int:
        """Count the number of ocurrences of an item in the palette."""
        if block is not None and not force_count:
            return 1
        return self._blut.count(block)

    def extend(self, blocks: Sequence[Block], force: bool = False):
        """Extend the palette with a sequence of blocks.

        Use `force` to ensure entries are appended (deletes duplicates).
        """
        for block in block:
            self.append(block, force=force)

    def index(self, block: Block) -> int:
        """Get the look-up index of a Block."""
        return self._blut.index(block)

    def insert(self, index: int, block: Block):
        """Insert the Block at the index, causing a right-shift."""
        raise NotImplementedError

    def pop(self, pos=-1):
        """Return and delete the Block at that index from the Palette."""
        raise NotImplementedError

    def remove(self, block: Block):
        """Delete the Block from the Palette."""
        raise NotImplementedError

    def reverse(self):
        """Reverse the order of the Palette."""
        raise NotImplementedError

    def sort(self, *, key: Callable = None, reverse: bool = False):
        """Sort the Palette."""
        raise NotImplementedError

    def strip(self):
        """Remove all empty entries in the Palette."""
        raise NotImplementedError

    # ====
    # Palette-centric methods
    # ====

    def get_indexes(self, show_empty=False) -> dict[int, Block]:
        """Return the block look-up table as a dict. Ignores None by default."""
        if show_empty:
            return dict(enumerate(self._blut))
        return {k: v for k, v in enumerate(self._blut) if v is not None}

    def add_block(self, block: Block) -> int | None:
        """Take a block to be added to the palette and returns its index."""
        if block is None:
            return None

        if block not in self._blut:
            try:
                # fill first empty number
                index = self._blut.index(None)
                self._blut[index] = block
                return index
            except ValueError:
                self._blut.append(block)
                return -1
        return self._blut.index(block)

    def replace_block(
        self, current: Block, replacement: Block = EMPTY_BLOCK
    ) -> int | None:
        """Replace a Block with another Block (uses "nothing" by default)."""
        try:
            old_index: int = self._blut.index(current)
            try:
                new_index: int = self._blut.index(replacement)

                # replacement Block already existed in Palette
                self._blut[old_index] = None
                return new_index

            except ValueError:
                # replacement Block does not yet exist in Palette
                self._blut[old_index] = replacement
                if replacement is None:
                    return None
                return old_index
        except ValueError:
            error(
                f"Current Block {current} does not exist in Palette!\n"
                "The replacement block was added instead!"
            )
            return self.add_block(replacement)

    def remove_block(self, block: Block) -> int | None:
        """Remove a Block from the Palette."""
        return self.replace_block(block, replacement=None)

    def transform(self, flip: Vec3bLike = (0, 0, 0), rotation: int = 0):
        """Transform every Block in this Palette.

        Flips first, rotates second (16 is a full clockwise rotation).
        """
        for block in self._blut:
            if block is None:
                continue
            block.transform(flip=flip, rotation=rotation)
        return


class Shape:
    """Represents a collection spacial points assigned a value."""

    def __init__(
        self, size: Vec3iLike = (1, 1, 1), palette: Palette = Palette()
    ) -> None:
        """Instantiate an empty shape using the necessary values."""
        self._matrix: NDArray = np.zeros(size, dtype=int)
        self._palette: Palette = palette

    def transform(self, flip: Vec3bLike = (0, 0, 0), rotation: int = 0):
        """Transform this Shape by rotating and/or flipping it.

        Flips first, rotates second (16 is a full clockwise rotation).
        """
        raise NotImplementedError

    def put_block(self, block: Block, position: Vec3iLike, *args, **kwargs):
        """Place a Block into the Shape, and update its Palette if necessary."""
        raise NotImplementedError

    def get_block(self, position: Vec3iLike, *args, **kwargs):
        """Query the Block at that relative position in the shape."""
        if type(position) is int:
            position = [position, args[0], args[1]]

        return self._palette.self._matrix[*position]
