# DATA ETL

Framework to easily create ETL processes.

Key features:

- Simple, flexible syntax.
- ETLs that will run on multiple workers without the need of writing multiprocessing code.
- High compatibility:
    - Works in Unix, Windows & MacOS.
    - Python >= 3.9
- Light: no dependencies required for its core version.
    - The API version will require [Falcon](https://falcon.readthedocs.io/en/stable/index.html),
      which is a minimalist ASGI/WSGI framework that doesn't require other packages to work.
    - The Dashboard version (full version) will require Falcon and [Dash](https://dash.plotly.com/).

## TODO

- Optimize measuring the Node performance
    - Avoid blocking queue (BUT when using
      SimpleQueue [we got this error on Windows](https://github.com/python/cpython/blob/120729d862f0ef9979508899f7f63a9f3d9623cb/Lib/multiprocessing/connection.py#L289))
    - use some kind of buffer that doesn't care about loosing items?
    - run the measurements more sparsely? every X batches?
- Improve logs (add ETA, avg time per item, overhead?)
- Handle node validation types
- Add total_items retrieval in Extractor. Allow retrieving that value at any moment?
    - It could be a multiprocessing Value, which could be set at the extract() method so we don't
      need to instantiate client at start() to get count, but we could do it at extract already if
      we want
- Node configuration parameters validation
- Allow arbitrary number of workers on each node? (except normal Extractors)
- Implement PartitionedExtractor so it runs without a MP queue
- When logging exceptions, log at which action the error occurred (start, finalize...)
- Be able to detect when an ETLWorker got killed incorrectly (for example externally killed?).
  This means we need to:
    - Trigger the stop event
    - Launch some worker replacement that will be able to finish the shutdown orchestration of the
      ETL. In other words, consume remaining/hung up items in queues + produce required Sentinel
      values in order to shut down the nodes from top to bottom in the ETL.
- As an ETL will only stop/finish when all its Node were finalized, we need to handle cases where
  the stop event is set but processing a bucket in Node X takes too long, ideally we should be able
  to:
    - Check if the stop event was set on every processed item (how much overhead?) instead per
      bucket.
    - Add timeout when processing an item/bucket as soon the stop event is set, to avoid hanging
      the ETL too much.
- Validate Node configuration settings
- Add tests: for interruptions, handle killed workers, etc...
- Add documentation (mkdocs?)