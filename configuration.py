from trytond.model import ModelSQL, ModelView, fields
import pyodbc

__all__ = [
    'Configuration',
    ]

class Configuration(ModelSQL, ModelView):
    'Configuration'
    __name__ = 'conector.configuration'

    server = fields.Char('Server', required=True)
    db = fields.Char('Database', required=True)
    user = fields.Char('User', required=True)
    password = fields.Char('Password', required=True)

    @classmethod 
    def __setup__(cls):
        super(Configuration, cls).__setup__()
        cls._buttons.update({
                'test_conexion': {},
                })

    #Función que se activa al pulsar el botón test_conexion
    @classmethod
    @ModelView.button
    def test_conexion(cls, records):
        print('TEST CONEXION:')
        try:
            conexion = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+cls.server+';DATABASE='+cls.db+';UID='+cls.user+';PWD='+cls.password)
            print("Conexion sqlserver exitosa !")
        except Exception as e:
            print("Ocurrio un error al conectar SQL Server: ", e)


