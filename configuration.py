from trytond.model import ModelSQL, ModelView, fields
import pyodbc
from trytond.exceptions import UserError, UserWarning


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
        for record in records:
            try:
                conexion = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+str(record.server)+';DATABASE='+str(record.db)+';UID='+str(record.user)+';PWD='+str(record.password))
                print("Conexion sqlserver exitosa !")
                raise UserWarning("Conexion sqlserver exitosa !")
            except Exception as e:
                raise UserError("Ocurrio un error al conectar SQL Server: ", e)


