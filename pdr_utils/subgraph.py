import os
import requests
from web3 import Web3

OPF_OWNER_ADDRS = "" # default owner addrs, separated by comma

def query_subgraph(query):
    subgraph_url = os.getenv("SUBGRAPH_URL")
    request = requests.post(subgraph_url, "", json={"query": query}, timeout=1.5)
    if request.status_code != 200:
        # pylint: disable=broad-exception-raised
        raise Exception(
            f"Query failed. Url: {subgraph_url}. Return code is {request.status_code}\n{query}"
        )
    result = request.json()
    return result


def satisfies_filters(nft_data, filters):
    if not nft_data:
        return True

    for filter_key, filter_values in filters.items():
        if not filter_values:
            continue

        values = [
            nft_data_item["value"] for nft_data_item in nft_data
            if nft_data_item["key"] == Web3.keccak(filter_key.encode("utf-8")).hex()
        ]

        if not values:
            continue

        value = values[0]

        if value not in filter_values:
            return False

    return True


def hexify_keys(env_var):
    keys = os.getenv(env_var, None)

    if not keys:
        return None

    keys = keys.split(",")

    return [Web3.to_hex(text=key) for key in keys]


def filter_by_owners(contracts, owner_addrs):
    return [
        contract for contract in contracts
        if contract["token"]["nft"]["owner"]["id"] in owner_addrs
    ]

def filter_contracts(contracts):
    owner_addrs = os.getenv("OWNER_ADDRS", owner_addrs).split(",")
    owner_filtered_contracts = filter_by_owners(contracts, owner_addrs)

    filters = {
        "pair": hexify_keys("PAIR_FILTER"),
        "timeframe": hexify_keys("TIMEFRAME_FILTER"),
        "source": hexify_keys("SOURCE_FILTER")
    }

    filtered = [
        contract for contract in owner_filtered_contracts
        if satisfies_filters(
            contract["token"]["nft"]["nftData"],
            filters
        )
    ]

    return pts_filtered


def get_all_interesting_prediction_contracts():
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    contracts = {}

    while True:
        query = """
        {
            predictContracts(skip:%s, first:%s){
                id
                token {
                    id
                    name
                    symbol
                    nft {
                        owner {
                            id
                        }
                        nftData {
                            key
                            value
                        }
                    }
                }
                blocksPerEpoch
                blocksPerSubscription
                truevalSubmitTimeoutBlock
            }
        }
        """ % (
            offset,
            chunk_size,
        )
        offset += chunk_size
        try:
            result = query_subgraph(query)
            new_orders = filter_contracts(result["data"]["predictContracts"])

            if new_orders == []:
                break
            for order in new_orders:
                contracts[order["id"]] = {
                    "name": order["token"]["name"],
                    "address": order["id"],
                    "symbol": order["token"]["symbol"],
                    "blocks_per_epoch": order["blocksPerEpoch"],
                    "blocks_per_subscription": order["blocksPerSubscription"],
                    "last_submited_epoch": 0,
                }
        except Exception as e:
            print(e)
            return {}
    return contracts
