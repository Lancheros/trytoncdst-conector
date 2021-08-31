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
        print('TEST CONEXION !')

    @classmethod
    def setter_server(cls, instances, name, value):
        pass
