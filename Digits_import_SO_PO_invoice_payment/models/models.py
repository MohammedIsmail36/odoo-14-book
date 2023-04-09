from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ast import literal_eval


class ImportInvoicePayment(models.Model):
    _name = 'digits.import'
    _description = 'Digits_import_SO_PO_invoice_payment'


    name = fields.Char(readonly=True)
    order_no = fields.Char('Reference', required=True)
    type = fields.Selection([('sales', 'Sales Order')], string='Type', required=True,
                            default='sales') # , ('purchase', 'Purchase')
    # order_status = fields.Selection([('done', 'Done/ /Returned'), ('full_returned', 'Full Returned'),
    #                                  ('returned_without_payment', 'Returned Without Payment'), ('canceled', 'Canceled')],
    #                                 string='Type', required=True, default='done')

    # Partner Information fields =====
    # , compute = '_get_partner_id'
    partner_id = fields.Many2one('res.partner')
    email = fields.Char()
    mobile = fields.Char('Mobile', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    city_id = fields.Char(string='City of Address')
    state_id = fields.Many2one("res.country.state", string='State')

    #
    # country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', help="Select the Country",
    #                              default=lambda self: self.env.user.company_id.country_id)
    # city_id = fields.Many2one('res.city', string='City of Address', domain="[('state_id', '=', state_id)]",
    #                           default=lambda self: self.env.user.company_id.city_id)
    # state_id = fields.Many2one("res.country.state", string='State', help="Select the State where you are from",
    #                            ondelete='restrict', domain="[('country_id', '=', country_id)]",
    #                            default=lambda self: self.env.user.company_id.state_id)

    analytic_account = fields.Many2one('account.analytic.account')
    store_id = fields.Many2one('stock.location')
    currency_id = fields.Many2one('res.currency')
    tax_id = fields.Many2one('account.tax')
    inv_journal = fields.Many2one('account.journal', domain="[('type', '=', 'sale')]", required=True)
    invoice_date = fields.Date('Invoice Date', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    description = fields.Char('description', required=True, default='/')
    # product_uom_id = fields.Many2one('uom.uom', required=True)

    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                                     domain="[('category_id', '=', product_uom_category_id)]", ondelete="restrict", required=True)
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    quantity = fields.Float()
    price = fields.Float()
    discount = fields.Float()

    pmt_journal = fields.Many2one('account.journal')
    payment_amount = fields.Float()
    payment_date = fields.Date()
    partial_payment = fields.Selection([('keep', 'Keep Open'), ('writeoff', 'Write-Off')],
                                       string="Partial Payment", default='writeoff')
    writeoff_account = fields.Many2one('account.account', string="Write-Off Account", default='204')
    # allow_payment = fields.Boolean(string="Allow Payment Amount more then Invoice Amount", default=True)

    fob = fields.Char('FOB')
    awb = fields.Char("AWB")
    customer_name = fields.Char('Customer ')
    imp_ref03 = fields.Char()
    imp_ref04 = fields.Char()
    imp_ref05 = fields.Char()
    imp_ref06 = fields.Char()
    imp_ref07 = fields.Char()
    imp_ref08 = fields.Char()
    # imp_ref09 = fields.Char("Client Name")

    invoiced = fields.Boolean(default=False)
    is_paid = fields.Boolean(default=False)
    cr_invoice_id = fields.Many2one('account.move')
    cr_payment_id = fields.Many2one('account.payment')
    active = fields.Boolean(default=True)
    force_create = fields.Boolean(default=False)
    cont = fields.Boolean(default=False)


    # Reference Fields ( Can be Invisible)
    sale_order_name = fields.Char('SO Name')
    sale_order_id = fields.Char('SO Id')
    sale_order_draft = fields.Boolean('SO Draft', default=False)
    sale_order_confirm = fields.Boolean('SO Confirmed', default=False)
    stock_picking_id = fields.Char('Stock Picking Id')
    draft_invoiced = fields.Boolean('Draft Invoiced', default=False)


    # Override Create Method
    @api.model
    def create(self, vals):
        res = super(ImportInvoicePayment, self).create(vals)
        res.create_partner()
        return res

    # Create Partner if not exist
    def create_partner(self):
        for rec in self:
            partner_obj = self.env['res.partner']
            count = partner_obj.search_count([('mobile', '=', rec.mobile)])
            if count == 0:
                partner_obj.create({'name': rec.mobile,
                                    'email': rec.email,
                                    'mobile': rec.mobile,
                                    'country_id': rec.country_id.id,
                                    'city': rec.city_id,
                                    'state_id': rec.state_id.id})
            rec.partner_id = partner_obj.search([('mobile', '=', rec.mobile)]).id

    # Check All Lines Before Post Lines
    def is_valid_order_nos(self, order_nos):
        order_refs = set([line[0] for line in order_nos])
        for ref in order_refs:
            ref_nums = [line[1] for line in order_nos if line[0] == ref]
            if len(set(ref_nums)) > 1:
                return False
        return True

    # Pass Lines To is_valid_order_nos Method
    def validate_lines(self):
        order_nos = []
        for rec in self:
            order_nos.append([rec.order_no, rec.partner_id.id])
        if not self.is_valid_order_nos(order_nos):
            raise ValidationError(_("the Same order numbers must have the same partner"))

    # sale_orders_obj = self.env['sale.order']
    # for record in self:
    #     sale_orders =  self.env['sale.order'].search([('id', '=', self.sale_order_id)])
    #     if record.sale_order_id and record.sale_order_confirm and record.stock_picking_id:
    #         # sale_orders = sale_orders_obj.search([('id', '=', self.sale_order_id)])
    #         print(sale_orders)
    def get_order_ids(self):
        order_ids = []
        for rec in self:
            if rec.sale_order_id:
                sale_order = self.env['sale.order'].search([('id', '=', rec.sale_order_id)])
                if sale_order not in order_ids:
                    order_ids.append(sale_order)
        return order_ids

    # Get all Line based domain
    def get_lines(self):
        sub_lines = []
        for rec in self:
            order_line = self.search(
                [('order_no', '=', rec.order_no), ('partner_id', '=', rec.partner_id.id), ('active', '=', True)])
            if order_line not in sub_lines:
                sub_lines.append(order_line)
        return sub_lines

    # Create sale Order Line Method
    def create_sale_order_line(self, product_id, description, quantity, price, tax_id, product_uom):
        so_line = [0,0, {'product_id': product_id,
                'name': description,
                'product_uom_qty': quantity,
                'price_unit': price,
                'tax_id': tax_id,
                'product_uom': product_uom}]
        return so_line

    # Get Sales Order Ids:
    def get_sales_orders(self):
        sales_order_obj = self.env['sale.order']
        for record in self:
            # if not record.sale_order_id and record.sale_order_draft:
            sale_order_search = sales_order_obj.search([('digit_import_order', '=', record.order_no)])
            record.sale_order_id = sale_order_search.id
            record.sale_order_name = sale_order_search.name
            sales_order_obj.update({'digit_import_order_id': record.id})
            # else :
            #     raise ValidationError(_("Has Sale Order already"))

    # Method Confirm Sale Order
    def confirm_sales_order(self):
        sales_order_obj = self.env['sale.order']
        for record in self:
            if record.sale_order_id and not record.sale_order_confirm:
                # Find the sales order you want to confirm:
                sale_order = sales_order_obj.search([('id', '=', record.sale_order_id)])
                # Confirm the sales order:
                if sale_order and sale_order.state == 'done':
                    record.sale_order_confirm = True
                else:
                    sale_order.action_confirm()
                    record.sale_order_confirm = True

    # set quantities to reservation and Validation
    def set_quantities_validation(self):
        stock_picking_obj = self.env['stock.picking']
        for record in self:
            if record.sale_order_id and record.sale_order_confirm and not record.stock_picking_id:
                stock_picking = stock_picking_obj.search([('sale_id.id', '=', record.sale_order_id)])
                if stock_picking.state == 'done':
                    record.stock_picking_id = stock_picking.id
                else:
                    stock_picking.action_set_quantities_to_reservation()
                    stock_picking.button_validate()
                    record.stock_picking_id = stock_picking.id

    # Post Lines
    def post_lines(self):
        self.validate_lines()
        sub_lines = self.get_lines()
        for line in sub_lines:
            multi_lines = []
            for sl in line:
                tax_ids = [(6, 0, [self.tax_id.id])] if self.tax_id else [(6, 0, [])]
                r = self.create_sale_order_line(sl.product_id.id, sl.description, sl.quantity, sl.price, tax_ids, sl.product_uom_id.id)
                multi_lines.append(r)
            print(" ========== Multi Line ======== ", multi_lines)
            order_obj = self.env['sale.order']
            order_obj.create({'partner_id': line[0].partner_id.id,
                                           'date_order': line[0].invoice_date,
                                           'digit_import_order': line[0].order_no,
                                           'order_line': multi_lines})
            line.sale_order_draft = True
            print(" ========== inv_journal ======== ", line[0].inv_journal.id)
            # print(" ========== inv_journal ======== ", line[0].di.id)
            # Call Method Get Sales Order Ids:
            self.get_sales_orders()
            self.confirm_sales_order()
            self.set_quantities_validation()
            self.create_invoices(line[0].inv_journal.id)

    #
    # def unlink(self):
    #     for rec in self:
    #         if rec.sale_order_confirm:
    #             raise UserError(_("You Can't Delete this %s it has a confirmed sales order") % (rec.order_no))
    #     rtn = super(ImportInvoicePayment, self).unlink()
    #     return rtn

    # ===============================================================================================
    # Create invoices for selected sales orders
    def create_invoice_line(self, product_id, quantity, price_unit, name, tax_ids):
        inv_line = [0, 0, {'product_id': product_id,
                          'name': name,
                          'quantity': quantity,
                          'price_unit': price_unit,
                          'tax_ids': tax_ids}]
        return inv_line

    # , inv_journal, discount
    def create_invoices(self, inv_journal):
        sales_order_ids = self.get_order_ids()
        # invoices = self.env['account.move']
        for order in sales_order_ids:
            # Populate the invoice with sales order data
            invoice_lines = []
            for line in order.order_line:
                l = self.create_invoice_line(line.product_id.id, line.product_uom_qty, line.price_unit, line.name, [(6, 0, line.tax_id.ids)])
                invoice_lines.append(l)

            # Create a new invoice
            invoice = self.env['account.move'].create({
                'partner_id': order.partner_id.id,
                'invoice_date': order.date_order,
                'invoice_origin': order.name,
                'digit_sale_order_id': order.id,
                'journal_id': inv_journal,
                'move_type': 'out_invoice',
                # Invoice Line:
                'invoice_line_ids': invoice_lines
            })

            # Calculate the invoice total
            invoice.amount_total = sum(line.price_subtotal for line in invoice.invoice_line_ids)
            order.invoice_ids = [(6, 0, [invoice.id])]
            order.invoice_status = 'invoiced'
            order.state = 'sale'
            invoice.action_post()
            self.invoiced = True
            self.cr_invoice_id = invoice.id

class MoveAccount(models.Model):
    _inherit = 'account.move'

    digit_sale_order_id = fields.Many2one('sale.order', string="Sale Order Id")


    imp_fob = fields.Char('FOB')
    imp_ref1 = fields.Char()
    imp_ref2 = fields.Char()
    imp_ref3 = fields.Char()
    imp_ref4 = fields.Char()
    imp_ref5 = fields.Char()
    imp_ref6 = fields.Char()
    imp_ref7 = fields.Char()
    imp_ref8 = fields.Char()


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def _get_invoice_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('digit_sale_order_id', '=', self.id)])
            rec.digit_invoice_count = count

    # Smart Button Function
    def open_digit_import_Invoice(self):
        return {
            'name': 'Digits Import Invoice',
            'view_type': 'form',
            'domain': [('digit_sale_order_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    # Fields
    digit_import_order = fields.Char("Digits Import Order No")
    digit_import_order_id = fields.Many2one('digits.import')
    digit_invoice_count = fields.Integer("Digits Import Invoice", compute='_get_invoice_count')

    @api.model
    def create(self, values):
        print("Sale Order vals=======", values)
        return super(SaleOrder, self).create(values)

    def unlink(self):
        print("Self", self)
        for rec in self:
            if rec.digit_import_order:
                raise UserError(_("You Can't Delete this Quotation it has order no:  %s") % (rec.digit_import_order))
        rtn = super(SaleOrder, self).unlink()
        return rtn

