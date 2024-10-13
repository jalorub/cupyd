from abc import abstractmethod
from copy import deepcopy
from functools import partial
from multiprocessing import Queue as MultiprocessingQueue
from queue import Queue
from threading import Thread
from time import perf_counter
from typing import List, Optional, Union, Any, Iterator

from cupyd.core.communication import Connector, InterProcessEventFlag
from cupyd.core.communication.connector import IntraProcessConnector
from cupyd.core.communication.counter import MPCounter
from cupyd.core.constants.node_actions import (
    START,
    FINALIZE,
    UPDATE_COUNTER,
    PRODUCE_BUCKET,
    PRODUCE_TIMING,
    PROCESS_BUCKET,
    CONSUME_BUCKET,
    GENERATE_BUCKET,
)
from cupyd.core.constants.sentinel_values import NO_MORE_ITEMS
from cupyd.core.graph.classes import Node
from cupyd.core.models.node_exception import NodeException
from cupyd.core.nodes.bulker import Bulker
from cupyd.core.nodes.debulker import DeBulker
from cupyd.core.nodes.extractor import Extractor
from cupyd.core.nodes.filter import Filter
from cupyd.core.nodes.loader import Loader
from cupyd.core.nodes.transformer import Transformer


def _set_copy_bucket_on_produce(output_connectors: List[Connector]) -> List[Connector]:
    """Determine which connectors need a pre-copy of the bucket before producing them."""

    intra_process_connector_found = False

    for connector in output_connectors:
        if isinstance(connector, IntraProcessConnector):
            if intra_process_connector_found:
                connector.copy_bucket_on_produce = True
            else:
                intra_process_connector_found = True

    return output_connectors


def get_item_value_by_key(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item[key]
    else:
        return getattr(item, key)


def _extractor_item_generator(extractor: Extractor) -> Iterator[List[Any]]:
    for item in extractor.extract():
        yield item


def _transformer_process_bucket(
    bucket: List[Any],
    transformer: Transformer,
    input_key: Optional[str],
) -> List[Any]:
    """Run the transform() method on every item from a bucket."""

    processed_bucket = []

    for item in bucket:

        if input_key:
            value = get_item_value_by_key(item=item, key=input_key)
            result = transformer.transform(value)
        else:
            result = transformer.transform(item)

        processed_bucket.append(result)

    return processed_bucket


def _filter_process_bucket(
    bucket: List[Any],
    filter_node: Filter,
    value_to_filter: Any,
    disable_safe_copy: bool,
    input_key: Optional[str],
) -> List[Any]:
    """Run the filter() method on every item from a bucket."""

    filtered_bucket = []

    items = bucket if disable_safe_copy else deepcopy(bucket)

    for item_idx, item in enumerate(items):

        if input_key:
            value = get_item_value_by_key(item=item, key=input_key)
            result = filter_node.filter(value)
        else:
            result = filter_node.filter(item)

        if result != value_to_filter:
            filtered_bucket.append(bucket[item_idx])

    return filtered_bucket


def _loader_process_bucket(
    bucket: List[Any],
    loader: Loader,
    has_outputs: bool,
    disable_safe_copy: bool,
    input_key: Optional[str],
) -> List[Any]:
    """Run the load() method on every item from a bucket."""

    # If the Loader output items are passed onto another Node, then, as a safety measure (unless
    # disabled), it will load a copy of the incoming bucket instead of the original one
    if has_outputs:
        items = bucket if disable_safe_copy else deepcopy(bucket)
        for item in items:
            if input_key:
                value = get_item_value_by_key(item=item, key=input_key)
                loader.load(value)
            else:
                loader.load(item)
    else:
        for item in bucket:
            if input_key:
                value = get_item_value_by_key(item=item, key=input_key)
                loader.load(value)
            else:
                loader.load(item)

    return bucket


class NodeWorker(Thread):

    def __init__(
        self,
        node: Union[Node, Extractor, Transformer, Filter, Loader, Bulker, DeBulker],
        input_connector: Optional[Connector],
        output_connectors: List[Connector],
        counter: Optional[MPCounter],
        finished_threads_queue: Queue,
        stop_event: InterProcessEventFlag,
        pause_event: InterProcessEventFlag,
        monitor_performance: InterProcessEventFlag,
        node_timings: MultiprocessingQueue,
    ):
        super().__init__(name=node.name)
        self.node = node
        self.input_connector = input_connector
        self.output_connectors = output_connectors
        self.counter = counter
        self.finished_threads_queue = finished_threads_queue
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.node_timings = node_timings
        self.monitor_performance = monitor_performance
        self.exception_found: Optional[NodeException] = None
        self.skip_processing = False
        self.is_node_terminal = isinstance(self.node, Loader) and not self.node.outputs

    def run(self):
        # todo: could this be determined beforehand? should be possible, at build() step
        self.output_connectors = _set_copy_bucket_on_produce(self.output_connectors)

        if not isinstance(self.node, Bulker) and not isinstance(self.node, DeBulker):
            try:
                self.node.start()
            except Exception as exc:
                self.exception_found = NodeException(exc=exc, action=START)

        if not self.exception_found:
            self._run()

        if not isinstance(self.node, Bulker) and not isinstance(self.node, DeBulker):
            try:
                if self.exception_found:
                    self.node.handle_exception(self.exception_found)
                else:
                    self.node.finalize()
            except Exception as e:
                self.exception_found = NodeException(exc=e, action=FINALIZE)

        self.finished_threads_queue.put((self.node.id, self.exception_found))

    @abstractmethod
    def _run(self):
        pass

    def _handle_exception(self, exception: Exception, action: str) -> None:
        if not self.stop_event:
            self.stop_event.set()
        if not self.exception_found:  # don't replace original exception in case another one occurs
            self.exception_found = NodeException(exc=exception, action=action)
        self.skip_processing = True


class ExtractorWorker(NodeWorker):

    def _run(self):
        self.node: Extractor

        bucket: List[Any] = []
        stop_iteration = False
        start_time: Optional[float] = None
        bucket_size = self.node.configuration.bucket_size
        generator = _extractor_item_generator(extractor=self.node)

        while not self.stop_event:

            if self.pause_event:
                self.pause_event.wait()

            # generate a bucket of items
            try:
                start_time = perf_counter() if self.monitor_performance else None

                while len(bucket) < bucket_size:
                    bucket.append(next(generator))

            except StopIteration:
                stop_iteration = True
            except Exception as e:
                self.exception_found = NodeException(exc=e, action=GENERATE_BUCKET)
                break

            # produce the bucket to the output connectors of the node
            if bucket:
                try:
                    for connector in self.output_connectors:
                        connector.produce(bucket)
                except Exception as e:
                    self.exception_found = NodeException(exc=e, action=PRODUCE_BUCKET)
                    break

                try:
                    if start_time:
                        timing = (perf_counter() - start_time) / len(bucket)
                        self.node_timings.put((self.node.id, timing))
                except Exception as e:
                    self.exception_found = NodeException(exc=e, action=PRODUCE_TIMING)
                    break

                bucket = []

            if stop_iteration:
                break


class ProcessorWorker(NodeWorker):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.node, Transformer):
            self._process_bucket_function = partial(
                _transformer_process_bucket,
                transformer=self.node,
                input_key=self.node.configuration.input_key,
            )
        elif isinstance(self.node, Loader):
            self._process_bucket_function = partial(
                _loader_process_bucket,
                loader=self.node,
                has_outputs=bool(self.node.outputs),
                disable_safe_copy=self.node.configuration.disable_safe_copy,
                input_key=self.node.configuration.input_key,
            )
        elif isinstance(self.node, Filter):
            self._process_bucket_function = partial(
                _filter_process_bucket,
                filter_node=self.node,
                value_to_filter=self.node.configuration.value_to_filter,
                disable_safe_copy=self.node.configuration.disable_safe_copy,
                input_key=self.node.configuration.input_key,
            )
        else:
            raise TypeError(f"Invalid node type: {type(self.node)}")

    # TODO: Might be useful to know which item value caused the error
    def _run(self):
        timing: Optional[float] = None
        bucket = None

        while True:
            # consume a bucket of items
            try:
                bucket = self.input_connector.consume()
                if bucket is NO_MORE_ITEMS:
                    break
            except Exception as e:
                self._handle_exception(exception=e, action=CONSUME_BUCKET)

            if self.stop_event:
                self.skip_processing = True

            if self.skip_processing:
                continue

            if self.pause_event:
                self.pause_event.wait()

            # process the bucket
            # todo: detect the stop or pause event as soon its set, checking on every item
            #  instead on every bucket? Add timeout to avoid hanging processing after stop was set?
            try:
                start_time = perf_counter() if self.monitor_performance else None

                bucket = self._process_bucket_function(bucket)

                if start_time and bucket:
                    timing = (perf_counter() - start_time) / len(bucket)

            except Exception as e:
                self._handle_exception(exception=e, action=PROCESS_BUCKET)
            else:
                # produce the bucket to the output connectors of the node
                try:
                    for connector in self.output_connectors:
                        connector.produce(bucket)
                except Exception as e:
                    self._handle_exception(exception=e, action=PRODUCE_BUCKET)
                    continue

                try:
                    if timing:
                        self.node_timings.put((self.node.id, timing))
                        timing = None
                except Exception as e:
                    self._handle_exception(exception=e, action=PRODUCE_TIMING)
                    continue

                try:
                    if self.counter:
                        self.counter.increase(amount=len(bucket))
                except Exception as e:
                    self._handle_exception(exception=e, action=UPDATE_COUNTER)
                    continue


class BulkerWorker(NodeWorker):

    def _run(self):
        self.node: Bulker

        bulk = []
        bulk_size = self.node.bulk_size  # TODO: allow changing bulk size dynamically?

        while True:

            # consume a bucket of items
            try:
                bucket = self.input_connector.consume()
                if bucket is NO_MORE_ITEMS:
                    break
            except Exception as e:
                self._handle_exception(exception=e, action=CONSUME_BUCKET)
                continue

            if self.stop_event:
                self.skip_processing = True

            if self.skip_processing:
                continue

            if self.pause_event:
                self.pause_event.wait()

            try:
                bulk.extend(bucket)

                if len(bulk) >= bulk_size:
                    remaining_items = None

                    for chunk in self._chunk(items=bulk, bulk_size=bulk_size):
                        if len(chunk) == bulk_size:
                            for connector in self.output_connectors:
                                connector.produce([chunk])
                        else:
                            remaining_items = chunk

                    bulk = remaining_items or []

            except Exception as e:
                self._handle_exception(exception=e, action=PRODUCE_BUCKET)
                continue

        # if there are remaining items, produce them
        if bulk and self.exception_found is None:
            try:
                for connector in self.output_connectors:
                    connector.produce([bulk])
            except Exception as e:
                self._handle_exception(exception=e, action=PRODUCE_BUCKET)

    @staticmethod
    def _chunk(items: List[Any], bulk_size: int) -> Iterator[List[Any]]:
        for i in range(0, len(items), bulk_size):
            yield items[i : i + bulk_size]  # noqa


class DeBulkerWorker(NodeWorker):

    def _run(self):
        while True:

            # consume a bucket of items
            try:
                bucket = self.input_connector.consume()
                if bucket is NO_MORE_ITEMS:
                    break
            except Exception as e:
                self._handle_exception(exception=e, action=CONSUME_BUCKET)
                continue

            if self.stop_event:
                self.skip_processing = True

            if self.skip_processing:
                continue

            if self.pause_event:
                self.pause_event.wait()

            try:
                for item in bucket:
                    for connector in self.output_connectors:
                        connector.produce(item)
            except Exception as e:
                self._handle_exception(exception=e, action=PRODUCE_BUCKET)
                continue
