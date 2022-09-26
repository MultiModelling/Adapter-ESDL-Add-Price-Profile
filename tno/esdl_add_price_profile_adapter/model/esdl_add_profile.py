from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

import pytz

from tno.esdl_add_price_profile_adapter.model.model import Model, ModelState
from tno.esdl_add_price_profile_adapter.types import ESDLAddPriceProfileAdapterConfig, InfluxDBConfig

from esdl import esdl
from esdl.esdl_handler import EnergySystemHandler

from influxdb import InfluxDBClient

ETM_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
INFLUXDB_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:00+0000"

cet = pytz.timezone("Europe/Amsterdam")
utc = pytz.timezone("UTC")


class ESDLAddProfile(Model):

    @staticmethod
    def parse_etm_datetime(dt_str):
        dt = datetime.strptime(dt_str, ETM_DATETIME_FORMAT)
        cet_dt = cet.localize(dt)           # Assume CET timezone for dates returned by ETM
        utc_dt = cet_dt.astimezone(utc)     # Convert them to UTC...
        return utc_dt

    @staticmethod
    def process_csv_bytes(csv_bytes, replace_year):
        csv_str = csv_bytes.decode('utf-8')

        curve_lines_str = csv_str.split('\n')
        curve_lines = [line.split(',') for line in curve_lines_str]
        curve_lines.pop(0)              # Remove header
        while curve_lines[-1] == ['']:  # Last line(s) can be empty
            curve_lines.pop(-1)

        if replace_year:
            curve_values = [[ESDLAddProfile.parse_etm_datetime(v[0].replace('2050', str(replace_year))), float(v[1])]
                            for v in curve_lines]
        else:
            curve_values = [[ESDLAddProfile.parse_etm_datetime(v[0]), float(v[1])] for v in curve_lines]
        return curve_values

    @staticmethod
    def upload_profile(influxdb_config: InfluxDBConfig, profile_array):
        use_ssl = influxdb_config.host.startswith('https')
        if influxdb_config.host.startswith('http'):     # matches http or https
            host_without_protocol = influxdb_config.host.split('://')[1]
        else:
            host_without_protocol = influxdb_config.host

        client = InfluxDBClient(
            host=host_without_protocol,
            port=influxdb_config.port,
            username=influxdb_config.username,
            password=influxdb_config.password,
            database=influxdb_config.database,
            ssl=use_ssl
        )
        if influxdb_config.database not in client.get_list_database():
            client.create_database(influxdb_config.database)

        json_body = []

        for profile_element in profile_array:
            fields = dict()
            fields[influxdb_config.field] = float(profile_element[1])

            json_body.append({
                "measurement": influxdb_config.measurement,
                "time": datetime.strftime(profile_element[0], INFLUXDB_DATETIME_FORMAT),
                "fields": fields
            })

        client.write_points(points=json_body, database=influxdb_config.database, batch_size=100)

    @staticmethod
    def create_esdl_timeseries_profile(profile_array):
        start_dt = profile_array[0][0]

        profile = esdl.TimeSeriesProfile(
            id=str(uuid4()),
            startDateTime=start_dt,
            timestep=3600,
            values=[v[1] for v in profile_array]
        )
        profile.profileQuantityAndUnit = esdl.QuantityAndUnitType(
            id=str(uuid4()),
            physicalQuantity=esdl.PhysicalQuantityEnum.COST,
            unit=esdl.UnitEnum.EURO,
            perMultiplier=esdl.MultiplierEnum.MEGA,
            perUnit=esdl.UnitEnum.WATTHOUR,
            description="COST in EUR/MWh"
        )

        return profile

    @staticmethod
    def create_esdl_influxdb_profile(influxdb_config: InfluxDBConfig, profile_array):
        start_dt = profile_array[0][0]
        end_dt = profile_array[-1][0]

        host = influxdb_config.esdl_host if influxdb_config.esdl_host else influxdb_config.host
        port = influxdb_config.esdl_port if influxdb_config.esdl_port else influxdb_config.port

        profile = esdl.InfluxDBProfile(
            id=str(uuid4()),
            host=host,
            port=port,
            database=influxdb_config.database,
            measurement=influxdb_config.measurement,
            field=influxdb_config.field,
            startDate=start_dt,
            endDate=end_dt,
        )
        profile.profileQuantityAndUnit = esdl.QuantityAndUnitType(
            id=str(uuid4()),
            physicalQuantity=esdl.PhysicalQuantityEnum.COST,
            unit=esdl.UnitEnum.EURO,
            perMultiplier=esdl.MultiplierEnum.MEGA,
            perUnit=esdl.UnitEnum.WATTHOUR,
            description="COST in EUR/MWh"
        )

        return profile

    def process_results(self, result):
        if self.minio_client:
            return result
        else:
            return result

    def run(self, model_run_id: str):
        model_run_info = Model.run(self, model_run_id=model_run_id)

        if model_run_info.state == ModelState.ERROR:
            return model_run_info

        config: ESDLAddPriceProfileAdapterConfig = self.model_run_dict[model_run_id].config

        input_csv_bytes = self.load_from_minio(config.input_csv_file_path)
        profile_array = ESDLAddProfile.process_csv_bytes(input_csv_bytes, config.replace_year)

        influxdb_profile = False
        if config.influxdb_config:
            ESDLAddProfile.upload_profile(config.influxdb_config, profile_array)
            influxdb_profile = True

        input_esdl_bytes = self.load_from_minio(config.input_esdl_file_path)
        input_esdl = input_esdl_bytes.decode('utf-8')

        esh = EnergySystemHandler()
        es = esh.load_from_string(input_esdl)

        esi: esdl.EnergySystemInformation = es.energySystemInformation
        if esi:
            carrs: esdl.Carriers = esi.carriers
            for carr in carrs.carrier:
                if isinstance(carr, esdl.ElectricityCommodity):
                    if influxdb_profile:
                        carr.cost = ESDLAddProfile.create_esdl_influxdb_profile(config.influxdb_config, profile_array)
                    else:
                        carr.cost = ESDLAddProfile.create_esdl_timeseries_profile(profile_array)

        es_str = esh.to_string()

        model_run_info = Model.store_result(self, model_run_id=model_run_id, result=es_str)
        return model_run_info
