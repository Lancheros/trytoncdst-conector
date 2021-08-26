from trytond.pool import Pool

#import wiz
import conector
import party
import product
import sale
import configuration

def register():
    Pool.register(
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
        sale.Cron,
        configuration.Configuration,
        #wiz.ActualizarVentas,
        module='conector', type_='model')

    Pool.register(
        #wiz.ActualizarVentas,
        module='conector', type_='wizard')

