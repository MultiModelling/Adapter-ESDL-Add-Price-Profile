from enum import Enum
from typing import Dict, Optional, Any, ClassVar, Type
from marshmallow_dataclass import dataclass
from dataclasses import field

from marshmallow import Schema, fields


class ModelState(str, Enum):
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    ERROR = "ERROR"


@dataclass
class InfluxDBConfig:
    host: Optional[str] = None
    port: Optional[int] = None
    esdl_host: Optional[str] = None
    esdl_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    measurement: Optional[str] = None
    field: Optional[str] = None


@dataclass
class ESDLAddPriceProfileAdapterConfig:
    input_esdl_file_path: Optional[str] = None
    input_csv_file_path: Optional[str] = None
    output_file_path: Optional[str] = None
    replace_year: Optional[int] = None
    influxdb_config: Optional[InfluxDBConfig] = None


@dataclass
class ModelRun:
    state: ModelState
    config: ESDLAddPriceProfileAdapterConfig
    result: dict


@dataclass(order=True)
class ModelRunInfo:
    model_run_id: str
    state: ModelState = field(default=ModelState.UNKNOWN)
    result: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

    # support for Schema generation in Marshmallow
    Schema: ClassVar[Type[Schema]] = Schema
