from billing.views import calculate_vps


def get_configurations_context(configurations):
    configurations_context = {}
    configurations_total_price = 0

    for configuration in configurations:
        item = calculate_vps(configuration=configuration)
        configurations_total_price += item.get("total_cash", 0)

        for k, v in item.items():
            if not str(k).endswith("text"):
                configurations_context[k] = configurations_context.get(k, 0) + v

    return configurations_context, configurations_total_price
