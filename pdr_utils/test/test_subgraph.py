import pytest
from web3 import Web3
from pdr_utils.subgraph import satisfies_filters, hexify_keys, filter_by_owners


encoded_pair = Web3.keccak("pair".encode("utf-8")).hex()
encoded_timeframe = Web3.keccak("timeframe".encode("utf-8")).hex()


def test_satisfies_filters():
    # no nft data => will not be filtered out
    assert satisfies_filters(None, {"a", "b"})

    # no filters => will not be filtered out
    assert satisfies_filters({"a": "b"}, {})

    # one filter
    assert satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": "another", "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x123"]}
    )

    assert not satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": "another", "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x1234"]}
    )

    assert satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": "another", "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": []}
    )

    # multiple filters both matching
    assert satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": encoded_timeframe, "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x123"], "timeframe": ["0x1234"]}
    )

    # multiple filters: one matching, one not
    assert not satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": encoded_timeframe, "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x123"], "timeframe": ["0x123"]}
    )

    # multiple possibilities for one filter
    assert satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": encoded_timeframe, "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x123"], "timeframe": ["0x123", "0x1234"]}
    )

    # multiple filters: one matching,
    # the other is missing from nft_data so it doesn't filter out
    assert satisfies_filters(
        [
            {"key": encoded_pair, "value": "0x123"},
            {"key": "another2", "value": "0x1234"},
            {"key": "another3", "value": "0x12345"},
        ], {"pair": ["0x123"], "timeframe": ["0x123"]}
    )


def test_hexify_keys(monkeypatch):
    monkeypatch.setenv("PAIR_FILTER", "0x123,0x456")
    monkeypatch.setenv("TIMEFRAME_FILTER", "")

    assert hexify_keys("PAIR_FILTER") == ["0x3078313233", "0x3078343536"]
    assert hexify_keys("TIMEFRAME_FILTER") is None
    assert hexify_keys("SOURCE_FILTER") is None


@pytest.mark.parametrize(
    "contracts, owner_addrs, expected_result",
    [
        (
            [
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address2"}}}},
                {"token": {"nft": {"owner": {"id": "address3"}}}}
            ],
            ["address1", "address3"],
            [
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address3"}}}}
            ]
        ),
        (
            [
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address3"}}}}
            ],
            ["address1", "address2"],
            [
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
                {"token": {"nft": {"owner": {"id": "address1"}}}},
            ]
        ),
    ]
)
def test_filter_by_owners(contracts, owner_addrs, expected_result):
    result = filter_by_owners(contracts, owner_addrs)
    assert result == expected_result
