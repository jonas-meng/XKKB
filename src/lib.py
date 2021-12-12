import concurrent.futures
import json
import time
import log_utility
import requests

from eth_abi import encode_abi
from tronpy import Tron


def read_json(path):
    with open(path) as reader:
        return json.load(reader)


def read_tron_nodes(node_config_path="res/tron_node.json"):
    return read_json(node_config_path)


def read_tron_account(account_config_path="res/tron.json"):
    return read_json(account_config_path)


def print_json(data):
    print(json.dumps(data, indent=2))


class WinNFTHorse:
    def __init__(self, log_path="log/activity.log"):
        self.client = Tron()
        self.log_path = log_path
        self.logger = log_utility.config_logger(self.__class__.__name__, log_path)
        nodes = read_tron_nodes()
        self.btk_tron = BTKTron(nodes["nodes"]["NY"])

    def get_start_exchange_signature(self, user_address, token_id):
        url = "https://api.winnfthorse.io/api/Coupon/Signature"
        payload = {
            "user_address": user_address,
            "contract_address": "TVwfiRLXWha8qJrHUW8EPq4UpnnZQvv3fB",
            "token_id": token_id
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(f"{response.text}")
        result = response.json()
        return {
            'nonce': result['nonce'],
            'token_id': result['token_id'],
            'signature': result['signature'],
            'genes': result['genes']
        }

    def get_start_exchange(self, account, token_id):
        contract_address = "TPRLVtaxRBpnCCT7hcvqbUbU5hVu1jWB3U"
        contract_hex_address = self.client.to_hex_address(contract_address)
        function_selector = "startExchange(uint256,uint256,uint256,bytes)"
        call_value = 0
        user_address = account["address"]
        user_hex_address = account["hexAddress"]
        user_private_key = account["privateKey"]
        signature = self.get_start_exchange_signature(user_address, token_id)
        parameter = self.btk_tron.abi_encode_parameters(["uint256", "uint256", "uint256", "bytes"],
                                                        [token_id, signature['genes'], signature['nonce'], bytes.fromhex(signature['signature'])])
        transaction = self.btk_tron.trigger_smart_contract(user_hex_address, contract_hex_address, function_selector, parameter, call_value)
        transaction = self.btk_tron.get_transaction_sign(transaction, user_private_key)
        self.btk_tron.broadcast_signed_transaction(transaction)

    def get_mystery_box_signature(self, contract_address, user_address):
        url = "https://api.winnfthorse.io/api/MysteryBox/Signature"
        payload = {
            "contract_address": contract_address,
            "user_address": user_address
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(f"{response.text}")
        result = response.json()
        return {
            'nonce': result['nonce'],
            # remove the 0x at the beginning
            'signature': result['signature'][2:]
        }

    def get_mystery_box_in_process(self, mystery_box_path="res/mystery_box.txt", max_workers=8):
        accounts = read_addresses(mystery_box_path)
        num_of_task = int(len(accounts)/max_workers)
        params = [
            {
                "id": int(i/num_of_task),
                "accounts": accounts[i:i + num_of_task]
            }
            for i in range(0, len(accounts), num_of_task)
        ]
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as process_executor:
            process_executor.map(self.get_mystery_box_in_thread, params)

    def get_mystery_box_in_thread(self, params, max_workers=16):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as thread_executor:
            thread_executor.map(self.get_mystery_box, params["accounts"])
        self.logger.info(f"{params['id']}-th Thread pool finished")

    def get_mystery_box(self, account):
        contract_address = "TPRLVtaxRBpnCCT7hcvqbUbU5hVu1jWB3U"
        contract_hex_address = self.client.to_hex_address(contract_address)
        function_selector = "mintNFTBySignature(uint256,bytes)"
        call_value = 500000000
        user_address = account["address"]
        user_hex_address = account["hexAddress"]
        user_private_key = account["privateKey"]
        signature = self.get_mystery_box_signature(contract_address, user_address)
        parameter = self.btk_tron.abi_encode_parameters(["uint256", "bytes"], [signature['nonce'], bytes.fromhex(signature['signature'])])
        transaction = self.btk_tron.trigger_smart_contract(user_hex_address, contract_hex_address, function_selector, parameter, call_value)
        transaction = self.btk_tron.get_transaction_sign(transaction, user_private_key)
        self.btk_tron.broadcast_signed_transaction(transaction)


class Endpoint:
    GENERATE_ADDRESS = "wallet/generateaddress"
    CREATE_ACCOUNT = "wallet/createaccount"
    GET_TRANSACTION_SIGN = "wallet/gettransactionsign"
    BROADCAST_TRANSACTION = "wallet/broadcasttransaction"
    CREATE_TRANSACTION = "wallet/createtransaction"
    GET_TRANSACTION_BY_ID = "wallet/gettransactionbyid"
    TRIGGER_SMART_CONTRACT = "wallet/triggersmartcontract"


class Network:
    MAIN_NETWORK = "https://api.trongrid.io"
    TEST_NETWORK = "https://api.shasta.trongrid.io"


def read_addresses(address_path):
    with open(address_path) as reader:
        return [json.loads(line) for line in reader.readlines()]


class BTKTron:

    def __init__(self, node=None, log_path="log/activity.log"):
        self.client = Tron()
        self.node = node
        self.log_path = log_path
        self.logger = log_utility.config_logger(self.__class__.__name__, log_path)

    def activate_accounts(self, accounts, owner_address, private_key):
        """
        Activate all accounts passed

        accounts: a list of accounts
        owner_address: owner address in hex mode
        private_key: owner address's private key
        """
        for index, account in enumerate(accounts):
            self.logger.info(f"Activating {index}-th address: {account['address']}, {account['hexAddress']}")
            self.activate_account(owner_address=owner_address, to_address=account['hexAddress'], private_key=private_key)

    def abi_encode_parameters(self, types, values):
        """
        types: a list of types
        values: a list of values
        """
        for i in range(len(types)):
            if types[i] == "address":
                # replace 41 with 0x
                address = values[i]
                values[i] = '0x' + address[2:]
        encoded_param = encode_abi(types, values)
        return encoded_param.hex()

    def trigger_smart_contract(self, owner_address, contract_address, function_selector, parameter, call_value, fee_limit=100000000):
        url = f"{self.get_node_url()}/{Endpoint.TRIGGER_SMART_CONTRACT}"
        self.logger.info(url)
        payload = {
            "owner_address": owner_address,
            "contract_address": contract_address,
            "function_selector": function_selector,
            "call_value": call_value,
            "parameter": parameter,
            "fee_limit": fee_limit
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        self.logger.info(response.text)
        return response.json()

    def transfer_fix_amount_to_accounts(self, accounts, total_amount, amount, initial_account=None, skip=0):
        """
        transfer a decreasing amount from account to account, each time the transferred amount decreased by {amount},
        such that in the end each account will have {amount} trx

        accounts: all accounts will have {amount} TRX
        total_amount: the initial amount / total amount token transferred
        amount: the amount left in each account
        initial_account: initial account used to transfer trx
        skip: in case some transfers have finished, we will skip them
        """
        total_amount = total_amount
        transfer_amount = total_amount
        current_owner = initial_account
        for idx, account in enumerate(accounts):
            if idx < skip:
                # set current account as the next owner account
                current_owner = account
                # remove the amount left in current account
                transfer_amount = transfer_amount - amount
                continue

            # set current account as the receiver account
            current_to = account
            self.logger.info(f"{idx}-th transfer {transfer_amount} trx from {current_owner['address']} to {current_to['address']}")
            self.transfer_account(owner_address=current_owner['hexAddress'],
                                  to_address=current_to['hexAddress'],
                                  private_key=current_owner['privateKey'],
                                  amount=amount)

            # after current account received trx
            current_owner = current_to
            # remove the amount left in current account
            transfer_amount = transfer_amount - amount
            # wait for 3 second for the confirmation of the transaction
            time.sleep(3)

    def get_transaction_info_by_id(self, transaction_id):
        url = f"{self.get_node_url()}/{Endpoint.GET_TRANSACTION_BY_ID}"
        self.logger.info(url)
        payload = {"value": transaction_id}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        self.logger.info(response.text)
        return response.json()

    def get_node_url(self, default_network=Network.TEST_NETWORK):
        """
        get node url or test network
        """
        if self.node:
            return f"http://{self.node['ip']}:8090"
        else:
            return default_network

    def activate_account(self, owner_address, to_address, private_key):
        """
        activate account by sending first activation transaction, cost 1.1 TRX
        """
        transaction = self.create_account_transaction(owner_address, to_address)
        transaction = self.get_transaction_sign(transaction, private_key)
        self.broadcast_signed_transaction(transaction)

    def transfer_account(self, owner_address, to_address, private_key, amount):
        """
        transfer {amount} TRX from owner address to to address
        """
        transaction = self.create_transaction(owner_address, to_address, amount)
        transaction = self.get_transaction_sign(transaction, private_key)
        self.broadcast_signed_transaction(transaction)

    def create_transaction(self, owner_address, to_address, amount):
        """
        create trx transfer transaction
        """
        url = f"{self.get_node_url()}/{Endpoint.CREATE_TRANSACTION}"
        self.logger.info(url)
        payload = {
            "to_address": to_address,
            "owner_address": owner_address,
            "amount": amount
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(f"{response.text}")
        return response.json()

    def broadcast_signed_transaction(self, transaction):
        url = f"{self.get_node_url()}/{Endpoint.BROADCAST_TRANSACTION}"
        self.logger.info(url)
        payload = transaction
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(response.text)
        return response.json()

    def create_account_transaction(self, owner_address, to_address):
        """
        create activate account transaction
        """
        url = f"{self.get_node_url()}/{Endpoint.CREATE_ACCOUNT}"
        self.logger.info(url)
        payload = {
            "owner_address": owner_address,
            "account_address": to_address
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(response.text)
        return response.json()

    def get_transaction_sign(self, transaction, private_key):
        """
        get transaction signed with private key
        """
        url = f"{self.get_node_url()}/{Endpoint.GET_TRANSACTION_SIGN}"
        self.logger.info(url)
        payload = {
            "transaction": transaction,
            "privateKey": private_key
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers)
        self.logger.info(response.text)
        return response.json()

    def generate_address_to(self, num, path, generate_address_call=None):
        """
        num: number of address need to be generated
        path: path to the file containing all generated address
        generate_address_call: method that generates a address
        """

        # if generate address call is not specified, by default offline address generator is used
        if not generate_address_call:
            generate_address_call = self.generate_address_offline
        addresses = [
            generate_address_call()
            for _ in range(0, num)
        ]
        with open(path, "a") as output:
            output.writelines('\n'.join([json.dumps(address) for address in addresses]))

    def generate_address_offline(self):
        """
        get Tron public/private key in offline
        """
        address = self.client.generate_address()
        address = {
            "privateKey": address['private_key'],
            "address": address['base58check_address'],
            "hexAddress": address['hex_address']
        }
        self.logger.info(json.dumps(address))
        return address

    def generate_address(self):
        """
        generate address from self hosted nodes (recommended) or from test network (keys are potentially leaked)
        """
        url = f"{self.get_node_url()}/{Endpoint.GENERATE_ADDRESS}"
        self.logger.info(url)
        headers = {"Accept": "application/json"}
        response = requests.request("GET", url, headers=headers)
        self.logger.info(response.text)
        return response.json()
