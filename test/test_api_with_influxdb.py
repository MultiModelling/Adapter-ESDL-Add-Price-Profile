import requests

api_endpoint = "http://localhost:9202"


res = requests.get(api_endpoint + '/status')
if res.ok:
    print("Endpoint /status ok! ", res)
else:
    print("Endpoint /status not ok! ")
    exit(1)

model_run_id = None
res = requests.get(api_endpoint + '/model/request')
if res.ok:
    print("Endpoint /model/request ok!")
    result = res.json()
    print(result)
    model_run_id = result['model_run_id']
else:
    print("Endpoint /model/request not ok!")
    exit(1)

post_body = {
    "base_path": "bedrijventerreinommoord/Scenario_1_II3050_Nationale_Sturing/Trial_1/MM_workflow_run_1/",
    "input_esdl_file_path": "ESDL_add_price_profile_adapter/Hybrid HeatPump.esdl",
    "input_csv_file_path": "ETM_price_profile_adapter/elektrictitetisprijs_profiel.csv",
    "output_file_path": "ESDL_add_price_profile_adapter/HHP_profile.esdl",
    "replace_year": 2019,
    "influxdb_config": {
        "host": "localhost",
        "port": 8086,
        "esdl_host": "http://influxdb",
        "esdl_port": 8086,
        "database": "mmvib",
        "measurement": "bedrijventerreinommoord",
        "field": "E_prijs_EUR_per_MWh"
    }
}

res = requests.post(api_endpoint + '/model/initialize/' + model_run_id, json=post_body)
if res.ok:
    print("Endpoint /model/initialize ok!")
    result = res.json()
    print(result)
else:
    print("Endpoint /model/initialize not ok!")
    exit(1)

res = requests.get(api_endpoint + '/model/run/' + model_run_id)
if res.ok:
    print("Endpoint /model/run ok!")
    result = res.json()
    print(result)
else:
    print("Endpoint /model/run not ok!")
    exit(1)

res = requests.get(api_endpoint + '/model/status/' + model_run_id)
if res.ok:
    print("Endpoint /model/status ok!")
    result = res.json()
    print(result)
else:
    print("Endpoint /model/status not ok!")
    exit(1)

res = requests.get(api_endpoint + '/model/results/' + model_run_id)
if res.ok:
    print("Endpoint /model/results ok!")
    result = res.json()
    print(result)
else:
    print("Endpoint /model/results not ok!")
    exit(1)

res = requests.get(api_endpoint + '/model/remove/' + model_run_id)
if res.ok:
    print("Endpoint /model/remove ok!")
    result = res.json()
    print(result)
else:
    print("Endpoint /model/remove not ok!")
    exit(1)




