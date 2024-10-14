# Node categories

## Extractor

The `Extractor` node is in charge of extracting data from a certain source. This could be anything
from a CSV file, a XLSX file, a DB, an API...

It will yield Items from a function we call `extract()`.

---

### Configuration

- **bucket_size**
    - type: `int`
    - default: 1000
    - Size on which the extracted items will be packaged and enqueued to be sent to children Nodes.

- **run_in_main_process**
    - type: `bool`
    - default: True
    - If True, the Node will run with a thread in the main process. If False, the Node will run in
      its own spawned process.

## Transformer

The `Transformer` Node is in charge of transforming Items.

Every Transformer node will have a `transform(item)` that will receive an Item and return its
transformed version.

---

### Configuration

- **input_key**
    - type: `str`
    - default: None
    - Optional. When provided, if the incoming Item is a dict, the Node will receive `item
  [input_key]`. If the item is not a dict, the Node will receive `item.input_key`.

- **run_in_main_process**
    - type: `bool`
    - default: True
    - If True, the Node will run with a thread in the main process. If False, the Node will run in
      its own spawned process.

## Filter

The `Filter` Node is in charge of filtering out Items.

Every Filter node will have a `filter(item)` that receives an Item and will return the item or
not (None) if this item meets a certain condition.

---

### Configuration

todo

## Loader

The Loader node is in charge of loading Items: storing the items in a DB, a file, a Python object...

Every Loader node will implement a `load(item)` method which will load the incoming Item.

---

### Configuration

todo

## Bulking

### Bulker

Bulker nodes will store Items in a bulk/batch (a Python list really) until it reaches a maximum
size. When that happens, the bulk is passed as an Item by itself onto the connected children Nodes.

---

### Configuration

todo

### DeBulker

DeBulker nodes will unpack the Items contained in an incoming bulk Item (this can be a list of
items, a set, a previously bulked set of Items, etc...) and produce them as individual Items
onto the connected children nodes.

---

### Configuration

todo
