import logging

from io import BytesIO
from weasyprint import HTML
from django.http import HttpResponse
from django.template.loader import get_template

from billing.views import calculate_vps
from vpsService.enum_utils import VpsDevicePriceEnum

logger = logging.getLogger(__name__)


def render_to_pdf(template_src: str, context_dict=None):
    template = get_template(template_name=template_src)
    html = template.render(context_dict)

    pdf_bytes = generate_pdf(html)
    if pdf_bytes is not None:
        return HttpResponse(pdf_bytes, content_type='application/pdf')
    return None


def generate_pdf(html):
    try:
        result = BytesIO()
        HTML(string=html).write_pdf(result, timeout=120)  # Increase the timeout value as needed
        return result.getvalue()
    except Exception as e:
        # Handle any exceptions that may occur during PDF generation
        logger.info(f"PDF generation error: {e}")
        return None


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


class ConfigurationsCalculator:
    def __init__(self, configurations):
        self.configurations = configurations
        self.configurations_context = {}
        self.configurations_total_price = 0

    def calculate(self):
        for configuration in self.configurations:
            self.process_configuration(configuration)
        configurations_cost_prices = self.get_configurations_cost_prices()
        return self.configurations_context, self.configurations_total_price, configurations_cost_prices

    def process_configuration(self, configuration):
        item = calculate_vps(configuration=configuration)
        total_cash = item.get("total_cash", 0)
        self.configurations_total_price += total_cash

        for k, v in item.items():
            if k.endswith("text") or k.startswith("storage"):
                continue

            if k in ["ssd", "hdd"]:
                self.process_storage_configuration(v)
            else:
                self.process_price_configuration(k, v)

    def process_storage_configuration(self, storage_configuration):
        for k2, v2 in storage_configuration.items():
            self.configurations_context[k2] = self.configurations_context.get(k2, 0) + v2

    def process_price_configuration(self, key, value):
        self.configurations_context[key] = self.configurations_context.get(key, 0) + value

    def get_configurations_cost_prices(self):
        return {
            'cpu_price': VpsDevicePriceEnum.CPU,
            'ram_price': VpsDevicePriceEnum.RАМ,
            'hdd_price': VpsDevicePriceEnum.HDD,
            'ssd_price': VpsDevicePriceEnum.SSD,
            'internet_price': VpsDevicePriceEnum.INTERNET,
            'tasix_price': VpsDevicePriceEnum.TASIX,
            'imut_price': VpsDevicePriceEnum.IMUT,
            'ipv4_address_price': VpsDevicePriceEnum.IPV4_ADDRESS,
        }
