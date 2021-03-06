from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
import datetime
import logging
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
            ('product.product|update_products', "Importar productos"),
            )


class Product(ModelSQL, ModelView):
    'Products'
    __name__ = 'product.product'
    id_tecno = fields.Char('Id TecnoCarnes', required=False)

    #Función encargada de crear o actualizar los productos y categorias de db TecnoCarnes,
    #teniendo en cuenta la ultima fecha de actualizacion y si existe o no.
    @classmethod
    def update_products(cls):
        logging.warning('RUN PRODUCTOS')
        #Importa categorias contables
        cls.update_accounting_categories()

        productos_tecno = cls.last_update()
        cls.create_or_update()
        col_pro = cls.get_columns_db_tecno('TblProducto')
        Category = Pool().get('product.category')

        
        #Se procede a importar productos
        if productos_tecno:
            #Creación de los productos con su respectiva categoria e información
            Producto = Pool().get('product.product')
            Template_Product = Pool().get('product.template')
            #to_category = []
            to_product = []
            to_template = []
            for producto in productos_tecno:
                id_producto = str(producto[col_pro.index('IdProducto')])
                existe = cls.buscar_producto(id_producto)
                id_categoria = producto[col_pro.index('contable')]
                categoria_contable = Category.search([('id_tecno', '=', id_categoria)])
                if categoria_contable:
                    categoria_contable = categoria_contable[0]
                else:
                    #category = {
                    #    'id_tecno': id_categoria,
                    #    'name': str(id_categoria)+' - sin modelo',
                    #    'accounting': True
                    #}
                    categoria = Category()
                    categoria.id_tecno = id_categoria
                    categoria.name = str(id_categoria)+' - sin modelo'
                    categoria.accounting = True
                    categoria.save()
                    #to_category.append(categoria)
                    categoria_contable = categoria
                nombre_producto = producto[col_pro.index('Producto')].strip()
                tipo_producto = cls.tipo_producto(producto[col_pro.index('maneja_inventario')])
                udm_producto = cls.udm_producto(producto[col_pro.index('unidad_Inventario')])
                vendible = cls.vendible_producto(producto[col_pro.index('TipoProducto')])
                valor_unitario = producto[col_pro.index('valor_unitario')]
                #En caso de existir el producto se procede a verificar su ultimo cambio y a modificar
                if existe:
                    ultimo_cambio = producto[col_pro.index('Ultimo_Cambio_Registro')]
                    create_date = None
                    write_date = None
                    #LA HORA DEL SISTEMA DE TRYTON TIENE UNA DIFERENCIA HORARIA DE 5 HORAS CON LA DE TECNO
                    if existe.write_date:
                        write_date = (existe.write_date - datetime.timedelta(hours=5, minutes=5))
                    elif existe.create_date:
                        create_date = (existe.create_date - datetime.timedelta(hours=5, minutes=5))
                    #print(ultimo_cambio, create_date, write_date)
                    #if (True):
                    if (ultimo_cambio and write_date and ultimo_cambio > write_date) or (ultimo_cambio and not write_date and ultimo_cambio > create_date):
                        existe.template.name = nombre_producto
                        existe.template.type = tipo_producto
                        existe.template.default_uom = udm_producto
                        existe.template.purchase_uom = udm_producto
                        existe.template.salable = vendible
                        if vendible:
                            existe.template.sale_uom = udm_producto
                        existe.template.list_price = valor_unitario
                        existe.template.account_category = categoria_contable.id
                        existe.template.sale_price_w_tax = 0
                        existe.template.save()
                else:
                    prod = Producto()
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
                    temp.account_category = categoria_contable.id
                    temp.sale_price_w_tax = 0
                    prod.id_tecno = id_producto
                    prod.template = temp
                    #temp.save()
                    #prod.save()
                    to_template.append(temp)
                    to_product.append(prod)
            #Category.save(to_category)
            Template_Product.save(to_template)
            Producto.save(to_product)
        logging.warning('FINISH PRODUCTOS')


    @classmethod
    def update_accounting_categories(cls):
        modelos = cls.get_modelos_tecno()
        if not modelos:
            logging.error('Revisar vista modelo contable, No se encontraron valores')
            #raise UserError("Revisar vista modelo contable", "No se encontraron valores")
        #Creación o actualización de las categorias de los productos
        Category = Pool().get('product.category')
        to_category = []
        for modelo in modelos:
            id_tecno = modelo.IDMODELOS
            nombre = str(id_tecno)+' - '+modelo.MODELOS.strip()
            
            existe = cls.buscar_categoria(id_tecno)
            if not existe:
                categoria = {
                    'id_tecno': id_tecno,
                    'name': nombre,
                    'accounting': True
                }
                #categoria = Category()
                #categoria.id_tecno = id_tecno
                #categoria.name = nombre
                #categoria.accounting = True
                #categoria.save()
                categoria = cls.set_account(modelo, categoria)
                to_category.append(categoria)
                
        Category.create(to_category)

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
    
    #Función encargada de asignar las cuentas contables a las categorias de los productos
    @classmethod
    def set_account(cls, modelo, category):
        Account = Pool().get('account.account')

        #Gastos
        l_expense = list(modelo.CUENTA1)
        if int(l_expense[0]) >= 5:
            expense = Account.search([('code', '=', modelo.CUENTA1)])
            if expense:
                category['account_expense'] = expense[0]
        
        #Ingresos
        l_revenue = list(modelo.CUENTA3)
        if l_revenue[0] == '4':
            revenue = Account.search([('code', '=', modelo.CUENTA3)])
            if revenue:
                category['account_revenue'] = revenue[0]
        
        #Devolucion venta
        l_return_sale = list(modelo.CUENTA4)
        if int(l_return_sale[0]) >= 4:
            return_sale = Account.search([('code', '=', modelo.CUENTA4)])
            if return_sale:
                category['account_return_sale'] = return_sale[0]
        
        return category

    #Esta función se encarga de traer todos la vista modelos de la bd TecnoCarnes
    @classmethod
    def get_modelos_tecno(cls):
        Config = Pool().get('conector.configuration')
        consult = "SELECT * FROM dbo.vistamodelos"
        data = Config.get_data(consult)
        return data

    #Función encargada de consultar si existe un producto dado de la bd TecnoCarnes
    @classmethod
    def buscar_producto(cls, id_producto):
        Product = Pool().get('product.product')
        producto = Product.search(['OR', ('id_tecno', '=', id_producto), ('code', '=', id_producto)])
        if producto:
            return producto[0]
        else:
            return False

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
                query = cursor.execute("SET DATEFORMAT ymd SELECT * FROM dbo."+table+" WHERE fecha_creacion >= CAST('"+date+"' AS datetime) OR Ultimo_Cambio_Registro >= CAST('"+date+"' AS datetime)")
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
        fecha = fecha.strftime('%Y-%m-%d %H:%M:%S')
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

#Herencia del party.contact_mechanism e insercción del campo id_tecno
class ProductCategory(ModelSQL, ModelView):
    'ProductCategory'
    __name__ = 'product.category'
    id_tecno = fields.Char('Id TecnoCarnes', required=False)