import time
import logging
import requests
import json
from tronpy import Tron
from datetime import datetime
from eth_abi import encode_abi

# THIS SCRIPT GENERATES AND ACTIVATES TRON ACCOUNT, 1.1 TRX IS REQUIRED FOR EACH ACCOUNT ACTIVATION
# PLEASE RESERVE ENOUGH TRONX IN CREATOR ADDRESS: TAYWpojf6eccQgLaaDqfv2FB7Z8GayR7Ay
# HEX ADDRESS: 41064c9ad5dfa714d2b429a995140ac882f9cda65d

TEST_ADDRESS = "TAYWpojf6eccQgLaaDqfv2FB7Z8GayR7Ay"
TEST_HEX_ADDRESS = "41064c9ad5dfa714d2b429a995140ac882f9cda65d"
TEST_PRIVATE_KEY = "6e06993158a19f55076a9a584e79245e9c504708574d981154a5289629cf04e5"

HOLDER_WIN_MYSTERY_BOX_ADDRESS_PATH = "res/holder_address.txt"
HOLDER_LOG_PATH = "log/holder.log"
HOLDER_LOTTERY_PATH = "res/holder_lottery.txt"

OFFLINE_HOLDER_WIN_MYSTERY_BOX_ADDRESS_PATH = "res/offline_holder_address.txt"
OFFLINE_HOLDER_LOG_PATH = "log/offline_holder.log"
OFFLINE_HOLDER_LOTTERY_PATH = "res/offline_holder_lottery.txt"

ADDRESS_PATH = "res/address.txt"


WALLET_HEX_ADDRESS = "41064c9ad5dfa714d2b429a995140ac882f9cda65d"
WALLET_PRIVATE_KEY = "6e06993158a19f55076a9a584e79245e9c504708574d981154a5289629cf04e5"

WIN_NFT_HORSE_CONTRACT = "TRroN1acf1KUTUoBUKMLzfbUoXESBL5dJa"
WIN_NFT_HORSE_CONTRACT_HEX_ADDRESS = "41ae4bc8bc6a813e68e9262d5a1aa6ddfb0ee20d26"

WIN_NFT_CONTRACT = "THmGFax8tqkWcnmGcRb8ipyL9bzdAA8Svv"
WIN_NFT_CONTRACT_HEX_ADDRESS = "41557eba63a93c658684c5853c978a8ed091ffbf80"

TRON_API_KEY = "efdfb536-ac64-4391-a9af-7c3e2eb3ed33"

SUN = 1
TRX = 1_000_000 * SUN

logger = logging.getLogger(__name__)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def config_logger(log_path):
    logger.setLevel(logging.DEBUG)
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_path)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def generate_address():
    url = "https://api.shasta.trongrid.io/wallet/generateaddress"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    print(response.text)
    return response.text


def generate_address_offline():
    client = Tron()
    address = client.generate_address()
    print(address)
    return json.dumps({
        "privateKey": address['private_key'],
        "address": address['base58check_address'],
        "hexAddress": address['hex_address']
    }) + '\n'


def generate_address_of(num, path, generate_address_call=generate_address_offline):
    """
    num: number of address
    path: file path
    """
    addresses = [
        generate_address_call()
        for _ in range(0, num)
    ]
    with open(path, "a") as output:
        output.writelines(addresses)


def activate_account(owner_address, to_address, private_key):
    transaction = create_account_transaction(owner_address, to_address)
    transaction = get_transaction_sign(transaction, private_key)
    broadcast_signed_transaction(transaction)


def transfer_account(owner_address, to_address, private_key, amount):
    transaction = create_trx_transaction(owner_address, to_address, amount)
    transaction = get_transaction_sign(transaction, private_key)
    return broadcast_signed_transaction(transaction)


def create_account_transaction(owner_address, to_address):
    url = "https://api.trongrid.io/wallet/createaccount"

    payload = {
        "owner_address": owner_address,
        "account_address": to_address
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    print("creating account transaction")

    response = requests.request("POST", url, json=payload, headers=headers)

    logger.info(f"{response.text}")
    return json.loads(response.text)


def create_trx_transaction(owner_address, to_address, amount):
    url = "https://api.trongrid.io/wallet/createtransaction"

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

    logger.info(f"{response.text}")
    return json.loads(response.text)


def get_transaction_sign(transaction, private_key):
    url = "https://api.shasta.trongrid.io/wallet/gettransactionsign"

    payload = {
        "transaction": transaction,
        "privateKey": private_key
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    logger.info(f"{response.text}")
    return json.loads(response.text)


def broadcast_signed_transaction(transaction):
    url = "https://api.trongrid.io/wallet/broadcasttransaction"

    payload = transaction
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(response.text)
    return json.loads(response.text)


def read_addresses(address_path):
    with open(address_path) as reader:
        return [
            json.loads(line)
            for line in reader.readlines()
        ]


def activate_accounts_in(path, own_address, private_key):
    address_list = read_addresses(address_path=path)
    for index, address in enumerate(address_list):
        print(f"Activating {index}-th address: {address['address']}, {address['hexAddress']}")
        activate_account(owner_address=own_address, to_address=address['hexAddress'], private_key=private_key)


def get_transaction(address, limit=1):
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions?limit={limit}"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    transactions = response.json()
    print(json.dumps(transactions, indent=2))
    return transactions


def get_transaction_trc20(address, limit=1, only_to=None, only_confirmed=True):
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
    payload = {
        "limit": limit
    }
    if only_to:
        payload["only_to"] = only_to
    if only_confirmed:
        payload["only_confirmed"] = only_confirmed
    headers = {
        "Accept": "application/json"
    }
    response = requests.request("GET", url, params=payload, headers=headers)
    return json.loads(response.text)


def is_win_nft_received(transactions):
    try:
        if transactions['data'][0]['token_info']['symbol'] == 'MBOX1000':
            return 0
    except:
        pass
    return 1


def check_win_nft_unreceived():
    address_list = read_addresses(address_path=ADDRESS_PATH)
    num_of_unreceived = sum(
        [is_win_nft_received(get_transaction_trc20(address["address"])) for address in address_list])
    print(f"total unreceived count: {num_of_unreceived}")


def get_trc20_token_holder_balances():
    url = "https://api.trongrid.io/v1/contracts/TVwfiRLXWha8qJrHUW8EPq4UpnnZQvv3fB/tokens?limit=200"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    print(json.dumps(response.json(), indent=2))


def transfer_amount_in_sequence(address_path, total_amount, topup):
    addresses = read_addresses(address_path=address_path)
    current_owner_idx = 0
    current_to_idx = 1
    total_amount = total_amount
    amount = total_amount - topup
    while True:
        current_owner = addresses[current_owner_idx]
        current_to = addresses[current_to_idx]
        print(f"{current_to_idx}-th transfer {amount} trx from {current_owner['address']} to {current_to['address']}")
        transfer_account(owner_address=current_owner['hexAddress'],
                         to_address=current_to['hexAddress'],
                         private_key=current_owner['privateKey'],
                         amount=amount*TRX)
        current_owner_idx += 1
        current_to_idx += 1
        amount -= topup
        if current_to_idx >= len(addresses):
            break
        time.sleep(3)


def get_win_nft_horse_lowest_price():
    url = "https://api.winnfthorse.io/api/GetAxieBriefList"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://market.winnfthorse.io",
        "Referer": "https://market.winnfthorse.io",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }
    payload = {
        "auctionType": "All",
        "limit": 6,
        "page": 1,
        "sort": "Lowest Price"
    }
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        pass
    return None




def get_transaction_info_by_account(transaction_id):
    url = "https://api.trongrid.io/wallet/gettransactionbyid"

    payload = {"value": transaction_id}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_transaction_info_by_contract(contract_address):
    url = f"https://api.trongrid.io/v1/contracts/{contract_address}/transactions"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_create_auction_transaction(limit):
    """
    WIN_NFT_HORSE only have create auction as IN transaction
    """
    transactions = get_transaction_trc20(WIN_NFT_HORSE_CONTRACT, limit=limit, only_to=True, only_confirmed=None)
    return transactions["data"]


def get_events_by_transaction_id(transaction_id):
    url = f"https://api.trongrid.io/v1/transactions/{transaction_id}/events"
    headers = {
        "Accept": "application/json"
    }
    response = requests.request("GET", url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_current_lowest_price():
    res = get_win_nft_horse_lowest_price()
    if not res:
        return None, None
    horses = res['data']
    for horse in horses:
        if horse['a_startingPrice'] == horse['a_currentPrice']:
            return horse['a_currentPrice'], horse['a_id']
    return None, None


def track_win_nft_horse_lowest_price():
    interval = 10
    last_lowest_price = None
    while True:
        time.sleep(interval)
        current_lowest_price, horse_id = get_current_lowest_price()
        if not current_lowest_price:
            logger.info("FAILED TO REQUEST DATA")
            continue
        current_lowest_price = float(current_lowest_price)
        if not last_lowest_price:
            last_lowest_price = current_lowest_price
        else:
            logger.info(f"last lowest price {last_lowest_price/TRX}, current lowest price {current_lowest_price/TRX}")
            if last_lowest_price / current_lowest_price > 1:
                logger.info(f"Horse ID: {horse_id}, Price: {current_lowest_price}, NFTAddress: THmGFax8tqkWcnmGcRb8ipyL9bzdAA8Svv")
            else:
                last_lowest_price = current_lowest_price


def trigger_smart_contract(owner_address, contract_address, function_selector, parameter, call_value, fee_limit):
    url = "https://api.trongrid.io/wallet/triggersmartcontract"
    print(parameter)
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
    logger.info(f"{response.text}")
    return response.json()


def encode_params(horse_id):
    # 41557eba63a93c658684c5853c978a8ed091ffbf80 -> 0x557eba63a93c658684c5853c978a8ed091ffbf80
    encoded_param = encode_abi(['address', 'uint256'], ["0x557eba63a93c658684c5853c978a8ed091ffbf80", horse_id])
    return encoded_param.hex()


def get_bid_transaction(owner_address, horse_id, bid_price, fee=100):
    owner_address = owner_address
    contract_address = WIN_NFT_HORSE_CONTRACT_HEX_ADDRESS
    function_selector = "bid(address,uint256)"
    parameters = encode_params(horse_id)
    call_value = bid_price
    fee_limit = fee*TRX
    transaction = trigger_smart_contract(owner_address, contract_address, function_selector, parameters, call_value, fee_limit)
    return transaction


def fire_bid_transaction(horse_id, bid_price):
    transaction = get_bid_transaction(WALLET_HEX_ADDRESS, horse_id, bid_price)
    print(transaction)
    transaction = get_transaction_sign(transaction["transaction"], WALLET_PRIVATE_KEY)
    print(transaction)
    return broadcast_signed_transaction(transaction)


def track_win_nft_horse_lowest_price_with_on_chain_transaction():
    limit = 1
    last_reviewed_transaction_id = None
    lowest_market_price = 10000*TRX
    while True:
        try:
            acution_transactions = get_create_auction_transaction(limit)
            if not last_reviewed_transaction_id:
                last_reviewed_transaction_id = acution_transactions[0]["transaction_id"]
            transaction = acution_transactions[0]
            if last_reviewed_transaction_id == transaction["transaction_id"]:
                continue
            logger.info(f"new transaction id {transaction['transaction_id']} at {datetime.fromtimestamp(int(transaction['block_timestamp'])/1000)}")
            horse_id = transaction["value"]
            seller = transaction["from"]
            transaction_id = transaction["transaction_id"]
            events = get_events_by_transaction_id(transaction_id)
            first_event = events["data"][0]
            if first_event["event_name"] != "AuctionCreated":
                continue
            # fix price order
            if first_event["result"]["_startingPrice"] == first_event["result"]["_endingPrice"]:
                horse_price = float(first_event["result"]["_startingPrice"])
                logger.info(f"lowest market price is {lowest_market_price/TRX}, horse price of {transaction_id} is {horse_price/TRX}")
                if int(lowest_market_price / horse_price) >= 2:
                    transaction = fire_bid_transaction(int(horse_id), int(horse_price))
                    logger.info(f"{bcolors.WARNING}PINGO! Seller: {seller}, Horse ID: {horse_id}, Horse Price: {horse_price/TRX}, NFTAddress: THmGFax8tqkWcnmGcRb8ipyL9bzdAA8Svv {bcolors.ENDC}")
                    if transaction["result"]:
                        logger.info(f"{bcolors.WARNING}PINGO! Bid transaction ID: {transaction['txid']} {bcolors.ENDC}")
            last_reviewed_transaction_id = acution_transactions[0]["transaction_id"]
        except Exception as error:
            logger.debug(f"Unexpected error occurred! {error}")
            pass


def get_market_lowest_price():
    interval = 3
    while True:
        current_lowest_price, horse_id = get_current_lowest_price()
        if not current_lowest_price:
            logger.info("FAILED TO REQUEST DATA")
            time.sleep(interval)
            continue
        return float(current_lowest_price)


def get_account_info_by_address(address):
    url = f"https://api.trongrid.io/v1/accounts/{address}"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def register_address_on_for_mystery_box(address):
    """
    error: {"err_code":500,"err_msg":"Your TRX is less than 150,000, please go get TRXs!","data":[]}
    success: {"err_code":0,"err_msg":"","data":{"list":[10405]}}
    """
    url = "https://api.winnfthorse.io/api/Activity/BalanceAirdrop"
    payload = {
        "address": address,
        "currency": "TRX"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.winnfthorse.io",
        "Referer": "https://www.winnfthorse.io",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def holder_lottery_registration():
    path = OFFLINE_HOLDER_WIN_MYSTERY_BOX_ADDRESS_PATH
    lottery_path = OFFLINE_HOLDER_LOTTERY_PATH
    current_address =TEST_ADDRESS
    current_owner_address = TEST_HEX_ADDRESS
    current_private_key = TEST_PRIVATE_KEY
    amount = 150000 * TRX

    address_list = read_addresses(address_path=path)
    lottery_list = []
    skip = 0
    current_count = 0
    transaction_waiting_interval = 5
    for address in address_list:
        if current_count < skip:
            current_address = address['address']
            current_owner_address = address['hexAddress']
            current_private_key = address['privateKey']
            logger.info(f"set current owner address {address['hexAddress']}")
            current_count += 1
            logger.info(f"current count is {current_count}")
            continue
        current_to_address = address['hexAddress']
        logger.info(f"Transfering {amount/TRX} from {current_address}({current_owner_address}) to {address['address']}({current_to_address})")
        transfer_account(
            owner_address=current_owner_address,
            to_address=current_to_address,
            private_key=current_private_key,
            amount=amount
        )
        time.sleep(transaction_waiting_interval)
        logger.info(f"Registering address: {address['address']}, {address['hexAddress']}")
        resp = register_address_on_for_mystery_box(address['address'])
        logger.info(json.dumps(resp))
        if resp["err_code"] == 0:
            logger.info(f"Appending tuple ({address['address']}, {resp['data']['list'][0]})")
            lottery_number = str(resp['data']['list'][0])
            lottery_address = str(address['address'])
            lottery_list.append(f"{lottery_address}, {lottery_number}\n")
        else:
            logger.error(f"Failed registration on address: {address['address']}, {address['hexAddress']}")
            break
        current_owner_address = address['hexAddress']
        current_private_key = address['privateKey']
        logger.info(f"set current owner address {address['hexAddress']}")
        current_count += 1
        logger.info(f"current count is {current_count}")
    with open(lottery_path, "a") as output:
        output.writelines(lottery_list)


if __name__ == "__main__":
    # transaction = trigger_smart_contract(TEST_HEX_ADDRESS, "41938ab55d0f1deb96ccc15073b889625e4a3df4af", "mintNFTBySignature(uint256,bytes)",
    #                        call_value=0,
        #                    parameter="000000000000000000000000000000000000000000000000000000000001c51100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041c26e70ef41f375f4582a0f8efe1bc03df8d78b75f35bdd135ba4e48de5ee983f351523c6489d4941a155f0969a36caee341b0de676c0ab30cabfa7622d5192a01c00000000000000000000000000000000000000000000000000000000000000",
    #                        fee_limit=100000000)
    # print(transaction)
    # transaction = get_transaction_sign(transaction["transaction"], WALLET_PRIVATE_KEY)
    # print(transaction)
    # broadcast_signed_transaction(transaction)
    # from eth_abi import encode_abi
    # a = "000000000000000000000000000000000000000000000000000000000001c51100000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000041c26e70ef41f375f4582a0f8efe1bc03df8d78b75f35bdd135ba4e48de5ee983f351523c6489d4941a155f0969a36caee341b0de676c0ab30cabfa7622d5192a01c00000000000000000000000000000000000000000000000000000000000000"
    # encoded_param = encode_abi(['uint256', 'bytes'], [115985, bytes.fromhex('c26e70ef41f375f4582a0f8efe1bc03df8d78b75f35bdd135ba4e48de5ee983f351523c6489d4941a155f0969a36caee341b0de676c0ab30cabfa7622d5192a01c')])
    # b = encoded_param.hex()
    
    # print(get_transaction_info_by_account("3bdc4e1b7d16e963a63528ff5b7a930043fa1386de615128a4bcd2473149138a"))

    transaction = get_transaction_info_by_account("2aa7f16719e28adb6a03922a201138cd631b2d611113b23e33a04cd956ee020b")
    print(json.dumps(transaction, indent=2))
    pass
