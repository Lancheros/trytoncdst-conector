from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.exceptions import UserError
import logging

__all__ = [
    'SaleDevice',
    'Journal'
    'Cron',
    ]


class Cron(metaclass=PoolMeta):
    'Cron'
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.method.selection.append(
            ('sale.device|import_data_pos', "Importar Pos"),
            )


#Heredar para agregar el campo id_tecno
class SaleDevice(metaclass=PoolMeta):
    'SaleDevice'
    __name__ = 'sale.device'
    id_tecno = fields.Char('Id Tabla Sqlserver', required=False)

    @classmethod
    def import_data_pos(cls):
        #Se requiere previamente haber creado el diario para ventas POS con código VM
        #Posterior a la importación. revisar las configuraciones
        logging.warning("RUN CONFIG POS")
        cls.create_or_update()
        cls.import_sale_shop()
        cls.import_sale_device()
        cls.import_statement_sale()
        #Transaction().connection.commit()
        #msg1 = f'Recordatorio: Revisar las configuraciones de Tiendas, Terminales de venta y Libros diarios (formas de pago) de las terminales...'
        #logging.warning(msg1)
        logging.warning("FINISH CONFIG POS")
        #raise UserError("RECORDATORIO: ", "Revisa las configuraciones de las tiendas, terminales de venta y libros diarios (formas de pago) de las terminales...")

    @classmethod
    def import_sale_shop(cls):
        bodegas = cls.get_data_table('TblBodega')
        pool = Pool()
        Shop = pool.get('sale.shop')
        location = pool.get('stock.location')
        payment_term = Pool().get('account.invoice.payment_term')
        payment_term, = payment_term.search([], order=[('id', 'DESC')], limit=1)
        currency = pool.get('currency.currency')
        moneda, = currency.search([('code', '=', 'COP')])
        to_create = []
        for bodega in bodegas:
            id_tecno = bodega.IdBodega
            location = location.search([('id_tecno', '=', id_tecno)])
            if not location:
                raise UserError("Error de bodega", "LA BODEGA DE TECNOCARNES CON ID {id_tecno} NO EXISTE")
            nombre = bodega.Bodega
            location = location[0]
            existe = Shop.search([('warehouse', '=', location)])
            company = Transaction().context.get('company')
            if not existe:
                shop = {
                    'name': nombre,
                    'warehouse': location,
                    'currency': moneda,
                    'company': company,
                    'payment_term': payment_term,
                    'sale_invoice_method': 'order',
                    'sale_shipment_method': 'order'
                }
                shop = cls.sequence_sale(shop)
                shop = cls.price_list_sale(shop)
                to_create.append(shop)
        Shop.create(to_create)


    @classmethod
    def price_list_sale(cls, shop):
        pool = Pool()
        Price_list = pool.get('product.price_list')
        price_list = Price_list.search([], order=[('id', 'DESC')], limit=1)

        if price_list:
            shop['price_list'] = price_list[0]
        else:
            price_list = {
                'name': 'Lista de precio POS',
                'company': 1,
                'unit': 'product_default'
            }
            price_list, = Price_list.create([price_list])
            shop['price_list'] = price_list
        return shop

    #Crear secuencia para las ventas
    @classmethod
    def sequence_sale(cls, shop):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        sequence_t = cls.find_seq('Sale')
        sequence1 = Sequence.search([('sequence_type', '=', sequence_t[0])])
        if sequence1:
            shop['sale_sequence'] = sequence1[0]
            shop['sale_return_sequence'] = sequence1[0]
        else:
            sequence2 = {
                'name': 'Venta',
                'number_increment': 1,
                'number_next_internal': 1,
                'padding': 0,
                'sequence_type': sequence_t,
                'type': 'incremental'
            }
            sequence2, = Sequence.create([sequence2])
            shop['sale_sequence'] = sequence2
            shop['sale_return_sequence'] = sequence2
        return shop

    #Función encargada de consultar la secuencia de un nombre dado
    @classmethod
    def find_seq(cls, name):
        Sequence = Pool().get('ir.sequence.type')
        seq = Sequence.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*seq.select(where=(seq.name == name)))
        result = cursor.fetchall()
        return result[0]

    #CREAR TERMINALES DE VENTA
    @classmethod
    def import_sale_device(cls):
        pool = Pool()
        SaleD = pool.get('sale.device')
        Location = pool.get('stock.location')
        #obtengo la tienda actual
        Shop = pool.get('sale.shop')
        equipos = cls.get_data_table('TblEquipo')
        
        to_create = []
        for equipo in equipos:
            id_equipo = equipo.IdEquipo
            nombre = equipo.Equipo
            ubicacion = equipo.Ubicacion
            location = Location.search([('id_tecno', '=', ubicacion)])
            if location:
                shop = Shop.search([('warehouse', '=', location[0])])
                if shop:
                    shop = shop[0]
                else:
                    shop, = Shop.search([], order=[('id', 'DESC')], limit=1)
            else:
                shop, = Shop.search([], order=[('id', 'DESC')], limit=1)
            #En caso de ser un nombre vacio se continua con el siguiente
            if len(nombre) == 0 or nombre == ' ':
                continue
            
            device = SaleD.search([('id_tecno', '=', id_equipo)])
            if not device:
                sale_data = {
                    'id_tecno': id_equipo,
                    'name': nombre,
                    'code': id_equipo,
                    'shop': shop,
                    'environment': 'retail'
                }
                to_create.append(sale_data)
        SaleD.create(to_create)


    #Libro de Ventas Pos
    @classmethod
    def import_statement_sale(cls):
        forma_pago = cls.get_data_table('TblFormaPago')
        pool = Pool()
        Account = pool.get('account.account')
        Journal = pool.get('account.statement.journal')
        Ajournal = pool.get('account.journal')
        #currency = pool.get('currency.currency')
        #moneda, = currency.search([('code', '=', 'COP')])
        #company = Transaction().context.get('company')
        to_create = []
        for fp in forma_pago:
            idt = str(fp.IdFormaPago)
            journal = Journal.search([('id_tecno', '=', idt)])
            if not journal:
                nombre = fp.FormaPago
                cuenta, = Account.search([('code', '=', '110505')])
                diario, = Ajournal.search([('code', '=', 'VM')])
                statement_journal = {
                    'id_tecno': idt,
                    'name': nombre,
                    'journal': diario,
                    'account': cuenta,
                    'payment_means_code': '1',
                    'kind': 'other',
                }
                to_create.append(statement_journal)
        Journal.create(to_create)

    #Crea o actualiza un registro de la tabla actualización en caso de ser necesario
    @classmethod
    def create_or_update(cls):
        Actualizacion = Pool().get('conector.actualizacion')
        actualizacion = Actualizacion.search([('name', '=','CONFIG_POS')])
        if actualizacion:
            #Se busca un registro con la actualización
            actualizacion, = Actualizacion.search([('name', '=','CONFIG_POS')])
            actualizacion.name = 'CONFIG_POS'
            actualizacion.save()
        else:
            #Se crea un registro con la actualización
            actualizar = Actualizacion()
            actualizar.name = 'CONFIG_POS'
            actualizar.save()


    @classmethod
    def get_data_table(cls, table):
        Config = Pool().get('conector.configuration')
        consult = "SELECT * FROM dbo."+table+""
        result = Config.get_data(consult)
        return result

#Heredar para agregar el campo id_tecno
class Journal(metaclass=PoolMeta):
    'StatementJournal'
    __name__ = 'account.statement.journal'
    id_tecno = fields.Char('Id Tabla Sqlserver', required=False)