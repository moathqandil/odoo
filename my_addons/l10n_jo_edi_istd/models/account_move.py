# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import requests
import json
import uuid
from base64 import b64encode
import pprint
import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


def round_amount(amount, digits=3):
    return f'%.{digits}f' % round(amount, digits)

def round_quantity(qty, digits=3):
    return f'%.{digits}f' % round(qty, digits)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_jo_tax = fields.Monetary(string='Tax Amount', compute='_compute_l10n_jo_tax')
    l10n_jo_discount = fields.Monetary(string='Discount Amount', compute='_compute_l10n_jo_discount')

    @api.depends('price_subtotal', 'price_total')
    def _compute_l10n_jo_tax(self):
        for line in self:
            line.l10n_jo_tax = line.price_total - line.price_subtotal

    @api.depends('quantity', 'price_unit', 'price_subtotal')
    def _compute_l10n_jo_discount(self):
        for line in self:
            line.l10n_jo_discount = (line.quantity * line.price_unit) - line.price_subtotal


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_jo_amount_discount = fields.Monetary(string='Total Discount', compute='_compute_amount_discount')
    l10n_jo_amount_b4_discount = fields.Monetary(string='Amount Before Discount', compute='_compute_amount_discount')
    l10n_jo_uuid = fields.Char(string='Invoice UUID', copy=False)
    istd_invoice_sent = fields.Boolean(string='Invoice Sent', copy=False)
    istd_date_sent = fields.Datetime(string='Invoice Sending Time', copy=False)
    istd_einvoice = fields.Text(string='ISTD E-Invoice', copy=False)
    istd_qrcode = fields.Text(string='QR Code', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Generating UUID for each record being created
        """
        for vals in vals_list:
            vals['l10n_jo_uuid'] = uuid.uuid4().hex
        return super(AccountMove, self).create(vals_list)

    @api.depends('invoice_line_ids.l10n_jo_discount', 'amount_untaxed')
    def _compute_amount_discount(self):
        for move in self:
            move.l10n_jo_amount_discount = sum(move.invoice_line_ids.mapped('l10n_jo_discount'))
            move.l10n_jo_amount_b4_discount = move.amount_untaxed + move.l10n_jo_amount_discount

    def _post(self, soft=True):
        """
        Send invoices for if option (Send At Confirm) activated (with respect to company)
        :return:
        """
        result = super(AccountMove, self)._post(soft=soft)
        self.filtered(lambda m: m.company_id.l10n_jo_send_invoices_at_confirm).send_invoices_istd()
        return result

    @api.model
    def send_daily_invoices_istd(self):
        """
        This function will be called from a cron job to send daily invoices (depending on creation date)
        :return:
        """
        yesterday = (fields.Date.today() + relativedelta(days=-1)).strftime('%Y-%m-%d')
        datetime_from = datetime.strptime(yesterday, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        datetime_to = datetime.strptime(yesterday, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        domain = [('create_date', '>=', datetime_from), ('create_date', '<=', datetime_to)]
        invoices = self.search(domain)
        invoices.send_invoices_istd()

    def send_invoices_istd(self):
        invoices = self.filtered(lambda m: m.country_code == 'JO'
                                           and m.state == 'posted'
                                           and not m.istd_invoice_sent
                                           and m.move_type in ['out_invoice', 'out_refund'])
        for invoice in invoices:
            invoice._send_invoice_istd()

    def _send_invoice_istd(self):
        invoice_xml = self._prepare_invoice_xml()
        encoded_invoice = b64encode((invoice_xml).encode()).decode('utf-8')
        # print(encoded_invoice)
        url = "https://backend.jofotara.gov.jo/core/invoices/"
        headers = {
            'Content-Type': 'application/json',
            'Client-id': f'{self.company_id.l10n_jo_client_id}',
            'Secret-Key': f'{self.company_id.l10n_jo_client_secret}',
        }
        payload = json.dumps({
            "invoice": f"{encoded_invoice}"
        })
        response = requests.request(method='POST', url=url, headers=headers, data=payload, verify=False)
        # print(response.text)
        if response.status_code == 200:
            response = response.json()
            _logger.info(f"ISTD request success:\n{pprint.pformat(response)}")
            if response['EINV_RESULTS']['status'] == 'PASS':
                self.istd_qrcode = response.get('EINV_QR', False)
                self.l10n_jo_uuid = response.get('EINV_INV_UUID', False)
                self.istd_einvoice = response.get('EINV_SINGED_INVOICE', False)
                self.istd_invoice_sent = True
                self.istd_date_sent = fields.Datetime.now()

            if response['EINV_STATUS'] == 'SUBMITTED':
                self.message_post(
                    body="Invoice hase been sent to ISTD successfully",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
        else:
            try:
                _logger.info(f"ISTD request faild with status code: {response.status_code}")
                response = response.json()
                _logger.info(f"ISTD request success:\n{pprint.pformat(response)}")
            except:
                _logger.info(f"ISTD request faild with status code: {response.status_code}")

    def _prepare_invoice_xml(self):
        self.ensure_one()
        # invoice_types = {'cash': '012', 'credit': '022'}  # todo: will add invoice type in account.move
        # customer_identity = {'nationalId': 'NIN', 'DocumentId': 'PN', 'taxId': 'TN'}  # todo: will add this in res.partner
        invoice_type = '388' if self.move_type == 'out_invoice' else '381'
        notes = html2plaintext(self.narration or "")
        xml_string = f"""<Invoice	xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"	xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"	xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"	xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
	            <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
                <cbc:ID>{self.name.replace('/', '_')}</cbc:ID>
                <cbc:UUID>{self.l10n_jo_uuid or uuid.uuid4().hex}</cbc:UUID>
                <cbc:IssueDate>{self.invoice_date.strftime('%Y-%m-%d')}</cbc:IssueDate>
                <cbc:InvoiceTypeCode name="{'012'}">{invoice_type}</cbc:InvoiceTypeCode>
                <cbc:Note>{notes}</cbc:Note>
                <cbc:DocumentCurrencyCode>JOD</cbc:DocumentCurrencyCode>
                <cbc:TaxCurrencyCode>JOD</cbc:TaxCurrencyCode>
                {self._get_origin_invoice_details()}
                <cac:AdditionalDocumentReference>
                    <cbc:ID>ICV</cbc:ID>
                    <cbc:UUID>{'1'}</cbc:UUID>
                </cac:AdditionalDocumentReference>
                {self._get_supplier_party()}
                {self._get_customer_party()}
                <cac:SellerSupplierParty>
                    <cac:Party>
                        <cac:PartyIdentification>
                            <cbc:ID>{self.company_id.l10n_jo_activity_number or ''}</cbc:ID>
                        </cac:PartyIdentification>
                    </cac:Party>
                </cac:SellerSupplierParty>
                {self._get_payment_means()}
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReason>discount</cbc:AllowanceChargeReason>
                    <cbc:Amount currencyID="JO">{round_amount(self.l10n_jo_amount_discount)}</cbc:Amount>
                </cac:AllowanceCharge>
                <cac:TaxTotal>
                    <cbc:TaxAmount currencyID="JO">{round_amount(self.amount_tax)}</cbc:TaxAmount>
                </cac:TaxTotal>
                <cac:LegalMonetaryTotal>
                    <cbc:TaxExclusiveAmount currencyID="JO">{round_amount(self.l10n_jo_amount_b4_discount)}</cbc:TaxExclusiveAmount>
                    <cbc:TaxInclusiveAmount currencyID="JO">{round_amount(self.amount_total)}</cbc:TaxInclusiveAmount>
                    <cbc:AllowanceTotalAmount currencyID="JO">{round_amount(self.l10n_jo_amount_discount)}</cbc:AllowanceTotalAmount>
                    <cbc:PayableAmount currencyID="JO">{round_amount(self.amount_total)}</cbc:PayableAmount>
                </cac:LegalMonetaryTotal>
                {self._prepare_invoice_lines_xml()}
            </Invoice>
            """
        return xml_string

    def _prepare_invoice_lines_xml(self):
        self.ensure_one()
        lines_as_xml = ""
        counter = 1
        for line in self.invoice_line_ids:
            lines_as_xml += f"""<cac:InvoiceLine>
                    <cbc:ID>{counter}</cbc:ID>
                    <cbc:InvoicedQuantity unitCode="PCE">{round_quantity(line.quantity)}</cbc:InvoicedQuantity>
                    <cbc:LineExtensionAmount currencyID="JO">{round_amount(line.price_subtotal)}</cbc:LineExtensionAmount>
                    <cac:TaxTotal>
                        <cbc:TaxAmount currencyID="JO">{round_amount(line.l10n_jo_tax)}</cbc:TaxAmount>
                        <cbc:RoundingAmount currencyID="JO">{round_amount(line.price_total)}</cbc:RoundingAmount>
                        <cac:TaxSubtotal>
                            <cbc:TaxAmount currencyID="JO">{round_amount(line.l10n_jo_tax)}</cbc:TaxAmount>
                            <cac:TaxCategory>
                                <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5305">S</cbc:ID>
                                <cbc:Percent>{line.tax_ids[:1].amount if line.tax_ids else '0.00'}</cbc:Percent>
                                <cac:TaxScheme>
                                    <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5153">VAT</cbc:ID>
                                </cac:TaxScheme>
                            </cac:TaxCategory>
                        </cac:TaxSubtotal>
                    </cac:TaxTotal>
                    <cac:Item>
                        <cbc:Name>{line.name or line.product_id.name}</cbc:Name>
                    </cac:Item>
                    <cac:Price>
                        <cbc:PriceAmount currencyID="JO">{round_amount(line.price_unit)}</cbc:PriceAmount>
                        <cac:AllowanceCharge>
                            <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                            <cbc:AllowanceChargeReason>DISCOUNT</cbc:AllowanceChargeReason>
                            <cbc:Amount currencyID="JO">{round_amount(line.l10n_jo_discount)}</cbc:Amount>
                        </cac:AllowanceCharge>
                    </cac:Price>
                </cac:InvoiceLine>"""
            counter += 1
        return lines_as_xml

    def _get_origin_invoice_details(self):
        '''
        This part related to credit note
        :return:
        '''
        self.ensure_one()
        if self.move_type != 'out_refund':
            return ''
        details_as_xml = f"""
        <cac:BillingReference>
          <cac:InvoiceDocumentReference>
            <cbc:ID>{self.reversed_entry_id.name.replace('/', '_') or ''}</cbc:ID>
            <cbc:UUID>{self.reversed_entry_id.l10n_jo_uuid or ''}</cbc:UUID>
            <cbc:DocumentDescription>{self.amount_total}</cbc:DocumentDescription>
          </cac:InvoiceDocumentReference>
        </cac:BillingReference>
        """
        return details_as_xml

    def _get_payment_means(self):
        '''
        This part related to credit note
        :return:
        '''
        self.ensure_one()
        if self.move_type != 'out_refund':
            return ''
        details_as_xml = f"""
        <cac:PaymentMeans>
            <cbc:PaymentMeansCode listID="UN/ECE 4461">10</cbc:PaymentMeansCode>
            <cbc:InstructionNote>In cash</cbc:InstructionNote>
        </cac:PaymentMeans>
        """
        return details_as_xml

    def _get_supplier_party(self):
        self.ensure_one()
        # if self.move_type == 'out_invoice':
        vat_no = self.company_id.vat or ''
        partner_name = self.company_id.name
        # else:
        #     vat_no = self.partner_id.vat or ''
        #     partner_name = self.partner_id.display_name
        details_as_xml = f"""
        <cac:AccountingSupplierParty>
            <cac:Party>
                <cac:PostalAddress>
                    <cac:Country>
                        <cbc:IdentificationCode>JO</cbc:IdentificationCode>
                    </cac:Country>
                </cac:PostalAddress>
                <cac:PartyTaxScheme>
                    <cbc:CompanyID>{vat_no}</cbc:CompanyID>
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:PartyTaxScheme>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>{partner_name}</cbc:RegistrationName>
                </cac:PartyLegalEntity>
            </cac:Party>
        </cac:AccountingSupplierParty>
        """
        return details_as_xml

    def _get_customer_party(self):
        self.ensure_one()
        # if self.move_type == 'out_invoice':
        vat_no = self.partner_id.vat or ''
        zip_no = self.partner_id.zip if len(self.partner_id.zip or '') == 5 else ''
        state_code = self.partner_id.state_id.code or ''
        partner_name = self.partner_id.display_name
        partner_phone = self.partner_id.phone or ''
        # else:
        #     vat_no = self.company_id.vat or ''
        #     zip_no = self.company_id.zip if len(self.company_id.zip or '') == 5 else ''
        #     state_code = self.company_id.state_id.code or ''
        #     partner_name = self.company_id.name
        #     partner_phone = self.company_id.phone or ''
        details_as_xml = f"""
        <cac:AccountingCustomerParty>
            <cac:Party>
                <cac:PartyIdentification>
                    <cbc:ID schemeID="{'TN'}">{vat_no}</cbc:ID>
                </cac:PartyIdentification>
                <cac:PostalAddress>
                    <cbc:PostalZone>{zip_no}</cbc:PostalZone>
                    <cbc:CountrySubentityCode>{state_code}</cbc:CountrySubentityCode>
                    <cac:Country>
                        <cbc:IdentificationCode>JO</cbc:IdentificationCode>
                    </cac:Country>
                </cac:PostalAddress>
                <cac:PartyTaxScheme>
                    <cbc:CompanyID>{'1'}</cbc:CompanyID>
                    <cac:TaxScheme>
                        <cbc:ID>VAT</cbc:ID>
                    </cac:TaxScheme>
                </cac:PartyTaxScheme>
                <cac:PartyLegalEntity>
                    <cbc:RegistrationName>{partner_name}</cbc:RegistrationName>
                </cac:PartyLegalEntity>
            </cac:Party>
            <cac:AccountingContact>
                <cbc:Telephone>{partner_phone}</cbc:Telephone>
            </cac:AccountingContact>
        </cac:AccountingCustomerParty>
        """
        return details_as_xml

