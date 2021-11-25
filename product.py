from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
import datetime
from decimal import Decimal
from trytond.exceptions import UserError


__all__ = [
    'Product',
    'ProductCategory',
    'Cron',
    ]


class Cron(metaclass=PoolMeta):
    'Cron'
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.method.selection.append(
            ('product.product|update_products', "Update products"),
            )


class Product(ModelSQL, ModelView):
    'Products'
    __name__ = 'product.product'
    id_tecno = fields.Char('Id TecnoCarnes', required=False)

    #Función encargada de crear o actualizar los productos y categorias de db TecnoCarnes,
    #teniendo en cuenta la ultima fecha de actualizacion y si existe o no.
    @classmethod
    def update_products(cls):
        print("---------------RUN PRODUCTOS---------------")
        productos_tecno = cls.last_update()
        cls.create_or_update()
        col_pro = cls.get_columns_db_tecno('TblProducto')
        modelos = cls.get_modelos_tecno()

        #Creación o actualización de las categorias de los productos
        Category = Pool().get('product.category')
        #to_category = []
        for modelo in modelos:
            id_tecno = modelo[0]
            nombre = str(id_tecno)+' - '+modelo[1].strip()
            
            existe = cls.buscar_categoria(id_tecno)
            if existe:
                existe.name = nombre
                existe.accounting = True
                cls.set_account(modelo, existe)
                existe.save()
            else:
                categoria = Category()
                categoria.id_tecno = id_tecno
                categoria.name = nombre
                categoria.accounting = True
                categoria.save()
                cls.set_account(modelo, categoria)
                
                #to_category.append(categoria)
        #print(to_category)
        #Category.save(to_category)

        if productos_tecno:
            #Creación de los productos con su respectiva categoria e información
            Producto = Pool().get('product.product')
            Template_Product = Pool().get('product.template')
            to_producto = []
            for producto in productos_tecno:
                id_producto = str(producto[col_pro.index('IdProducto')])
                existe = cls.buscar_producto(id_producto)
                id_categoria = producto[col_pro.index('contable')]
                #print(id_categoria)
                categoria_contable = Category.search([('id_tecno', '=', id_categoria)])
                if categoria_contable:
                    categoria_contable = categoria_contable[0]
                else:
                    categoria = Category()
                    categoria.id_tecno = id_categoria
                    categoria.name = 'sin modelo'
                    categoria.accounting = True
                    categoria_contable = categoria
                    categoria.save()
                nombre_producto = producto[col_pro.index('Producto')].strip()
                tipo_producto = cls.tipo_producto(producto[col_pro.index('maneja_inventario')])
                udm_producto = cls.udm_producto(producto[col_pro.index('unidad_Inventario')])
                vendible = cls.vendible_producto(producto[col_pro.index('TipoProducto')])
                valor_unitario = producto[col_pro.index('valor_unitario')]
                #costo_unitario = producto[col_pro.index('costo_unitario')]
                ultimo_cambio = producto[col_pro.index('Ultimo_Cambio_Registro')]
                if existe:
                    #if (True):
                    if (ultimo_cambio and existe.write_date and ultimo_cambio > existe.write_date) or (ultimo_cambio and not existe.write_date and ultimo_cambio > existe.create_date):
                        existe.template.name = nombre_producto
                        existe.template.type = tipo_producto
                        existe.template.default_uom = udm_producto
                        existe.template.salable = vendible
                        if vendible:
                            existe.template.sale_uom = udm_producto
                        existe.template.list_price = valor_unitario
                        #existe.cost_price = costo_unitario
                        #existe.template.categories = [categoria_producto]
                        existe.template.account_category = categoria_contable.id
                        existe.template.save()
                else:
                    prod = Producto()
                    prod.id_tecno = id_producto
                    temp = Template_Product()
                    temp.code = id_producto
                    temp.name = nombre_producto
                    temp.type = tipo_producto
                    temp.default_uom = udm_producto
                    temp.purchasable = True
                    temp.purchase_uom = udm_producto
                    temp.salable = vendible
                    if vendible:
                        temp.sale_uom = udm_producto
                    temp.list_price = valor_unitario
                    #prod.cost_price = costo_unitario
                    #temp.categories = [categoria_producto]
                    temp.account_category = categoria_contable.id
                    prod.template = temp
                    to_producto.append(prod)
            Producto.save(to_producto)


    #Función encargada de consultar si existe una categoria dada de la bd TecnoCarnes
    @classmethod
    def buscar_categoria(cls, id_categoria):
        Category = Pool().get('product.category')
        try:
            categoria_producto, = Category.search([('id_tecno', '=', id_categoria)])
        except ValueError:
            return False
        else:
            return categoria_producto
    
    @classmethod
    def set_account(cls, modelo, category):
        Account = Pool().get('account.account')
        CategoryAccount = Pool().get('product.category.account')

        l_expense = list(modelo[2])
        expense = False
        if l_expense[0] != '1':
            expense = Account.search([('code', '=', modelo[2])])
        revenue = Account.search([('code', '=', modelo[3])])
        return_sale = Account.search([('code', '=', modelo[4])])

        CategoryAccount, = CategoryAccount.search([('category', '=', category.id)])
        if expense:
            CategoryAccount.account_expense = expense[0]
        if revenue:
            CategoryAccount.account_revenue = revenue[0]
        if return_sale:
            category.account_return_sale = return_sale[0]

    #Esta función se encarga de traer todos los datos de una tabla dada de la bd TecnoCarnes
    @classmethod
    def get_modelos_tecno(cls):
        data = []
        try:
            Config = Pool().get('conector.configuration')
            conexion = Config.conexion()
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT IdModelos, max(Modelos), max(cuenta1), max(cuenta3), max(cuenta4) FROM dbo.TblModelos group by IdModelos")
                data = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY get_modelos_tecno: ", e)
            raise UserError("ERROR QUERY get_modelos_tecno: ", str(e))
        return data

    #Función encargada de consultar si existe un producto dado de la bd TecnoCarnes
    @classmethod
    def buscar_producto(cls, id_producto):
        Product = Pool().get('product.product')
        try:
            producto, = Product.search([('id_tecno', '=', id_producto)])
        except ValueError:
            return False
        else:
            return producto

    #Función encargada de retornar que tipo de producto será un al realizar la equivalencia con el manejo de inventario de la bd de TecnoCarnes
    @classmethod
    def tipo_producto(cls, inventario):
        #equivalencia del tipo de producto (si maneja inventario o no)
        if inventario == 'N':
            return 'service'
        else:
            return 'goods'

    #Función encargada de retornar la unidad de medida de un producto, al realizar la equivalencia con kg y unidades de la bd de TecnoCarnes
    @classmethod
    def udm_producto(cls, udm):
        #Equivalencia de la unidad de medida en Kg y Unidades.
        if udm == 1:
            return 2
        else:
            return 1

    #Función encargada de verificar si el producto es vendible, de acuerdo a su tipo
    @classmethod
    def vendible_producto(cls, tipo):
        columns_tiproduct = cls.get_columns_db_tecno('TblTipoProducto')
        tiproduct = None
        try:
            Config = Pool().get('conector.configuration')
            conexion = Config.conexion()
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo.TblTipoProducto WHERE IdTipoProducto = "+str(tipo))
                tiproduct = query.fetchone()
        except Exception as e:
            print("ERROR QUERY TblTipoProducto: ", e)
        #Se verifica que el tipo de producto exista y el valor si es vendible o no
        if tiproduct and tiproduct[columns_tiproduct.index('ProductoParaVender')] == 'S':
            return True
        else:
            return False


    #Función encargada de consultar las columnas pertenecientes a 'x' tabla de la bd de TecnoCarnes
    @classmethod
    def get_columns_db_tecno(cls, table):
        columns = []
        try:
            Config = Pool().get('conector.configuration')
            conexion = Config.conexion()
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '"+table+"' ORDER BY ORDINAL_POSITION")
                for q in query.fetchall():
                    columns.append(q[0])
        except Exception as e:
            print("ERROR QUERY "+table+": ", e)
        return columns

    #Esta función se encarga de traer todos los datos de una tabla dada de la bd TecnoCarnes
    @classmethod
    def get_data_db_tecno(cls, table):
        data = []
        try:
            Config = Pool().get('conector.configuration')
            conexion = Config.conexion()
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo."+table)
                data = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY "+table+": ", e)
        return data

    #Esta función se encarga de traer todos los datos de una tabla dada de acuerdo al rango de fecha dada de la bd TecnoCarnes
    @classmethod
    def get_data_where_tecno(cls, table, date):
        data = []
        try:
            Config = Pool().get('conector.configuration')
            conexion = Config.conexion()
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo."+table+" WHERE fecha_creacion >= CAST('"+date+"' AS datetime) OR Ultimo_Cambio_Registro >= CAST('"+date+"' AS datetime)")
                data = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY get_data_where_tecno: ", e)
        return data

    #Función encargada de traer los datos de la bd TecnoCarnes con una fecha dada.
    @classmethod
    def last_update(cls):
        Actualizacion = Pool().get('conector.actualizacion')
        #Se consulta la ultima actualización realizada para los terceros
        ultima_actualizacion = Actualizacion.search([('name', '=','PRODUCTOS')])
        if ultima_actualizacion:
            #Se calcula la fecha restando la diferencia de horas que tiene el servidor con respecto al clienete
            if ultima_actualizacion[0].write_date:
                fecha = (ultima_actualizacion[0].write_date - datetime.timedelta(hours=5))
            else:
                fecha = (ultima_actualizacion[0].create_date - datetime.timedelta(hours=5))
        else:
            fecha = datetime.date(1,1,1)
        fecha = fecha.strftime('%Y-%d-%m %H:%M:%S')
        data = cls.get_data_where_tecno('TblProducto', fecha)
        return data

    #Crea o actualiza un registro de la tabla actualización en caso de ser necesario
    @classmethod
    def create_or_update(cls):
        Actualizacion = Pool().get('conector.actualizacion')
        actualizacion = Actualizacion.search([('name', '=','PRODUCTOS')])
        if actualizacion:
            #Se busca un registro con la actualización
            actualizacion, = Actualizacion.search([('name', '=','PRODUCTOS')])
            actualizacion.name = 'PRODUCTOS'
            actualizacion.save()
        else:
            #Se crea un registro con la actualización
            actualizar = Actualizacion()
            actualizar.name = 'PRODUCTOS'
            actualizar.save()

    #Selecciona el impuesto equivalente en la bd Sqlserver
    @classmethod
    def select_tax(cls, tax):
        Tax = Pool().get('account.tax')
        try:
            if tax == 3:
                tax, = Tax.search([('name', '=', 'IVA 19,0%')])
                return tax.id
            elif tax == 4:
                tax, = Tax.search([('name', '=', 'IVA 5,0%')])
                return tax.id
            elif tax == 5:
                tax, = Tax.search([('name', '=', 'IVA SERVICIOS 19,0%')])
                return tax.id
            else:
                return False
        except Exception as e:
            raise UserError("Error al seleccionar el impuesto para la categoria: ", e)

#Herencia del party.contact_mechanism e insercción del campo id_tecno
class ProductCategory(ModelSQL, ModelView):
    'ProductCategory'
    __name__ = 'product.category'
    id_tecno = fields.Char('Id TecnoCarnes', required=False)