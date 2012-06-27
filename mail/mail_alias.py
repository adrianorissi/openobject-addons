# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from tools.translate import _

class mail_alias(osv.Model):
    """A Mail Alias is a mapping of an email address with a given OpenERP Document
       model. It is used by OpenERP's mail gateway when processing incoming emails
       sent to the system. If the recipient address (To) of the message matches
       a Mail Alias, the message will be either processed following the rules
       of that alias. If the message is a reply it will be attached to the
       existing discussion on the corresponding record, otherwise a new
       record of the corresponding model will be created.
       
       This is meant to be used in combination with a catch-all email configuration
       on the company's mail server, so that as soon as a new mail.alias is
       created, it becomes immediately usable and OpenERP will accept email for it.
     """
    _name = 'mail.alias'
    _description = "Mail Alias"
    _rec_name = 'alias_name'

    _columns = {
        'alias_name': fields.char('Mailbox Alias', size=255, required=True,
                            help="The name of the mailbox alias, e.g. 'jobs' "
                                 "if you want to catch emails for <jobs@example.my.openerp.com>",),
        'alias_model_id': fields.many2one('ir.model', 'Aliased Model', required=True,
                                          help="The model (OpenERP Document Kind) to which this alias "
                                               "corresponds. Any incoming email that does not reply to an "
                                               "existing record will cause the creation of a new record "
                                               "of this model (e.g. a Project Task)",
                                          # only allow selecting mail_thread models!
                                          #TODO kept doamin temporarily in comment, need to redefine domain
                                          #domain="[('field_id', 'in', 'message_ids')]"
                                          ),
        'alias_user_id': fields.many2one('res.users', 'Owner',
                                           help="The owner of records created upon receiving emails on this alias. "
                                                "If this field is kept empty the system will attempt to find the right owner "
                                                "based on the sender (From) address, or will use the Administrator account "
                                                "if no system user is found for that address."),
        'alias_defaults': fields.text('Default Values', required=True,
                                      help="The representation of a Python dictionary that will be evaluated to provide "
                                           "default values when creating new records."),
        'alias_force_thread_id': fields.integer('Record Thread ID',
                                      help="Optional ID of the thread (record) to which all "
                                           "messages will be attached, even if they did not reply to it. "
                                           "If set, this will disable the creation of new records completely.")
    }
    _defaults = {
        'alias_defaults': '{}',
        'alias_user_id': lambda s,c,u,ctx: u
    }
    _sql_constraints = [
        ('mailbox_uniq', 'UNIQUE(alias_name)', 'Unfortunately this mail alias is already used, please choose a unique one')
    ]
    
    def create_unique_alias(self, cr, uid, values, sequence=1 ,context=None):
        config_parameter_pool = self.pool.get("ir.config_parameter")
        domain = config_parameter_pool.get_param(cr, uid, "mail.catchall.domain", context=context)
        if sequence:
            prob_alias = "%s%s@%s"%(values['alias_name'], sequence, domain)
            search_alias = self.search(cr, uid, [('alias_name', '=', prob_alias)])
            if search_alias:    
                values = self.create_unique_alias(cr, uid, values, sequence+1, context)
            else:
                values.update({'alias_name': prob_alias})
                return values
        else:
            return values.update({'alias_name': "%s@%s"%(values['alias_name'],domain)})

    def write(self, cr, uid, ids, vals, context=None):
        config_parameter_pool = self.pool.get("ir.config_parameter")
        #TODO: Do we need to check specail charactor like email address parsing
        #     Like allowing . and _ only.
        if 'alias_name' in vals.keys():
            domain = config_parameter_pool.get_param(cr, uid, "mail.catchall.domain", context=context)
            #check the new alias, If only alias then concat the domain
            #if we have alias_name with random domain we will concat our domain.
            if vals.get('alias_name').count("@") == 0:
                vals.update({'alias_name': "%s@%s"%(vals.get('alias_name'), domain)})
            elif vals.get('alias_name').count("@") == 1:
                name =  "%s@%s"%(vals.get('alias_name').split("@")[0], domain)
                vals.update({'alias_name': name})
            else:
                raise osv.except_osv(_("Warning !"), _("Invalid mail alias name.\n It should be e.g. 'alias@domain.com' or only alias name 'alias'."))
        return super(mail_alias, self).write(cr, uid, ids, vals, context=context)

