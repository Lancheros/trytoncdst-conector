from trytond.pool import Pool

#import wiz
import conector
import party
import product
import sale
import configuration
import voucher
import pay_mode
from . import electronic_payroll_wizard
from . import company
from . import payment_term

def register():
    Pool.register(
        company.Company,
        conector.Actualizacion,
        party.Party,
        party.PartyAddress,
        party.ContactMechanism,
        party.Cron,
        product.Product,
        product.ProductCategory,
        product.Cron,
        sale.Sale,
        sale.SaleLine,
        sale.Location,
        sale.Cron,
        configuration.Configuration,
        voucher.Cron,
        voucher.Voucher,
        pay_mode.Cron,
        pay_mode.VoucherPayMode,
        payment_term.PaymentTerm,
        module='conector', type_='model')

    Pool.register(
        electronic_payroll_wizard.PayrollElectronicCdst,
        module='conector', type_='wizard')

