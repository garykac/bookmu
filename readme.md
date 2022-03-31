# Tables

Tables are structured as follows:

Simple table with no border lines.

```
++-------+-------+-------+
+|  1,1  |  1,2  |  1,3  |
+|  2,1  |  2,2  |  2,3  |
++-------+-------+-------+
```

Simple table with border lines around each cell. Border lines
must be comprised entirely of `'-'` that span the entire length
of each cell.

```
++-------+-------+-------+
+|  1,1  |  1,2  |  1,3  |
+|-------+-------+-------|
 |  2,1  |  2,2  |  2,3  |
++-------+-------+-------+
```

The entire table must be consistent - it is not valid to have
a table that has borders for only some cells.

To create a single-row table with a border, you need to add
a border line (either above or below the row data).

```
++-------+-------+        ++-------+-------+
+|-------+-------+        +|  1,1  |  1,2  |
 |  1,1  |  1,2  |   or    |-------+-------+
++-------+-------+        ++-------+-------+
```

Tables start and end with a line that starts with `'++'` and
contains only `'-'` except for the column boundaries, which
are marked with `'+'`.

Each row starts with `'+|'` and has a `'|'` at each column
boundary. There must be at least one `'  '`  (space) before
and after each `'|'`.

The contents of a cell may span multiple lines by using
continuation rows that start with `' |'`.

```
++--------+------------------+--------+
+| Cell1  | Lots and lots of | Cell3  |
 |        | content here in  |        |
 |        | cell 2           |        |
+| Cell4  | Cell5            | Cell6  |
++--------+------------------+--------+
```

## Header row

TODO

## Table cell alignment

```
++---------+------------+---------+
+| Left    |   Center   |   Right |
 | align   |   align    |   align |
++---------+------------+---------+
```

Horizontal alignment is typically inferred from the position of
the text in the cell:

* Left align cells have exactly 1 space on the left and at least
1 space on the right around the cell data.

* Center align cells have at least 2 spaces on each side of the
cell data.

* Right align cells have exactly 1 space on the right and at
least 2 spaces on the left around the cell data.

A single space on both sides of the cell data defaults to left
alignment.

### Explicit table cell alignment

Alignment can be explicitly specified using
an alignment line immediately before any row:

```
@|H        V|
```

where:

* H = horizontal alignment:
     `'<'` (left), `':'` (center), `'.'` (split), `'>'` (right), `' '` (infer)
* V = vertical alignment:
    `'^'` (top), `'-'` (center), `'v'` (bottom)

By default, H = `' '` (infer) and V = `'^'` (top)

The 'split' horizontal alignment requires that a split point be specified
with `':'`:

```
++----------+----------+
@|<        v|.    :   v|
+| Dogs     |    20    |
+| Cats     |  1370    |
+| Raccoons |     0.5  |
++----------+----------+
```

Everything in the cell up to and including the split point
will be right-aligned and everything after the split point
will be left aligned.

## Cell Spanning

Table cells can only span multiple columns or rows if the
table has border lines.

To span multiple rows or columns, remove the border
between cells:

```
++-------+-------+-------+-------+
+|   A   |   B   |   C   |       |
+|-------+-------+-------|       |
 |   E   |      F+G      | D+H+L |
+|-------+-------+-------|       |
 |      I+J      |   K   |       |
++-------+-------+-------+-------+
```

The spanned cell must be rectangular in shape.

Note that the border intersections in the divider lines can
be either `'+'` or `'|'`, the choice is purely aesthetic.

The start table and end table lines must always use `'+'`.
