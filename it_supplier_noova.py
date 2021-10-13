#!/usr/bin/python
#! -*- coding: utf8 -*-
import json
from builder_phase import ElectronicPayroll
#import xmltodict
import requests
import base64

class ElectronicPayrollCdst(object):

    def __init__(self, payroll, config):
        self.payroll = payroll
        self.config = config
        #self.dic_payroll = None
        self._create_electronic_payroll_phase()

    def _create_electronic_payroll_phase(self):

        ec_payroll = ElectronicPayroll(self.payroll, self.config)
        _type = 'nie' #Nomina individual
        if self.payroll.payroll_type != '102':
            _type = 'niae' #Nomina individual ajuste
        
        #prefix = self.config.payroll_electronic_sequence.prefix
        #seq = self.payroll.number.split(prefix, maxsplit=1)
        #file_name = _type + \
        #    self.payroll.company.party.id_number.zfill(
        #        10) + hex(int(seq[1])).zfill(8) + '.xml'
        if ec_payroll.status != 'ok':
            self.payroll.get_message(ec_payroll.status)
        xml_payroll = ec_payroll.make(self.payroll.payroll_type)
        #self.payroll.xml_payroll = xml_payroll
        #self.payroll.file_name_xml = file_name
        #self.payroll.save()
        #data = self._create_json_noova(xml_payroll)
        self._send_noova(xml_payroll)


    # Consumo API noova
    def _send_noova(self, dict):
        if self.payroll.company.url_supplier and self.payroll.company.auth_supplier and self.payroll.company.host_supplier and self.payroll.company.supplier_code:
            url = self.payroll.company.url_supplier
            auth = self.payroll.company.auth_supplier
            host = self.payroll.company.host_supplier
            sucode = self.payroll.company.supplier_code
        else:
            self.payroll.get_message('Missing fields in company | supplier it')
        auth = auth.encode('utf-8')
        auth = base64.b64encode(auth)
        auth = auth.decode('utf-8')
        header = {
            'Authorization': 'Basic '+auth,
            'Content-Type': 'application/json',
            'Host': host,
            'Content-Length': '967',
            'Expect': '100-continue',
            'Connection': 'Keep-Alive'
        }
        data = self._create_json_noova(dict, sucode)
        response = requests.post(url, headers=header, data=data)
        #self.payroll.get_message(response.text)
        if response.status_code == 200:
            #res = response.json()
            #xml_signed = encode_payroll(res['xml_base64_bytes'], 'decode')
            #self.payroll.xml_payroll = xml_signed.encode('utf8')
            self.payroll.electronic_state = 'submitted'
            self.payroll.electronic_message = response.text
            self.payroll.save()
            # return response
            print("CONEXION EXITOSA")
        else:
            self.payroll.get_message(response.text)


    def _create_json_noova(self, dict, sucode):
        dict_res = dict
        noova = {
            "Nvsuc_codi": sucode, # Código de la sucursal configurada en Noova
            "Nvnom_pref": dict_res["NumeroSecuenciaXML"]["Prefijo"], #
            "Nvnom_cons": dict_res["NumeroSecuenciaXML"]["Consecutivo"], #
            "Nvnom_nume": dict_res["NumeroSecuenciaXML"]["Numero"], #
            "Nvope_tipo": "NM", #Tipo de operación nómina (siempre debe ir "NM")
            #"Nvnom_redo": "", #Se utiliza para cuando se utilice el redondeo en el Documento
            "Nvnom_devt": dict_res["DevengadosTotal"],
            "Nvnom_dedt": dict_res["DeduccionesTotal"],
            "Nvnom_comt": dict_res["ComprobanteTotal"],
            "Nvnom_fpag": dict_res["FechasPagos"]["FechaPago"][0],
            #"Nvnom_cnov": "", #Duda
            "Periodo": { #
                "Nvper_fing": dict_res["Periodo"]["FechaIngreso"],
                #"Nvper_fret": "2020-12-31", #fecha retiro nomina
                "Nvper_fpin": dict_res["Periodo"]["FechaLiquidacionInicio"],
                "Nvper_fpfi": dict_res["Periodo"]["FechaLiquidacionFin"],
                "Nvper_tlab": dict_res["Periodo"]["TiempoLaborado"]
            },
            "InformacionGeneral": { #
                "Nvinf_tnom": dict_res["InformacionGeneral"]["TipoXML"],
                "Nvinf_pnom": dict_res["InformacionGeneral"]["PeriodoNomina"],
                "Nvinf_tmon": dict_res["InformacionGeneral"]["TipoMoneda"],
                #"Nvinf_mtrm": dict_res["InformacionGeneral"]["@TRM"] #Tasa Representativa del mercado
            },
            #"LNotas": [
            #    ""
            #],
            "Empleador": {#
                "Nvemp_nomb": dict_res["Empleador"]["RazonSocial"],
                #"Nvemp_pape": dict_res["Empleador"]["@PrimerApellido"],#opcional
                #"Nvemp_sape": dict_res["Empleador"]["@SegundoApellido"],#opcional
                #"Nvemp_pnom": dict_res["Empleador"]["@PrimerNombre"],#opcional
                #"Nvemp_onom": dict_res["Empleador"]["@OtrosNombres"],#opcional
                "Nvemp_nnit": dict_res["Empleador"]["NIT"],
                "Nvemp_endv": dict_res["Empleador"]["DV"],
                "Nvemp_pais": dict_res["Empleador"]["Pais"],
                "Nvemp_depa": dict_res["Empleador"]["DepartamentoEstado"],
                "Nvemp_ciud": dict_res["Empleador"]["MunicipioCiudad"],
                "Nvemp_dire": dict_res["Empleador"]["Direccion"]
            },
            "Trabajador": {#
                "Nvtra_tipo": dict_res["Trabajador"]["TipoTrabajador"],
                "Nvtra_stip": dict_res["Trabajador"]["SubTipoTrabajador"],
                "Nvtra_arpe": dict_res["Trabajador"]["AltoRiesgoPension"],
                "Nvtra_dtip": dict_res["Trabajador"]["TipoDocumento"],
                "Nvtra_ndoc": dict_res["Trabajador"]["NumeroDocumento"],
                "Nvtra_pape": dict_res["Trabajador"]["PrimerApellido"],
                "Nvtra_sape": dict_res["Trabajador"]["SegundoApellido"],
                "Nvtra_pnom": dict_res["Trabajador"]["PrimerNombre"],
                #"Nvtra_onom": dict_res["Trabajador"]["OtrosNombres"],
                "Nvtra_ltpa": dict_res["Trabajador"]["LugarTrabajoPais"],
                "Nvtra_ltde": dict_res["Trabajador"]["LugarTrabajoDepartamentoEstado"],
                "Nvtra_ltci": dict_res["Trabajador"]["LugarTrabajoMunicipioCiudad"],
                "Nvtra_ltdi": dict_res["Trabajador"]["LugarTrabajoDireccion"],
                "Nvtra_sint": dict_res["Trabajador"]["SalarioIntegral"],
                "Nvtra_tcon": dict_res["Trabajador"]["TipoContrato"],
                "Nvtra_suel": dict_res["Trabajador"]["Sueldo"],
                "Nvtra_codt": dict_res["Trabajador"]["CodigoTrabajador"]
            },
            "Pago": {#
                "Nvpag_form": dict_res["Pago"]["Forma"],
                "Nvpag_meto": dict_res["Pago"]["Metodo"],
                #"Nvpag_banc": dict_res["Pago"]["Banco"], #Validar
                #"Nvpag_tcue": dict_res["Pago"]["TipoCuenta"],
                #"Nvpag_ncue": dict_res["Pago"]["NumeroCuenta"]
            },
            "Devengados": {
                "Basico": {#
                    "Nvbas_dtra": dict_res["Devengados"]["Basico"]["DiasTrabajados"],
                    "Nvbas_stra": dict_res["Devengados"]["Basico"]["SueldoTrabajado"]
                },
                #"LHorasExtras": [
                #    {
                #        "Nvcom_fini": "2020-12-01T19:00:00",
                #        "Nvcom_ffin": "2020-12-01T21:00:00",
                #        "Nvcom_cant": "2",
                #        "Nvcom_pago": "180000.00",
                #        "Nvhor_tipo": "HEN",
                #        "Nvhor_porc": "75.00"
                #    }
                #],
                #"LVacaciones": [
                #    {
                #        "Nvcom_fini": "2020-12-05",
                #        "Nvcom_ffin": "2020-12-07",
                #        "Nvcom_cant": "2",
                #        "Nvcom_pago": "200000.00",
                #        "Nvvac_tipo": "1"
                #    }
                #],
                #"Primas": {
                #    "Nvpri_cant": "30",
                #    "Nvpri_pago": "75000.00",
                #    "Nvpri_pagn": "10000.00"
                #},
                #"Cesantias": {
                #    "Nvces_pago": "35000.00",
                #    "Nvces_porc": "2.00",
                #    "Nvces_pagi": "6000.00"
                #},
                #"LIncapacidades": [
                #    {
                #        "Nvcom_fini": "2020-12-10",
                #        "Nvcom_ffin": "2020-12-12",
                #        "Nvcom_cant": "2",
                #        "Nvcom_pago": "180000.00",
                #        "Nvinc_tipo": "2"
                #    }
                #],
                #"LLicencias": [
                #    {
                #        "Nvcom_fini": "2020-12-01",
                #        "Nvcom_ffin": "2020-12-05",
                #        "Nvcom_cant": "4",
                #        "Nvcom_pago": "360000.00",
                #        "Nvlic_tipo": "1"
                #    }
                #],
                #"LHuelgasLegales": [
                #    {
                #        "Nvcom_fini": "2020-12-05",
                #        "Nvcom_ffin": "2020-12-06",
                #        "Nvcom_cant": "1",
                #        "Nvcom_pago": "90000.00"
                #    }
                #],
                #"LAnticipos": [
                #    "20500.00",
                #    "12300.00",
                #],
            },#
            "Deducciones": {
                "Salud": {#
                    "Nvsal_porc": dict_res["Deducciones"]["Salud"]["Porcentaje"],
                    "Nvsal_dedu": dict_res["Deducciones"]["Salud"]["Deduccion"]
                },
                #"FondoPension": {#
                #    "Nvfon_porc": "4.00",
                #    "Nvfon_dedu": "40000.00"
                #},
                #"FondoSP": {
                #    "Nvfsp_porc": "1.00",
                #    "Nvfsp_dedu": "25500.00",
                #    "Nvfsp_posb": "1.00",
                #    "Nvfsp_desb": "10000.00"
                #},
                #"LSindicatos": [
                #    {
                #        "Nvsin_porc": "4.00",
                #        "Nvsin_dedu": "40000.00"
                #    }
                #],
                #"LPagosTerceros": [
                #    "20500.00",
                #    "12300.00",
                #],
                #"PensionVoluntaria": "33000.00"
            }
        }
        data_val = self._validate_data(dict_res, noova)
        data = json.dumps(data_val, indent=4)
        print(data)
        return data

    def _validate_data(self, dic, noova):
        if "Notas" in dic.keys():
           noova["LNotas"] = [dic["Notas"]]
        
        if self.payroll.employee.party.second_name:
            noova["Trabajador"]["Nvtra_onom"] = dic["Trabajador"]["OtrosNombres"]
        
        if self.payroll.bank_payment:
            noova["Pago"]["Nvpag_banc"] = dic["Pago"]["Banco"]
            noova["Pago"]["Nvpag_tcue"] = dic["Pago"]["TipoCuenta"]
            noova["Pago"]["Nvpag_ncue"] = dic["Pago"]["NumeroCuenta"]
        
        #if "HEDs" in dic["Devengados"].keys():
        #    horas = []
        #    for h in dic["Devengados"]["HEDs"]:
        #        val = {
        #            "Nvcom_fini": h["FechaInicio"],
        #            "Nvcom_ffin": h["FechaFin"],
        #            "Nvcom_cant": h["Cantidad"],
        #            "Nvcom_pago": h["Pago"],
        #            "Nvhor_porc": h["Porcentaje"]
        #        }
        #        horas.append(val)
        #    noova["Devengados"]["LHorasExtras"] = horas

        if "Vacaciones" in dic["Devengados"].keys():
            horas = []
            for h in dic["Devengados"]["Vacaciones"]:
                if "VacacionesComunes" in h.keys():
                    val = {
                        "Nvcom_fini": h["FechaInicio"],
                        "Nvcom_ffin": h["FechaFin"],
                        "Nvcom_cant": h["Cantidad"],
                        "Nvcom_pago": h["Pago"],
                        "Nvvac_tipo": h["1"]
                    }
                else:
                    val = {
                        "Nvcom_cant": h["Cantidad"],
                        "Nvcom_pago": h["Pago"],
                        "Nvvac_tipo": h["2"]
                    }
                horas.append(val)
            noova["Devengados"]["LVacaciones"] = horas

        if "Primas" in dic["Devengados"].keys():
            noova["Devengados"]["Primas"]["Nvpri_cant"] = dic["Devengados"]["Primas"]["Cantidad"]
            noova["Devengados"]["Primas"]["Nvpri_pago"] = dic["Devengados"]["Primas"]["Pago"],
            
            if "PagoNs" in dic["Devengados"]["Primas"]:
                noova["Devengados"]["Primas"]["Nvpri_pagn"] = dic["Devengados"]["PagoNs"]
        
        #if "Cesantias" in dic["Devengados"].keys():
        #    noova["Devengados"]["Cesantias"]["Nvces_pago"]

        if "Incapacidades" in dic["Devengados"].keys():
            horas = []
            for h in dic["Devengados"]["Incapacidades"]:
                val = {
                    "Nvcom_fini": h["FechaInicio"],
                    "Nvcom_ffin": h["FechaFin"],
                    "Nvcom_cant": h["Cantidad"],
                    "Nvcom_pago": h["Pago"],
                    "Nvinc_tipo": h["1"]
                }
                horas.append(val)
            noova["Devengados"]["LIncapacidades"] = horas

        if "Licencias" in dic["Devengados"].keys():
            data = []
            for h in dic["Devengados"]["Licencias"]:
                val = {
                    "Nvcom_fini": dic["Devengados"]["Licencias"][h]["FechaInicio"],
                    "Nvcom_ffin": dic["Devengados"]["Licencias"][h]["FechaFin"],
                    "Nvcom_cant": dic["Devengados"]["Licencias"][h]["Cantidad"],
                    "Nvcom_pago": dic["Devengados"]["Licencias"][h]["Pago"]
                }
                if "LicenciaMP" == h:
                    val["Nvlic_tipo"] = "1"
                elif "LicenciaR" == h:
                    val["Nvlic_tipo"] = "2"
                elif "LicenciaNR" == h:
                    val["Nvlic_tipo"] = "3"
                data.append(val)
            noova["Devengados"]["LLicencias"] = data

        if "OtrosTag" in dic["Devengados"].keys():
            data = []
            for h in dic["Devengados"]["OtrosTag"]:
                data.append(dic["Devengados"]["OtrosTag"][h])
            noova["Devengados"]["LAnticipos"] = data
        
        if "FondoPension" in dic["Deducciones"].keys():
            val = {
                "Nvfon_porc": dic["Deducciones"]["FondoPension"]["Porcentaje"],
                "Nvfon_dedu": dic["Deducciones"]["FondoPension"]["Deduccion"]
            }
            noova["Deducciones"]["FondoPension"] = val

        if "FondoSP" in dic["Deducciones"]:
            pass

        if "Sindicatos" in dic["Deducciones"]:
            pass

        if "OtrosD" in dic["Deducciones"]:
            data = []
            for od in dic["Deducciones"]["OtrosD"]:
                if dic["Deducciones"]["OtrosD"][od] == "PensionVoluntaria":
                    noova["Deducciones"]["PensionVoluntaria"] = dic["Deducciones"]["OtrosD"][od]
                else:
                    data.append(dic["Deducciones"]["OtrosD"][od])
            noova["Deducciones"]["LOtrasDeducciones"] = data
        
        return noova

"""
    def _send_electronic_payroll(self):
        if 1:  # try:
            if self.config.environment == '2':
                api_send = API_SEND['2']
            else:
                api_send = API_SEND['1']

            res = send_payroll_psk(
                self.payroll,
                self.config,
                api_send,
                API_SIGN[self.payroll.payroll_type],
            )
            if res.get('result') and res.get('result') == 'false':
                self.payroll.get_message(res['message'])
                return
            if self.config.environment == '2':
                response = res['responseDian']['Envelope']['Body']
                if 'SendTestSetAsyncResponse' in response:
                    self.payroll.write([self.payroll], {
                        'electronic_state': 'submitted',
                        'cune': self.payroll.get_cune(),
                        'zip_key': response['SendTestSetAsyncResponse']['ZipKey']
                    })
            else:
                response = res['responseDian']['Envelope']['Body']['SendNominaSyncResponse']['SendNominaSyncResult']

                xml_response_dian = encode_payroll(
                    response['XmlBase64Bytes'], 'decode')
                if response['IsValid'] == 'true':
                    payroll_type = 'nie'
                    if self.payroll.payroll_type != '102':
                        payroll_type = 'niae'

                    self.payroll.write([self.payroll], {
                        'cune': self.payroll.get_cune(self.payroll.payroll_type),
                        'electronic_state': 'authorized',
                        'electronic_message': response['StatusMessage'],
                        'xml_response_dian_': xml_response_dian.encode('utf8'),
                    })
                else:
                    cadena = ''
                    for r in response['ErrorMessage']['string']:
                        cadena += r + '\n'
                    self.payroll.write([self.payroll], {
                        'rules_fail': cadena,
                        'electronic_message': response['StatusMessage'],
                        'electronic_state': 'rejected',
                        'xml_response_dian_': xml_response_dian.encode('utf8'),
                    })

        else:  # except Exception as e:
            self.payroll.get_message('Error de Envio')

    def send_request_status_document(payroll, config):
        api_send = API_SEND['3']
        if config and config.environment == '1':
            api_send = API_SEND['4']
        res = send_request_status_psk(
            payroll,
            api_send,
        )
        if not res:
            payroll.get_message('Error de solicitud')

        if config and config.environment == '1':
            response = res['responseDian']['Envelope']['Body']['GetStatusResponse']['GetStatusResult']
        else:
            response = res['responseDian']['Envelope']['Body']['GetStatusZipResponse']['GetStatusZipResult']['DianResponse']
        print(response)
        if response['IsValid'] == 'false':
            payroll.get_message('Cune no valido')
        xml_response_dian = encode_payroll(
            response['XmlBase64Bytes'], 'decode')
        if response['IsValid'] == 'true':
            payroll.write([payroll], {
                'cune': response['XmlDocumentKey'],
                'electronic_state': 'authorized',
                'electronic_message': response['StatusMessage'],
                'xml_response_dian_': xml_response_dian.encode('utf8'),
            })
        else:
            cadena = ''
            for r in response['ErrorMessage']['string']:
                cadena += r + '\n'
            payroll.write([payroll], {
                'rules_fail': cadena,
                'electronic_message': response['StatusMessage'],
                'electronic_state': 'rejected',
            })
        return
"""
