from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class SaleOrder(models.Model):
    
    _inherit = 'sale.order'
    
    shipping_type_id = fields.Many2one('stock.shipping.type', required=False, copy=True, string="Tipo de entrega", states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'done' : [('readonly',True)], 'sale' : [('readonly',True)]})
    shipping_payer_id = fields.Many2one('stock.shipping.payer', required=False, copy=True, string="Pago de flete", states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'done' : [('readonly',True)], 'sale' : [('readonly',True)]})
    shipping_notes = fields.Text(string="Notas de salida de almacen", required=False, copy=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'done' : [('readonly',True)], 'sale' : [('readonly',True)]})

    def create(self, values):
        order = super(SaleOrder, self).create(values)
        for line in order.order_line.filtered(lambda x: not x.display_type):
            for product_template in order.env['product.product'].browse(line.product_id.id).optional_product_ids:
                product = product_template.product_variant_id
                if product in order.sale_order_option_ids.mapped(lambda x: x.product_id):
                    continue
                product = product.with_context(lang=order.partner_id.lang)
                pricelist = order.pricelist_id
                partner_id = order.partner_id.id
                price_unit = pricelist.with_context(uom=product.uom_id.id).get_product_price(product, 1, partner_id)
                name = product.name
                if product.description_sale:
                    name += '\n' + product.description_sale
                new_values = {
                    'product_id': product.id,
                    'order_id': order.id,
                    'price_unit': price_unit,
                    'website_description': product.website_description,
                    'name': name,
                    'uom_id': product.uom_id.id,
                }
                order.write({'sale_order_option_ids':[(0, 0, new_values)]})
        return order


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    product_values_ids = fields.One2many('returned.values','sale_line_id', string="Valores del producto", copy=True)
    date_planned = fields.Datetime(string='Date planned', invisible=True, compute="_get_date_planned")

    def get_product_attributes_table(self):
        for record in self:
            if not record.is_configurable_product:
                return False
            selection_records = record.product_no_variant_attribute_value_ids.filtered(lambda x: not x.is_custom)
            custom_values = record.product_custom_attribute_value_ids
            product_attributes = record.product_template_id.attribute_line_ids.mapped('attribute_id')
            attributes={str(line.id):"" for line in product_attributes}
            # attributes = {}
            for selection in selection_records:
                attributes[str(selection.attribute_id.id)] = selection.name
            if custom_values:
                for custom in custom_values:
                    attributes[str(custom.custom_product_template_attribute_value_id.attribute_id.id)] = custom.custom_value or " "
            # names = {line.name: attributes.get(str(line.id)," ") for line in product_attributes}
            categories = self.env['product.attribute'].fields_get().get(
                'category').get('selection')
            sections = {}
            for category, name in categories:
                sections[name]= {line.name: attributes.get(str(line.id), " ") for line in product_attributes if line.category == category}
            if record.product_template_id.default_template_ids:
                fname = _('Fabrication')
                sections[fname] = {line.name : line.values for line in record.product_template_id.default_template_ids}
            return sections

    @api.depends('customer_lead')
    def _get_date_planned(self):
        for line in self:
            date = line.order_id.date_order or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            customer_lead = line.customer_lead or 0.0
            security_lead = line.order_id and line.order_id.company_id.security_lead or self.env.user.company_id.security_lead
            date_planned = date + timedelta(days=customer_lead) - timedelta(days=security_lead)
            line.date_planned = date_planned

    @api.onchange('product_id')
    def onchange_product_id(self):
        
        vals = super(SaleOrderLine,self).product_id_change()
        if self.product_id:
            list_vals = []
            self.product_values_ids = [(6,0,list_vals)]
            template_id = (self.product_id.sale_template_id and self.product_id.sale_template_id) or (self.product_id.categ_id.sale_template_id and self.product_id.categ_id.sale_template_id) or False
            if template_id:
                values_ids = self.env['sales.product.template.values'].search([('template_id','=',template_id.id)],order='sequence asc')
                for template_value_id in values_ids:
                  #values = {'name':template_value_id.name, 'field_type' : template_value_id.field_type, 'values_ids' : [(6,0,template_value_id.selection_values.ids)]}
                  values = {
                    'template_line_id':template_value_id.id, 
                    'name':template_value_id.name, 
                    'selection' : template_value_id.selection_default and template_value_id.selection_default.id or False,
                    'multi_selection' : template_value_id.multi_selection_default and template_value_id.multi_selection_default.ids or []
                    }
                  list_vals.append((0,0,values))
                self.update({'product_values_ids' : list_vals})
        return vals
        

        
    # def create(self, values):
    #     vals = super(SaleOrderLine, self).create(values)
    #     if 'order_id' in values:
    #         options = self.env['sale.order.option']
    #         for product_template in self.env['product.product'].browse(values['product_id']).optional_product_ids:
    #             product = product_template.product_variant_id
    #             order = self.env['sale.order'].browse(values['order_id'])
    #
    #             product = product.with_context(lang=self.order_id.partner_id.lang)
    #
    #             pricelist = order.pricelist_id
    #             partner_id = order.partner_id.id
    #             price_unit = pricelist.with_context(uom=product.uom_id.id).get_product_price(product, 1, partner_id)
    #             name = product.name
    #             if product.description_sale:
    #                 name += '\n' + product.description_sale
    #
    #             values = {
    #                 'product_id' : product.id,
    #                 'order_id' : order.id,
    #                 'price_unit' : price_unit,
    #                 'website_description' : product.website_description,
    #                 'name' : name,
    #                 'uom_id' : product.uom_id.id,
    #             }
    #             option_id = options.create(values)
    #
    #     return vals

        
        
