import shioaji as sj
import shioaji.constant as sjc
from bot.utils import get_shioaji


api = get_shioaji(simulation=False)
contract = api.Contracts.Stocks.get("2330")
print(contract)

if contract is None:
    print("Contract not found")
    exit()

order = sj.Order(
    price=10,
    quantity=1,
    action=sjc.Action.Buy,
    price_type=sjc.StockPriceType.LMT,
    order_type=sjc.OrderType.ROD,
    account=api.stock_account,
)
print(order)
trade = api.place_order(contract, order)


