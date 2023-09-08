import logging
from werkzeug import urls
from odoo.http import request
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.addons.sp_payment_mips.controllers.main import SLPaystackController as sl_controller


_logger = logging.getLogger(__name__)


class SPLPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
 
        if self.provider_code != 'paystack':
            return res

        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(base_url, sl_controller._return_url)
        notify_url = urls.url_join(base_url, sl_controller._return_url)
        values = {
            'Authorization': 'Bearer ' + self.provider_id.paystack_secret_key,
            'Content-Type': 'application/json',
            'name': self.partner_name,
            'amount': self.amount,
            'description': 'Reference no :' + self.reference,
            'notify_url': notify_url,
            'cancel_return': return_url,
            'return_url': return_url,
            'item_reference': self.reference,
        }
        request.session['mips_reference'] = self.reference
        return values

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != 'paystack':
            return

        self.with_user(SUPERUSER_ID).write({'provider_reference': data.get('mipsReference')})
        self.with_user(SUPERUSER_ID)._set_done()
        return True

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        print("model paystack === ",tx)
        if provider_code != 'paystack':
            return tx

        reference = notification_data.get('mipsReference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'paystack')])
        if not tx:
            raise ValidationError(
                "Mips: " + _("No transaction found matching reference %s.", reference)
            )
        return tx


class SPLAcquirerPaystack(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('paystack', 'Paystack')], ondelete={'paystack': 'set default'})
    paystack_secret_key = fields.Char('Secret Key')

    @api.model
    def _paystack_get_api_url(self, environment):
        return {'paystack_form_url': 'https://api.paystack.co/page'}

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != 'paystack':
           return super()._get_default_payment_method_id(code)
        return self.env.ref('sp_payment_mips.paystack_payment_method').id
