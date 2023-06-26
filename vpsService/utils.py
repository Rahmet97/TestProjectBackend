from collections import defaultdict

from billing.views import calculate_vps
from vpsService.enum_utils import VpsDevicePriceEnum


def get_configurations_context(configurations: list) -> tuple[dict, int, dict]:
    configurations_context = {}
    configurations_total_price = 0

    configurations_cost_prices = {
        'cpu_price': VpsDevicePriceEnum.CPU,
        'ram_price': VpsDevicePriceEnum.RАМ,
        'hdd_price': VpsDevicePriceEnum.HDD,
        'ssd_price': VpsDevicePriceEnum.SSD,
        'internet_price': VpsDevicePriceEnum.INTERNET,
        'tasix_price': VpsDevicePriceEnum.TASIX,
        'imut_price': VpsDevicePriceEnum.IMUT,
        'ipv4_address_price': VpsDevicePriceEnum.IPV4_ADDRESS,
    }

    for configuration in configurations:
        item = calculate_vps(configuration=configuration)
        configurations_total_price += item.get("total_cash", 0)

        for k, v in item.items():
            if not str(k).endswith("text") and not str(k).startswith("storage"):

                if k in ["ssd", "hdd"]:
                    for k2, v2 in v.items():
                        configurations_context[k2] = configurations_context.get(k2, 0) + v2
                else:
                    configurations_context[k] = configurations_context.get(k, 0) + v

    return configurations_context, configurations_total_price, configurations_cost_prices
