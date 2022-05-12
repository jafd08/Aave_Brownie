from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from scripts.get_weth import get_weth
from web3 import Web3

# 0.03 amount eth for test
amount = Web3.toWei(0.05, "ether")
# 0.1668 ETH


def main():
    account = get_account()
    current_netw = network.show_active()
    erc20_addr = config["networks"][current_netw]["weth_token"]
    if current_netw in ["mainnet-fork"]:  # list of mainnets
        get_weth()
    lending_pool = get_lending_pool()
    print("lending_pool :", lending_pool)
    # approve sending the ERC20 tokens
    approve_erc20(amount, lending_pool.address, erc20_addr, account)
    # now we have everything approve, we will deposit
    print(" Depositing... ")

    tx = lending_pool.deposit(
        erc20_addr, amount, account.address, 0, {"from": account}
    )  # https://docs.aave.com/developers/v/2.0/the-core-protocol/lendingpool info about the deposit, parameters etc
    # referralCode is deprecated, we send 0 just to fill
    tx.wait(1)
    print(" Deposited !! ")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    # Lets borrow DAI
    print(" borrowing..! ")
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][current_netw]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (
        borrowable_eth * 0.95
    )  # we multiply by 0.95 as a buffer, to make sure our health factor is "better"
    #  borrowable eth -> borrable_dai * 95%
    print(" We are going to borrow ", amount_dai_to_borrow, "DAI")
    # we will borrow now
    dai_address = config["networks"][current_netw]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )

    borrow_tx.wait(1)
    print("We borrowed some DAI! ")
    get_borrowable_data(lending_pool, account)
    # repay_all(amount, lending_pool, account)
    print(
        " You just deposited, borrowed, and repayed with Aave, Brownie and Chainlink! "
    )


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print(" REPAYED!!  ")


def get_asset_price(price_feed_addr):
    # ABI
    # ADDRESS
    dai_eth_price_feed = interface.IAggregatorV3(price_feed_addr)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_eth_latest_price = Web3.fromWei(latest_price, "ether")
    print("The current DAI/ETH price is  :", converted_eth_latest_price)
    return float(converted_eth_latest_price)
    # 0.00543050000000000


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    print("available_borrow_eth :", available_borrow_eth)
    # passing to Eth since we get the Wei
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited")
    print(f"You have {total_debt_eth} total ETH borrowed")
    print(f"You can borrow {available_borrow_eth} worth of ETH")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(amount, spender, erc20_address, account):
    # We need
    # ABI
    # ADDRESS of token contract
    print(" Approving ERC20 token.... ")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)  # wait for 1 confirmation block to finish
    print(" APPROVED! ")

    return tx


def get_lending_pool():
    current_netw = network.show_active()

    lending_p_addrs_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][current_netw]["lending_pool_addresses_provider"]
    )

    lending_p_address = lending_p_addrs_provider.getLendingPool()
    # ABI
    # ADDRESS - Check!
    lending_pool = interface.ILendingPool(lending_p_address)
    return lending_pool
