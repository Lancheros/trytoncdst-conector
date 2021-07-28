
from conexion import conexion
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
import datetime
from trytond.transaction import Transaction

__all__ = [
    'Terceros',
    ]

class Terceros(ModelSQL, ModelView):
    'Terceros'
    __name__ = 'conector.terceros'

    actualizacion = fields.Char('Actualizacion', required=True)
    fecha = fields.DateTime('Fecha y hora', format="%H:%M:%S", required=True)


    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
                'cargar_datos': {},
                })

    """
    @classmethod
    def validate(cls, books):
        for book in books:
            if not book.isbn:
                continue
            try:
                if int(book.isbn) < 0:
                    raise ValueError
            except ValueError:
                cls.raise_user_error('invalid_isbn')
    """

    @classmethod
    def default_fecha(cls):
        return datetime.datetime.now()


    @classmethod
    @ModelView.button
    def cargar_datos(cls, fecha = None):
        #cls.carga_terceros()
        cls.carga_productos()
        return None


    @classmethod
    def carga_terceros(cls):
        terceros_tecno = cls.get_data_db_tecno('TblTerceros')
        columnas_terceros = cls.get_columns_db_tecno('TblTerceros')
        columnas_contactos = cls.get_columns_db_tecno('Terceros_Contactos')
        columna_direcciones = cls.get_columns_db_tecno('Terceros_Dir')
        
        pool = Pool()
        Party = pool.get('party.party')
        Address = pool.get('party.address')
        Lang = pool.get('ir.lang')
        es, = Lang.search([('code', '=', 'es_419')])
        Mcontact = pool.get('party.contact_mechanism')
        to_create = []

        for ter in terceros_tecno:
            exists = cls.find_party(ter[columnas_terceros.index('nit_cedula')].strip())
            if exists:
                exists.create_date = ter[columnas_terceros.index('fecha_creacion')]
                exists.type_document = cls.id_type(ter[columnas_terceros.index('tipo_identificacion')])
                exists.id_number = ter[columnas_terceros.index('nit_cedula')].strip()
                exists.name = ter[columnas_terceros.index('nombre')].strip()
                exists.first_name = ter[columnas_terceros.index('PrimerNombre')].strip()
                exists.second_name = ter[columnas_terceros.index('SegundoNombre')].strip()
                exists.first_family_name = ter[columnas_terceros.index('PrimerApellido')].strip()
                exists.second_family_name = ter[columnas_terceros.index('SegundoApellido')].strip()
                exists.write_date = ter[columnas_terceros.index('Ultimo_Cambio_Registro')]
                exists.type_person = cls.person_type(ter[columnas_terceros.index('TipoPersona')].strip())
                if exists.type_person == 'persona_juridica':
                    exists.declarante = True
                #Verificación e inserción codigo ciiu
                if ter[columnas_terceros.index('IdActividadEconomica')].strip() != 0:
                    exists.ciiu_code = ter[columnas_terceros.index('IdActividadEconomica')].strip()
                exists.regime_tax = cls.tax_regime(int(ter[columnas_terceros.index('IdTipoContribuyente')]))
                exists.lang = es
                cant_dir = 0

                #Actualización de la dirección y metodos de contacto
                cls.update_address(exists)
                cls.update_contact(exists)
                #---Revisar------
                exists.save()
            else:
                #Creando tercero junto con sus direcciones y metodos de contactos
                tercero = Party()
                tercero.create_date = ter[columnas_terceros.index('fecha_creacion')]
                tercero.type_document = cls.id_type(ter[columnas_terceros.index('tipo_identificacion')])
                tercero.id_number = ter[columnas_terceros.index('nit_cedula')].strip()
                tercero.name = ter[columnas_terceros.index('nombre')].strip()
                tercero.first_name = ter[columnas_terceros.index('PrimerNombre')].strip()
                tercero.second_name = ter[columnas_terceros.index('SegundoNombre')].strip()
                tercero.first_family_name = ter[columnas_terceros.index('PrimerApellido')].strip()
                tercero.second_family_name = ter[columnas_terceros.index('SegundoApellido')].strip()
                tercero.write_date = ter[columnas_terceros.index('Ultimo_Cambio_Registro')]
                #Equivalencia tipo de persona y asignación True en declarante
                tercero.type_person = cls.person_type(ter[columnas_terceros.index('TipoPersona')].strip())
                if tercero.type_person == 'persona_juridica':
                    tercero.declarante = True
                #Verificación e inserción codigo ciiu
                if ter[columnas_terceros.index('IdActividadEconomica')] != 0:
                    tercero.ciiu_code = ter[columnas_terceros.index('IdActividadEconomica')].strip()
                #Equivalencia regimen de impuestos
                tercero.regime_tax = cls.tax_regime(int(ter[columnas_terceros.index('IdTipoContribuyente')]))
                tercero.lang = es
                direcciones_tecno = cls.get_address_db_tecno(tercero.id_number)
                cant_dir = 0
                if direcciones_tecno:
                    for direc in direcciones_tecno:
                        if cant_dir == 0:
                            tercero.commercial_name = direc[columna_direcciones.index('NombreSucursal')].strip()
                            cant_dir += 1
                        #Creacion e inserccion de direccion
                        direccion = Address()
                        direccion.city = direc[columna_direcciones.index('ciudad')].strip()
                        direccion.country = 50
                        direccion.name = direc[columna_direcciones.index('Barrio')].strip()
                        direccion.party = tercero
                        direccion.party_name = tercero.name
                        direccion.street = direc[columna_direcciones.index('direccion')].strip()
                        direccion.save()
                contactos_tecno = cls.get_contacts_db_tecno(tercero.id_number)
                if contactos_tecno:
                    for cont in contactos_tecno:
                        #Creacion e inserccion de metodo de contacto phone
                        contacto = Mcontact()
                        contacto.type = 'phone'
                        contacto.value = cont[columnas_contactos.index('Telefono')].strip()
                        contacto.name = cont[columnas_contactos.index('Nombre')].strip()+' ('+cont[columnas_contactos.index('Cargo')].strip()+')'
                        contacto.party = tercero
                        contacto.save()
                        #Creacion e inserccion de metodo de contacto email
                        contacto = Mcontact()
                        contacto.type = 'email'
                        contacto.value = cont[columnas_contactos.index('Email')].strip()
                        contacto.name = cont[columnas_contactos.index('Nombre')].strip()+' ('+cont[columnas_contactos.index('Cargo')].strip()+')'
                        contacto.party = tercero
                        contacto.save()
                to_create.append(tercero)
        Party.save(to_create)


    @classmethod
    def carga_productos(cls):
        productos_tecno = cls.get_data_db_tecno('TblProducto')
        col_pro = cls.get_columns_db_tecno('TblProducto')
        col_gproducto = cls.get_columns_db_tecno('TblGrupoProducto')
        grupos_producto = cls.get_data_db_tecno('TblGrupoProducto')

        Category = Pool().get('product.category')
        to_categorias = []
        for categoria in grupos_producto:
            existe = cls.buscar_categoria(str(categoria[col_gproducto.index('IdGrupoProducto')])+'-'+categoria[col_gproducto.index('GrupoProducto')])
            if not existe:
                categoria_prod = Category()
                categoria_prod.name = str(categoria[col_gproducto.index('IdGrupoProducto')])+'-'+categoria[col_gproducto.index('GrupoProducto')]
                to_categorias.append(categoria_prod)
        Category.save(to_categorias)

        Producto = Pool().get('product.product')
        Template_Product = Pool().get('product.template')
        to_producto = []
        for producto in productos_tecno:
            existe = cls.buscar_producto(producto[col_pro.index('IdProducto')])
            if existe:
                name_categoria = None
                for categoria in grupos_producto:
                    if categoria[col_gproducto.index('IdGrupoProducto')] == producto[col_pro.index('IdGrupoProducto')]:
                        name_categoria = str(categoria[col_gproducto.index('IdGrupoProducto')])+'-'+categoria[col_gproducto.index('GrupoProducto')]
                categoria_producto, = Category.search([('name', '=', name_categoria)])
                existe.template.name = producto[col_pro.index('Producto')].strip()
                existe.template.type = cls.tipo_producto(producto[col_pro.index('maneja_inventario')].strip())
                #equivalencia de unidad de medida
                if producto[col_pro.index('unidad_Inventario')] == 1:
                    existe.template.default_uom = 2
                else:
                    existe.template.default_uom = 1
                existe.template.list_price = int(producto[col_pro.index('costo_unitario')])
                existe.template.categories = [categoria_producto]
                existe.template.save()
            else:
                prod = Producto()
                name_categoria = None
                for categoria in grupos_producto:
                    if categoria[col_gproducto.index('IdGrupoProducto')] == producto[col_pro.index('IdGrupoProducto')]:
                        name_categoria = str(categoria[col_gproducto.index('IdGrupoProducto')])+'-'+categoria[col_gproducto.index('GrupoProducto')]
                categoria_producto, = Category.search([('name', '=', name_categoria)])
                temp = Template_Product()
                temp.code = producto[col_pro.index('IdProducto')]
                temp.name = producto[col_pro.index('Producto')].strip()
                temp.type = cls.tipo_producto(producto[col_pro.index('maneja_inventario')].strip())
                #equivalencia de unidad de medida
                if producto[col_pro.index('unidad_Inventario')] == 1:
                    temp.default_uom = 2
                else:
                    temp.default_uom = 1
                temp.list_price = int(producto[col_pro.index('costo_unitario')])
                temp.categories = [categoria_producto]
                prod.template = temp
                to_producto.append(prod)
        Producto.save(to_producto)
        

    @classmethod
    def buscar_categoria(cls, id_categoria):
        Category = Pool().get('product.category')
        try:
            categoria_producto, = Category.search([('name', '=', id_categoria)])
        except ValueError:
            return False
        else:
            return True

    @classmethod
    def buscar_producto(cls, id_producto):
        Product = Pool().get('product.product')
        try:
            producto, = Product.search([('code', '=', id_producto)])
        except ValueError:
            return False
        else:
            return producto

    @classmethod
    def tipo_producto(cls, inventario):
        #equivalencia del tipo de producto (si maneja inventario o no)
        if inventario == 'N':
            return 'service'
        else:
            return 'goods'

    @classmethod
    def find_party(cls, id):
        Party = Pool().get('party.party')
        try:
            party, = Party.search([('id_number', '=', id)])
        except ValueError:
            return False
        else:
            return party


    @classmethod
    def id_type(cls, type):
        #Equivalencia tipo de identificacion
        if type == '1':
            return '13'
        elif type == '2':
            return '22'
        elif type == '3':
            return '31'
        elif type == '4':
            return '41'
        elif type == '6':
            return '12'
        else:
            return None


    @classmethod
    def person_type(cls, type):
        #Equivalencia tipo de persona y asignación True en declarante
        if type == 'Natural':
            return 'persona_natural'
        elif type == 'Juridica':
            return 'persona_juridica'

    @classmethod
    def tax_regime(cls, regime):
        #Equivalencia regimen de impuestos
        if regime == 1 or regime == 4:
            return 'gran_contribuyente'
        elif regime == 2 or regime == 5 or regime == 6 or regime == 7 or regime == 8:
            return 'regimen_responsable'
        elif regime == 3 or regime == 0:
            return'regimen_no_responsable'
        else:
            return None


    @classmethod
    def find_address(cls, party):
        Address = Pool().get('party.address')
        address = Address.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*address.select(where=(address.party == party.id)))
        result = cursor.fetchall()
        return result


    @classmethod
    def find_contact_mechanism(cls, party):
        Contact = Pool().get('party.contact_mechanism')
        contact = Contact.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*contact.select(where=(contact.party == party.id)))
        result = cursor.fetchall()
        return result

    @classmethod
    def get_columns_db_tecno(cls, table):
        columns = []
        try:
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = "+table+" ORDER BY ORDINAL_POSITION")
                for q in query.fetchall():
                    columns.append(q[0])
        except Exception as e:
            print("ERROR QUERY "+table+": ", e)
        return columns


    @classmethod
    def get_data_db_tecno(cls, table):
        data = []
        try:
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo."+table)
                data = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY "+table+": ", e)
        return data


    @classmethod
    def get_address_db_tecno(cls, nit):
        address = []
        try:
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo.Terceros_Dir WHERE nit = "+nit)
                address = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY ADDRESS: ", e)
        return address


    @classmethod
    def get_contacts_db_tecno(cls, nit):
        contacts = []
        try:
            with conexion.cursor() as cursor:
                query = cursor.execute("SELECT * FROM dbo.Terceros_Contactos WHERE Nit_Cedula = "+nit)
                contacts = list(query.fetchall())
        except Exception as e:
            print("ERROR QUERY CONTACTS: ", e)
        return contacts


    @classmethod
    def update_address(cls, party):
        address_tecno = cls.get_address_db_tecno(party.id)
        #Consultamos si existen direcciones para el tercero
        if address_tecno:
            columna_direcciones = cls.get_columns_db_tecno('Terceros_Dir')
            Address = Pool().get('party.address')
            address_party = cls.find_address(party)
            cant = 0
            if address_party:
                #Luego de consultar si existen direcciones en tryton, comenzamos a actualizarlas con la db TecnoCarnes
                if len(address_tecno) >= len(address_party):
                    for upd in address_party:
                        if cant == 0:
                            party.commercial_name = address_tecno[cant][columna_direcciones.index('NombreSucursal')].strip()
                        address = Address.search([('id', '=', upd[0])])
                        address.city = address_tecno[cant][columna_direcciones.index('ciudad')].strip()
                        address.name = address_tecno[cant][columna_direcciones.index('Barrio')].strip()
                        address.street = address_tecno[cant][columna_direcciones.index('direccion')].strip()
                        address.save()
                        cant+=1
                    #Verificamos si faltan direcciones por crear y las creamos
                    if (len(address_tecno) - len(address_party)) > 0:
                        while cant < len(address_tecno):
                            address = Address()
                            address.city = address_tecno[cant][columna_direcciones.index('ciudad')].strip()
                            address.country = 50
                            address.name = address_tecno[cant][columna_direcciones.index('Barrio')].strip()
                            address.party = party
                            address.party_name = party.name
                            address.street = address_tecno[cant][columna_direcciones.index('direccion')].strip()
                            address.save()
                            cant+=1
                else:
                    for upd in range(len(address_tecno)):
                        if cant == 0:
                            party.commercial_name = address_tecno[cant][columna_direcciones.index('NombreSucursal')].strip()
                            cant+=1
                        address = Address.search([('id', '=', address_party[upd][0])])
                        address.city = address_tecno[cant][columna_direcciones.index('ciudad')].strip()
                        address.name = address_tecno[cant][columna_direcciones.index('Barrio')].strip()
                        address.street = address_tecno[cant][columna_direcciones.index('direccion')].strip()
                        address.save()
            else:
                #En caso de no existir direcciones en tryton, las creamos
                for add in address_tecno:
                    if cant == 0:
                        party.commercial_name = address_tecno[cant][columna_direcciones.index('NombreSucursal')].strip()
                        cant+=1
                    address = Address()
                    address.city = add[columna_direcciones.index('ciudad')].strip()
                    address.country = 50
                    address.name = add[columna_direcciones.index('Barrio')].strip()
                    address.party = party
                    address.party_name = party.name
                    address.street = add[columna_direcciones.index('direccion')].strip()
                    address.save()


    @classmethod
    def update_contact(cls, party):
        contacts_tecno = cls.get_contacts_db_tecno(party.id)
        #Consultamos si existen contactos para el tercero
        if contacts_tecno:
            columns_contact = cls.get_columns_db_tecno('Terceros_Contactos')
            Contacts = Pool().get('party.contact_mechanism')
            contact_party = cls.find_contact_mechanism(party)
            cant = 0
            if contact_party:
                #Luego de consultar si existen contactos en tryton, comenzamos a actualizarlas con la db TecnoCarnes
                if len(contacts_tecno)*2 >= len(contact_party):
                    for upd in contact_party:
                        contact = Contacts.search([('id', '=', upd[0])])
                        if contact.type == 'phone':
                            contact.value = contacts_tecno[cant][columns_contact.index('Telefono')].strip()
                            contact.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contact.save()
                        elif contact.type == 'email':
                            contact.value = contacts_tecno[cant][columns_contact.index('Email')].strip()
                            contact.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contact.save()
                            cant+=1
                    #Verificamos si faltan contactos por crear y las creamos
                    if (len(contacts_tecno)*2 - len(contact_party)) > 0:
                        while cant < len(contacts_tecno):
                            contacto = Contacts()
                            #Creacion e inserccion de metodo de contacto phone
                            contacto = Contacts()
                            contacto.type = 'phone'
                            contacto.value = contacts_tecno[cant][columns_contact.index('Telefono')].strip()
                            contacto.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contacto.party = party
                            contacto.save()
                            #Creacion e inserccion de metodo de contacto email
                            contacto = Contacts()
                            contacto.type = 'email'
                            contacto.value = contacts_tecno[cant][columns_contact.index('Email')].strip()
                            contacto.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contacto.party = party
                            contacto.save()
                            cant+=1
                else:
                    for upd in range(len(contacts_tecno)*2):
                        contacto = Contacts.search([('id', '=', contact_party[upd][0])])
                        if contacto.type == 'phone':
                            contacto.value = contacts_tecno[cant][columns_contact.index('Telefono')].strip()
                            contacto.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contacto.save()
                        elif contacto.type == 'email':
                            contacto.value = contacts_tecno[cant][columns_contact.index('Email')].strip()
                            contacto.name = contacts_tecno[cant][columns_contact.index('Nombre')].strip()+' ('+contacts_tecno[cant][columns_contact.index('Cargo')].strip()+')'
                            contacto.save()
                            cant+=1
            else:
                #En caso de no existir direcciones en tryton, las creamos
                for add in contacts_tecno:
                    #Creacion e inserccion de metodo de contacto phone
                    contacto = Contacts()
                    contacto.type = 'phone'
                    contacto.value = add[columns_contact.index('Telefono')].strip()
                    contacto.name = add[columns_contact.index('Nombre')].strip()+' ('+add[columns_contact.index('Cargo')].strip()+')'
                    contacto.party = party
                    contacto.save()
                    #Creacion e inserccion de metodo de contacto email
                    contacto = Contacts()
                    contacto.type = 'email'
                    contacto.value = add[columns_contact.index('Email')].strip()
                    contacto.name = add[columns_contact.index('Nombre')].strip()+' ('+add[columns_contact.index('Cargo')].strip()+')'
                    contacto.party = party
                    contacto.save()


    @classmethod
    def find_or_create_using_magento_data(cls, order_data):
        """
        Find or Create sale using magento data
        :param order_data: Order Data from magento
        :return: Active record of record created/found
        """
        sale = cls.find_using_magento_data(order_data)

        if not sale:
            sale = cls.create_using_magento_data(order_data)

        return sale

    @classmethod
    def find_using_magento_data(cls, order_data):
        """
        Finds sale using magento data and returns that sale if found, else None
        :param order_data: Order Data from magento
        :return: Active record of record found
        """
        # Each sale has to be unique in an channel of magento
        sales = cls.search([
            ('magento_id', '=', int(order_data['order_id'])),
            ('channel', '=',
                Transaction().context['current_channel']),
        ])

        return sales and sales[0] or None

    @classmethod
    def create_using_magento_data(cls, order_data):
        """
        Create a sale from magento data. If you wish to override the creation
        process, it is recommended to subclass and manipulate the returned
        unsaved active record from the `get_sale_using_magento_data` method.
        :param order_data: Order data from magento
        :return: Active record of record created
        """
        ChannelException = Pool().get('channel.exception')

        Channel = Pool().get('sale.channel')

        channel = Channel.get_current_magento_channel()

        state_data = channel.get_tryton_action(order_data['state'])

        # Do not import if order is in cancelled or draft state
        if state_data['action'] == 'do_not_import':
            return

        sale = cls.get_sale_using_magento_data(order_data)
        sale.save()

        sale.lines = list(sale.lines)
        sale.add_lines_using_magento_data(order_data)
        sale.save()

        # Process sale now
        tryton_action = channel.get_tryton_action(order_data['state'])
        try:
            sale.process_sale_using_magento_state(order_data['state'])
        except UserError, e:
            # Expecting UserError will only come when sale order has
            # channel exception.
            # Just ignore the error and leave this order in draft state
            # and let the user fix this manually.
            ChannelException.create([{
                'origin': '%s,%s' % (sale.__name__, sale.id),
                'log': "Error occurred on transitioning to state %s.\nError "
                    "Message: %s" % (tryton_action['action'], e.message),
                'channel': sale.channel.id,
            }])

        return sale