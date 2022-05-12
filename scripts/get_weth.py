from scripts.helpful_scripts import get_account
from brownie import interface, config, network


def main():
    get_weth()


def get_weth():
    # Mints WETH by depositing ETH
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.05 * 10**18})
    print("Received 0.05 WETH ")
    return tx  # min 9h 00 27
