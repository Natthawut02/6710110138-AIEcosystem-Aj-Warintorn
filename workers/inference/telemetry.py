"""
telemetry.py (Inference Worker)
--------------------------------
Provides OpenTelemetry setup (Traces, Metrics, Logs) for the AI Inference Worker.
Routes telemetry data via OTLP gRPC to the OpenTelemetry Collector.
"""

import os
import logging
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Try importing OTLP gRPC exporters
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False

try:
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry._logs import set_logger_provider
    OTLP_LOGS_AVAILABLE = True
except ImportError:
    OTLP_LOGS_AVAILABLE = False

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "inference-worker")
RAW_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317")
OTEL_ENDPOINT = RAW_ENDPOINT.replace("http://", "").replace("https://", "")

tracer = None
meter = None
ner_requests_counter = None
ner_duration_histogram = None
ner_entities_counter = None


def setup_telemetry(service_name: str = SERVICE_NAME):
    """
    Initializes OpenTelemetry Tracing, Metrics, and Logging exporters.
    """
    global tracer, meter, ner_requests_counter, ner_duration_histogram, ner_entities_counter

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
    })

    # 1. Setup Tracing
    tracer_provider = TracerProvider(resource=resource)
    if OTLP_AVAILABLE:
        try:
            span_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        except Exception as e:
            logging.warning(f"Could not initialize OTLP SpanExporter: {e}")

    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("ner.inference.tracer")

    # 2. Setup Metrics
    if OTLP_AVAILABLE:
        try:
            metric_exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
            reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
            metrics.set_meter_provider(meter_provider)
        except Exception as e:
            logging.warning(f"Could not initialize OTLP MetricExporter: {e}")
            meter_provider = MeterProvider(resource=resource)
            metrics.set_meter_provider(meter_provider)
    else:
        meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter("ner.inference.meter")

    # Defined Metrics
    ner_requests_counter = meter.create_counter(
        name="ner_requests_total",
        description="Total number of NER inference requests processed",
        unit="1",
    )
    ner_duration_histogram = meter.create_histogram(
        name="ner_inference_duration_seconds",
        description="Latency distribution of NER inference execution",
        unit="s",
    )
    ner_entities_counter = meter.create_counter(
        name="ner_entities_detected_total",
        description="Total number of named entities detected",
        unit="1",
    )

    # 3. Setup Logs Exporter (Bridge python logging to OTel Collector -> Loki)
    if OTLP_LOGS_AVAILABLE and OTLP_AVAILABLE:
        try:
            logger_provider = LoggerProvider(resource=resource)
            set_logger_provider(logger_provider)
            log_exporter = OTLPLogExporter(endpoint=OTEL_ENDPOINT, insecure=True)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

            handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
            logging.getLogger().addHandler(handler)
        except Exception as e:
            logging.warning(f"Could not initialize OTLP LogExporter: {e}")

    logging.info(f"OpenTelemetry initialized for '{service_name}' -> Collector at {OTEL_ENDPOINT}")


def get_tracer():
    global tracer
    if tracer is None:
        tracer = trace.get_tracer("ner.inference.tracer")
    return tracer


def get_metrics():
    global ner_requests_counter, ner_duration_histogram, ner_entities_counter
    return ner_requests_counter, ner_duration_histogram, ner_entities_counter
