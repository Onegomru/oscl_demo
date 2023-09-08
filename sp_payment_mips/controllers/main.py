import json
import logging
import requests
from werkzeug import urls
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from urllib.parse import urlparse, parse_qs
from werkzeug.utils import redirect
import re

_logger = logging.getLogger(__name__)


class SLPaystackController(http.Controller):
    _notify_url = '/mips/request/'
    _return_url = '/mips/response'

    # def _paystack_validate_data_authenticity(self, **post):
    #     res = False
    #     if post.get('reference') and request.session.get('paystack_reference'):
    #         post['transactionReference'] = request.session['paystack_reference']
    #         del request.session['paystack_reference']
    #         tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
    #             'paystack', post
    #         )
    #         if tx_sudo:
    #             headers = {
    #                 'Authorization': 'Bearer ' + tx_sudo.sudo().provider_id.paystack_secret_key,
    #             }
    #             res = requests.get('https://api.paystack.co/transaction/verify/' + post.get('reference'), headers=headers)
    #             res.raise_for_status()
    #             resp = json.loads(res.content)
    #             post['status'] = resp['data'].get('status')
    #             post['error'] = resp['data'].get('log') and resp['data']['log'].get('errors')
    #             if resp['data'].get('status') == 'success':
    #                 _logger.info('Paystack: validated data')
    #                 tx_sudo._handle_notification_data('paystack', post)
    #                 return post
    #             error_message = "PayStack: " + _("Data were not acknowledged.")
    #             tx_sudo._set_error(error_message)
    #             raise ValidationError(error_message)
    #     raise ValidationError("PayStack:" + _("Can't find transaction reference."))

    @http.route('/payment/redirect/mips', type='http', auth='public', methods=['POST'], csrf=False, website=True)
    def sl_payment_redirect_paystack(self, **post):
        url = "https://api.mips.mu/api/load_payment_zone"
        custom_url = urls.url_join(request.httprequest.host_url,self._return_url)
        _logger.info(f"custom url return => {custom_url}")
        payload = {
            "authentify": {
                "id_merchant": "WSaadaXg6XoErkU8B1dp1PcUc44FDcIv",
                "id_entity": "3kiI0HWdviIfwEJml8jfALrG7wEjBKUO",
                "id_operator": "LcF4izWu3eK4ieIeKSIvsao8L5aKVRRX",
                "operator_password": "oFUNk7X4Kf1Onk5F1Rz2rqK4fa9nwDC5"
            },
            "order": {
                "id_order": post['item_reference'],
                "currency": "MUR",
                "amount": post['amount']
            },
            "iframe_behavior": {
                "height": 400,
                "width": 350,
                "custom_redirection_url": custom_url,
                "language": "EN"
            },
            "request_mode": "simple",
            "touchpoint": "native_app",
        }
        headers = {
            "user-agent": "",
            "Content-Type": "application/json",
            "Accept": "application/json, text/html, application/xml, multipart/form-data, application/EDIFACT, text/plain",
            "Authorization": "Basic b2Rvb182MzQxMjpKaEg5NHR3aEdVQVhZVktYME1TbQ=="
        }
            
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        url = data['answer']['payment_zone_data']
        _logger.info(f"url ============== {url}")
        start_index = url.find('?c=') + len('?c=')
        end_index = url.find('==&', start_index)
        extracted_value = url[start_index:end_index]   
        _logger.info(f"##### Extracted value: {extracted_value}")
        request.session['crypted_key'] = extracted_value
        session = http.request.session
        for key, value in session.items():
            _logger.info(f"Key: {key}, Value: {value}")
        return redirect(url)

    # @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False)
    # def paystack_request(self, **post):
    #     try:
    #         self._paystack_validate_data_authenticity(**post)
    #     except ValidationError as e:
    #         _logger.debug(f"Error while validate in request {e}")
    #     return ''

    # @http.route(_return_url, type='http', auth="public", methods=['POST', 'GET'], csrf=False)
    # def paystack_response(self, error=False, **post):
    #     try:
    #         self._paystack_validate_data_authenticity(**post)
    #     except ValidationError as e:
    #         _logger.debug(f'Error while validate in response {e}')
    #         if error:
    #             return request.render("sp_payment_paystack.paystack_cancelled_payment",
    #                 {'message': error})
    #     return request.redirect('/payment/status')

    
        for key, value in session.items():
            _logger.info(f"Key: {key}, Value: {value}")
        return redirect(url)

    @http.route(_return_url, type='http', auth="public", methods=['POST', 'GET'], csrf=False)
    def paystack_response(self, error=False, **post):
        post['mipsReference'] = request.session['mips_reference']
        # _logger.info(f"#### validate data post output ===> {post}")
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'paystack', post
        )
        _logger.info(f"#### tx_sudo #### {tx_sudo}")
        _logger.info(f"#### return post output #### {post}")
        tx_sudo._handle_notification_data('paystack', post)
        _logger.info(f"#### _handle_notification_data #### {tx_sudo._handle_notification_data}")
        return request.redirect('/payment/status')

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        sale_order_id = request.session.get('sale_last_order_id')
        print("# sale_order_id",sale_order_id)
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            values = self._prepare_shop_payment_confirmation_values(order)
            return request.render("sp_payment_mips.success_payment", values)
        else:
            return request.redirect('/shop')
    
    
    def _prepare_shop_payment_confirmation_values(self, order):
        return {
            'order': order,
        }
