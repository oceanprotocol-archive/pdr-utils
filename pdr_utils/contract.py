import json
import os
import glob
import time

from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend

from pathlib import Path
from web3 import Web3, HTTPProvider, WebsocketProvider
from web3.middleware import construct_sign_and_send_raw_middleware
from os.path import expanduser

rpc_url = os.environ.get("RPC_URL")
assert rpc_url is not None, "You must set RPC_URL environment variable"
private_key = os.environ.get("PRIVATE_KEY")
assert private_key is not None, "You must set PRIVATE_KEY environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"

# instantiate Web3 instance
w3 = Web3(Web3.HTTPProvider(rpc_url))
account: LocalAccount = Account.from_key(private_key)
owner = account.address
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))

class ContractConfig:
    def __init__(self, rpc_url: str, private_key: str):
        self.rpc_url = rpc_url or os.environ.get("RPC_URL")

        if rpc_url is None:
            raise ValueError("You must set RPC_URL environment variable")

        if private_key is None:
            raise ValueError("You must set PRIVATE_KEY environment variable")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            if not private_key.startswith("0x"):
                raise ValueError("Private key must start with 0x hex prefix")
            self.account: LocalAccount = Account.from_key(private_key)
            self.owner = self.account.address
            self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(self.account))



class Token:
    def __init__(self, config: ContractConfig, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(address=config.w3.to_checksum_address(address), abi=get_contract_abi('ERC20Template3'))
        self.config = config
    
    def allowance(self,account,spender):
        return self.contract_instance.functions.allowance(account,spender).call()

    def balanceOf(self,account):
        return self.contract_instance.functions.balanceOf(account).call()
    
    def approve(self,spender,amount):
        gasPrice = w3.eth.gas_price
        #print(f"Approving {amount} for {spender} on contract {self.contract_address}")
        try:
            tx = self.contract_instance.functions.approve(spender,amount).transact({"from":owner,"gasPrice":gasPrice})
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except:
            return None


class PredictorContract:
    def __init__(self, config: ContractConfig, address: str):
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(address=config.w3.to_checksum_address(address), abi=get_contract_abi('ERC20Template3'))
        self.token = Token(config, stake_token)
        stake_token=self.get_stake_token()

    def is_valid_subscription(self):
        return self.contract_instance.functions.isValidSubscription(owner).call()
    
    def get_empty_provider_fee(self):
        return {
            "providerFeeAddress": ZERO_ADDRESS,
            "providerFeeToken": ZERO_ADDRESS,
            "providerFeeAmount": 0,
            "v": 0,
            "r": 0,
            "s": 0,
            "validUntil": 0,
            "providerData": 0,
        }
    def string_to_bytes32(self,data):
        if len(data) > 32:
            myBytes32 = data[:32]
        else:
            myBytes32 = data.ljust(32, '0')
        return bytes(myBytes32, 'utf-8')
    def get_auth_signature(self):
        valid_until = int(time.time()) + 3600
        message_hash = w3.solidity_keccak(
        ["address", "uint256"],
        [
            owner,
            valid_until
        ],
        )
        pk = keys.PrivateKey(account.key)
        prefix = "\x19Ethereum Signed Message:\n32"
        signable_hash = w3.solidity_keccak(
            ["bytes", "bytes"], [w3.to_bytes(text=prefix), w3.to_bytes(message_hash)]
        )
        signed = keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)
        auth = {
            "userAddress": owner,
            "v": (signed.v + 27) if signed.v <= 1 else signed.v,
            "r": w3.to_hex(w3.to_bytes(signed.r).rjust(32, b"\0")),
            "s": w3.to_hex(w3.to_bytes(signed.s).rjust(32, b"\0")),
            "validUntil": valid_until,
        }
        return(auth)
    
    def buy_and_start_subscription(self,gasLimit):
        """ Buys 1 datatoken and starts a subscription"""
        fixed_rates=self.get_exchanges()
        if not fixed_rates:
            return
        (fixed_rate_address,exchange_id) = fixed_rates[0]
        # get datatoken price
        exchange = FixedRate(fixed_rate_address)
        (baseTokenAmount, oceanFeeAmount, publishMarketFeeAmount,consumeMarketFeeAmount) = exchange.get_dt_price(exchange_id)
        # approve
        self.token.approve(self.contract_instance.address,baseTokenAmount)
        # buy 1 DT
        gasPrice = w3.eth.gas_price
        provider_fees = self.get_empty_provider_fee()
        try:
            orderParams = (
                            owner,
                            0,
                            (
                                ZERO_ADDRESS,
                                ZERO_ADDRESS,
                                0,
                                0,
                                self.string_to_bytes32(''),
                                self.string_to_bytes32(''),
                                provider_fees["validUntil"],
                                w3.to_bytes(b'') ,
                            ),
                            (   
                                ZERO_ADDRESS,
                                ZERO_ADDRESS,
                                0
                            ),
                        )
            freParams=(
                            w3.to_checksum_address(fixed_rate_address),
                            w3.to_bytes(exchange_id),
                            baseTokenAmount,
                            0,
                            ZERO_ADDRESS,
                        )
            
            tx = self.contract_instance.functions.buyFromFreAndOrder(orderParams,freParams).build_transaction({"gas": gasLimit,'nonce': w3.eth.get_transaction_count(owner),"from":owner,"gasPrice":gasPrice})
            
            signed_txn = w3.eth.account.sign_transaction(tx,private_key)
            
            tx_id = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"tx_id: {tx_id}")
            #gas = self.contract_instance.functions.buyFromFreAndOrder(orderParams,freParams).estimate_gas({"from":owner,"gasPrice":gasPrice})
            #print(f"gas: {gas}")
            #tx_id = self.contract_instance.functions.buyFromFreAndOrder(orderParams,freParams).build_transaction({"from":owner,"gasPrice":gasPrice})
            #print(f"tx_id: {tx_id}")
            #receipt = w3.eth.wait_for_transaction_receipt(tx_id)
            #print(f"receipt: {receipt}")
            return tx_id
        except Exception as e:
            print(e)
            return None
    
    def buy_many(self,how_many,gasLimit):
        if how_many<1:
            return
        print(f"Buying {how_many} accesses....")
        for i in range(0,how_many):
            self.buy_and_start_subscription(gasLimit)
    
    def get_exchanges(self):
        return self.contract_instance.functions.getFixedRates().call()
    
    def get_stake_token(self):
        return self.contract_instance.functions.stakeToken().call()
    
    def get_price(self):
        fixed_rates=self.get_exchanges()
        if not fixed_rates:
            return
        (fixed_rate_address,exchange_id) = fixed_rates[0]
        # get datatoken price
        exchange = FixedRate(fixed_rate_address)
        (baseTokenAmount, oceanFeeAmount, publishMarketFeeAmount,consumeMarketFeeAmount) = exchange.get_dt_price(exchange_id)
        return baseTokenAmount
    
    def get_current_epoch(self):
        return self.contract_instance.functions.curEpoch().call()
    
    def get_blocksPerEpoch(self):
        return self.contract_instance.functions.blocksPerEpoch().call()
    
    def get_agg_predval(self, block):
        """ check subscription"""
        if not self.is_valid_subscription():
            print("Buying a new subscription...")
            self.buy_and_start_subscription()
            time.sleep(1)
        try:
            print("Reading contract values...")
            auth = self.get_auth_signature()
            (nom, denom) = self.contract_instance.functions.getAggPredval(block,auth).call({"from":owner})
            print(f" Got {nom} and {denom}")
            if denom==0:
                return None
            return nom/denom
        except Exception as e:
            print("Failed to call getAggPredval")
            print(e)
            return None


    
    def payout(self,slot):
        """ Claims the payout for a slot"""
        gasPrice = w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.payout(slot,owner).transact({"from":owner,"gasPrice":gasPrice})
            print(f"Submitted payout, txhash: {tx.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except Exception as e:
            print(e)
            return None

    def soonest_block_to_predict(self,block):
        return self.contract_instance.functions.soonestBlockToPredict(block).call()
    
    def submit_prediction(self,predicted_value,stake_amount,prediction_block):
        """ Sumbits a prediction"""
        stake_token = Token(self.contract_instance.functions.stakeToken().call())
        # TO DO - check allowence
        amount_wei = w3.to_wei(str(stake_amount),'ether')
        stake_token.approve(self.contract_address,amount_wei)
        gasPrice = w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.submitPredval(predicted_value,amount_wei,prediction_block).transact({"from":owner,"gasPrice":gasPrice})
            print(f"Submitted prediction, txhash: {tx.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except Exception as e:
            print(e)
            return None
    
    def get_trueValSubmitTimeoutBlock(self):
        return self.contract_instance.functions.trueValSubmitTimeoutBlock().call()
    
    def get_prediction(self,slot):
        return self.contract_instance.functions.getPrediction(slot).call({"from":owner})

    def submit_trueval(self,true_val,block,float_value,cancel_round):
        gasPrice = w3.eth.gas_price
        try:
            fl_value=w3.to_wei(str(float_value),'ether')
            tx = self.contract_instance.functions.submitTrueVal(block,true_val,fl_value,cancel_round).transact({"from":owner,"gasPrice":gasPrice})
            print(f"Submitted trueval, txhash: {tx.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except Exception as e:
            print(e)
            return None
    
    def redeem_unused_slot_revenue(self,block):
        gasPrice = w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.redeemUnusedSlotRevenue(block).transact({"from":owner,"gasPrice":gasPrice})
            print(f"redeem_unused_slot_revenue tx: {tx.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except Exception as e:
            print(e)
            return None

    def get_block(self,block):
        return w3.eth.get_block(block)
    

class FixedRate:
    def __init__(self, config: ContractConfig, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(address=config.w3.to_checksum_address(address), abi=get_contract_abi('FixedRateExchange'))
        self.config = config

    def get_dt_price(self, exchangeId):
        return self.contract_instance.functions.calcBaseInGivenOutDT(exchangeId,w3.to_wei('1','ether'),0).call()

    def buy_dt(self,exchange_id,baseTokenAmount):
        gasPrice = w3.eth.gas_price
        try:
            tx = self.contract_instance.functions.buyDT(exchange_id, w3.to_wei('1','ether'),baseTokenAmount, ZERO_ADDRESS, 0).transact({"from":owner,"gasPrice":gasPrice})
            print(f"Bought 1 DT tx: {tx.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx)
            return receipt
        except Exception as e:
            print(e)
            return None


def get_contract_abi(contract_name):
    """Returns the abi for a contract name."""
    path = get_contract_filename(contract_name)

    if not path.exists():
        raise TypeError("Contract name does not exist in artifacts.")

    with open(path) as f:
        data = json.load(f)
        return data['abi']

def get_contract_filename(contract_name):
    """Returns abi for a contract."""
    contract_basename = f"{contract_name}.json"

    # first, try to find locally
    address_filename = os.getenv("ADDRESS_FILE")
    path = None
    if address_filename:
        address_dir = os.path.dirname(address_filename)
        root_dir = os.path.join(address_dir, "..")
        os.chdir(root_dir)
        paths = glob.glob(f"**/{contract_basename}", recursive=True)
        if paths:
            assert len(paths) == 1, "had duplicates for {contract_basename}"
            path = paths[0]
            path = Path(path).expanduser().resolve()
            assert (
                path.exists()
            ), f"Found path = '{path}' via glob, yet path.exists() is False"
            return path
    # didn't find locally, so use use artifacts lib
    #path = os.path.join(os.path.dirname(artifacts.__file__), "", contract_basename)
    #path = Path(path).expanduser().resolve()
    #if not path.exists():
    #    raise TypeError(f"Contract '{contract_name}' not found in artifacts.")
    return path