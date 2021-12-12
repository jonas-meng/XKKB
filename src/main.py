import lib
import log_utility
from lib import BTKTron


def okex():
    node_config_path = "res/tron_node.json"
    nodes = lib.read_tron_nodes(node_config_path)

    account_config_path = "res/tron.json"
    test_accounts = lib.read_tron_account(account_config_path)
    test_account = test_accounts["okex_test"]

    log_path = "log/okex.log"
    btk_tron = BTKTron(node=nodes["nodes"]["NY"], log_path=log_path)

    address_path = "res/okex.txt"
    accounts = lib.read_addresses(address_path)

    # activate all account
    # btk_tron.activate_accounts(accounts, test_account["hexAddress"], test_account["privateKey"])

    TRX = 1000000
    total_amount = 1000*150*TRX
    amount = 150*TRX
    initial_account = test_account
    skip = 3
    btk_tron.transfer_fix_amount_to_accounts(accounts=accounts,
                                             total_amount=total_amount,
                                             amount=amount,
                                             initial_account=initial_account,
                                             skip=skip)


def test_remote():
    logger = log_utility.config_logger("test_remote", "log/test.log")
    logger.info("this is a remote message")


if __name__ == "__main__":
    test_remote()