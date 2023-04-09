# -*- coding: utf-8 -*-
# from odoo import http


# class ImportInvoicePayment(http.Controller):
#     @http.route('/Digits_import_SO_PO_invoice_payment/Digits_import_SO_PO_invoice_payment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/Digits_import_SO_PO_invoice_payment/Digits_import_SO_PO_invoice_payment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('Digits_import_SO_PO_invoice_payment.listing', {
#             'root': '/Digits_import_SO_PO_invoice_payment/Digits_import_SO_PO_invoice_payment',
#             'objects': http.request.env['Digits_import_SO_PO_invoice_payment.Digits_import_SO_PO_invoice_payment'].search([]),
#         })

#     @http.route('/Digits_import_SO_PO_invoice_payment/Digits_import_SO_PO_invoice_payment/objects/<model("Digits_import_SO_PO_invoice_payment.Digits_import_SO_PO_invoice_payment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('Digits_import_SO_PO_invoice_payment.object', {
#             'object': obj
#         })
