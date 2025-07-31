
# Código principal 

import numpy as np
import math
import os
import openpyxl
import streamlit as st
import pandas as pd
import io
from pathlib import Path
from math import ceil
import hashlib
import subprocess
import threading
import time

# Configuración de autenticación
VALID_PASSWORDS = {
    "JR": "admin",
    "MEG": "admin",
    "JM": "admin",
    "JJJ": "admin",
    "JAS": "admin",
    "AM": "admin",
    "RA": "admin",
    "MS": "admin",  
    # Agrega más usuarios aquí
}

CABLES_DATABASE = {
    "EX9-AC005EN-PSPS": {"descripcion": "Cable de comunicación 0.5m", "tipo": "comunicacion", "longitud": 0.5, "precio": 58.10,"Familias compatibles":"EX500, EX600", "Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
    "EX9-AC010EN-PSPS": {"descripcion": "Cable de comunicación 1m", "tipo": "comunicacion", "longitud": 1, "precio": 68.25, "Familias compatibles":"EX500, EX600","Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
    "EX9-AC020EN-PSPS": {"descripcion": "Cable de comunicación 2m", "tipo": "comunicacion", "longitud": 2, "precio": 74.34, "Familias compatibles":"EX500, EX600","Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
    "EX9-AC030EN-PSPS": {"descripcion": "Cable de comunicación 3m", "tipo": "comunicacion", "longitud": 3, "precio": 79.58,"Familias compatibles":"EX500, EX600","Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
    "EX9-AC050EN-PSPS": {"descripcion": "Cable de comunicación 5m", "tipo": "comunicacion", "longitud": 5, "precio": 92.15,"Familias compatibles":"EX500, EX600","Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
    "EX9-AC100EN-PSPS": {"descripcion": "Cable de comunicación 10m", "tipo": "comunicacion", "longitud": 10, "precio": 123.57,"Familias compatibles":"EX500, EX600","Protocolo":"EtherCat,Profinet, EthernetIP, Powerlink, Profisafe"},
   #CASCADA


    "EX9-AC005-SSPS": {"descripcion": "Cable de comunicación IO-Link 0.5m", "tipo": "comunicación", "longitud": 0.5, "precio": 26.70,"Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    "EX9-AC010-SSPS": {"descripcion": "Cable de comunicación IO-Link 1m", "tipo": "comunicación", "longitud": 1, "precio": 28.31, "Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    "EX9-AC020-SSPS": {"descripcion": "Cable de comunicación IO-Link 2m", "tipo": "comunicación", "longitud": 2, "precio": 30,"Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    "EX9-AC030-SSPS": {"descripcion": "Cable de comunicación IO-Link 3m", "tipo": "comunicación", "longitud": 3, "precio": 35.59, "Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    "EX9-AC050-SSPS": {"descripcion": "Cable de comunicación IO-Link 5m", "tipo": "comunicación", "longitud": 5, "precio": 44.48,"Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    "EX9-AC100-SSPS": {"descripcion": "Cable de comunicación IO-Link 10m", "tipo": "comunicación", "longitud": 10, "precio": 76.86,"Familias compatibles":"EX260, EX600", "Protocolo":"IO-Link"},
    
    "EX9-AC010EN-PSRJ": {"descripcion": "Cable de comunicación tipo RJ 0.5m", "tipo": "comunicación", "longitud": 0.5, "precio": 76.47,"Familias compatibles":"EX500, EX600, EXW1", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC020EN-PSRJ": {"descripcion": "Cable de comunicación tipo RJ 2m", "tipo": "comunicación", "longitud": 2, "precio": 85.69,"Familias compatibles":"EX500, EX600, EXW1", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC030EN-PSRJ": {"descripcion": "Cable de comunicación tipo RJ 3m", "tipo": "comunicación", "longitud": 3, "precio": 94.91, "Familias compatibles":"EX500, EX600, EXW1", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC050EN-PSRJ": {"descripcion": "Cable de comunicación tipo RJ 5m", "tipo": "comunicación", "longitud": 5, "precio": 111.19,"Familias compatibles":"EX500, EX600, EXW1", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC100EN-PSRJ": {"descripcion": "Cable de comunicación tipo RJ 10m", "tipo": "comunicación", "longitud": 10, "precio": 160.16,"Familias compatibles":"EX500, EX600, EXW1", "Protocolo":"Profinet, EthernetIP"},
    
    "EX9-AC010-1": {"descripcion": "Cable de alimentación 1m", "tipo": "alimentación", "longitud": 1, "precio": 34.82,"Familias compatibles":"EX500", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC030-1": {"descripcion": "Cable de alimentación 3m", "tipo": "alimentación", "longitud": 3, "precio": 42.89,"Familias compatibles":"EX500", "Protocolo":"Profinet, EthernetIP"},
    "EX9-AC050-1": {"descripcion": "Cable de alimentación 5m", "tipo": "alimentación", "longitud": 5, "precio": 54.26,"Familias compatibles":"EX500", "Protocolo":"Profinet, EthernetIP"},
    
    "EX500-AP010- S": {"descripcion": "Cable de alimentación 1m", "tipo": "alimentación", "longitud": 1, "precio": 50.45, "Familias compatibles":"EX260, EX600, EXW1", "Protocolo":"EtherCat, Profinet, EthernetIP, Powerlink"},
    "EX500-AP050- S": {"descripcion": "Cable de alimentación 5m", "tipo": "alimentación", "longitud": 5, "precio": 54.26, "Familias compatibles":"EX260, EX600, EXW1", "Protocolo":"EtherCat, Profinet, EthernetIP, Powerlink"},
    }

def select_optimal_cable_by_distance(cable_type, required_length, familia, cascada=False, protocolo_iolink=False):
    """
    Selecciona el cable óptimo basado en distancia, familia y configuración
    Reglas simplificadas:
    - Por defecto: PSRJ para comunicación
    - Si protocolo es IO-Link: SSPS para comunicación
    - Si cascada=True: PSPS para comunicación
    """
    available_cables = {}
    
    for ref, info in CABLES_DATABASE.items():
        # Verificar tipo de cable
        if info["tipo"].lower() != cable_type.lower():
            continue
            
        # Verificar longitud (debe ser >= requerida)
        if info["longitud"] < required_length:
            continue
            
        # Verificar familia compatible
        familias_compatibles = [f.strip() for f in info["Familias compatibles"].split(",")]
        if familia not in familias_compatibles:
            continue

        # Lógica de selección por tipo de conector para comunicación
        if cable_type.lower() == "comunicacion":
            if cascada and "PSPS" in ref:
                # Para cascada, solo cables PSPS
                available_cables[ref] = info
            elif protocolo_iolink and "SSPS" in ref:
                # Para IO-Link, solo cables SSPS
                available_cables[ref] = info
            elif not cascada and not protocolo_iolink and "PSRJ" in ref:
                # Por defecto, cables PSRJ (RJ45)
                available_cables[ref] = info
        else:
            # Para alimentación, cualquier cable compatible
            available_cables[ref] = info
    
    if not available_cables:
        return None, None
    
    # Seleccionar el cable con menor longitud que cumpla el requisito (más económico)
    optimal_cable = min(available_cables.items(), key=lambda x: x[1]["longitud"])
    return optimal_cable[0], optimal_cable[1]

def calculate_cables_needed_corrected(familia, solution, req, protocolo, cascada=False):
    """
    Calcula los cables necesarios según la familia y configuración
    Lógica corregida por familia
    """
    cables_needed = []
    distance = req['distance_m']
    num_zones = req['num_zones']
    has_wireless = solution.get('Has_wireless', False)
    protocolo_iolink = "io-link" in protocolo.lower()
    
    if familia in ["EX600", "EX260"]:
        # EX600/EX260: Un cable de comunicación + un cable de alimentación por cabecera
        num_headers = num_zones
        
        # Cable de comunicación
        if cascada and num_headers > 1:
            # Cascada: necesita cables PSPS entre cabeceras (n-1 cables)
            comm_cable_ref, comm_cable_info = select_optimal_cable_by_distance(
                "comunicacion", distance, familia, cascada=True, protocolo_iolink=protocolo_iolink
            )
            if comm_cable_ref:
                cables_needed.append({
                    "referencia": comm_cable_ref,
                    "descripcion": comm_cable_info["descripcion"] + " (Cascada entre cabeceras)",
                    "cantidad": num_headers - 1,
                    "precio_unitario": comm_cable_info["precio"],
                    "precio_total": comm_cable_info["precio"] * (num_headers - 1),
                    "tipo": "comunicacion"
                })
        
        # Cable de comunicación al PLC (siempre 1, independiente de cascada)
        comm_cable_ref, comm_cable_info = select_optimal_cable_by_distance(
            "comunicacion", distance, familia, cascada=False, protocolo_iolink=protocolo_iolink
        )
        if comm_cable_ref:
            cables_needed.append({
                "referencia": comm_cable_ref,
                "descripcion": comm_cable_info["descripcion"] + " (Cabecera → PLC)",
                "cantidad": 1,
                "precio_unitario": comm_cable_info["precio"],
                "precio_total": comm_cable_info["precio"],
                "tipo": "comunicacion"
            })
        
        # Cables de alimentación (uno por cabecera)
        pwr_cable_ref, pwr_cable_info = select_optimal_cable_by_distance(
            "alimentacion", distance, familia
        )
        if pwr_cable_ref:
            cables_needed.append({
                "referencia": pwr_cable_ref,
                "descripcion": pwr_cable_info["descripcion"] + " (Alimentación cabeceras)",
                "cantidad": num_headers,
                "precio_unitario": pwr_cable_info["precio"],
                "precio_total": pwr_cable_info["precio"] * num_headers,
                "tipo": "alimentacion"
            })
    
    elif familia == "EX500":
        # EX500: Gateway necesita comunicación + alimentación
        #        Cabeceras adicionales necesitan cables de derivación (alimentación)
        
        # Cable comunicación Gateway → PLC
        comm_cable_ref, comm_cable_info = select_optimal_cable_by_distance(
            "comunicacion", distance, familia, cascada=False, protocolo_iolink=protocolo_iolink
        )
        if comm_cable_ref:
            cables_needed.append({
                "referencia": comm_cable_ref,
                "descripcion": comm_cable_info["descripcion"] + " (Gateway → PLC)",
                "cantidad": 1,
                "precio_unitario": comm_cable_info["precio"],
                "precio_total": comm_cable_info["precio"],
                "tipo": "comunicacion"
            })
        
        # Cables de alimentación/derivación (Gateway + cabeceras adicionales)
        total_headers = num_zones  # 1 Gateway + (n-1) cabeceras adicionales
        pwr_cable_ref, pwr_cable_info = select_optimal_cable_by_distance(
            "alimentacion", distance, familia
        )
        if pwr_cable_ref:
            cables_needed.append({
                "referencia": pwr_cable_ref,
                "descripcion": pwr_cable_info["descripcion"] + " (Gateway + derivación)",
                "cantidad": total_headers,
                "precio_unitario": pwr_cable_info["precio"],
                "precio_total": pwr_cable_info["precio"] * total_headers,
                "tipo": "alimentacion"
            })
    
    elif familia == "EXW1":
        # EXW1: Maestro necesita comunicación + alimentación
        #       Esclavos/remotos solo necesitan alimentación
        
        # Cable comunicación Maestro → PLC
        comm_cable_ref, comm_cable_info = select_optimal_cable_by_distance(
            "comunicacion", distance, familia, cascada=False, protocolo_iolink=False  # EXW1 usa su propio protocolo wireless
        )
        if comm_cable_ref:
            cables_needed.append({
                "referencia": comm_cable_ref,
                "descripcion": comm_cable_info["descripcion"] + " (Maestro → PLC)",
                "cantidad": 1,
                "precio_unitario": comm_cable_info["precio"],
                "precio_total": comm_cable_info["precio"],
                "tipo": "comunicacion"
            })
        
        # Cables de alimentación (Maestro + Esclavos)
        num_wireless_modules = 1  # 1 maestro
        if 'Wireless_modules' in solution:
            num_wireless_modules += sum(data['quantity'] for data in solution['Wireless_modules'].values())
        
        pwr_cable_ref, pwr_cable_info = select_optimal_cable_by_distance(
            "alimentacion", distance, familia
        )
        if pwr_cable_ref:
            cables_needed.append({
                "referencia": pwr_cable_ref,
                "descripcion": pwr_cable_info["descripcion"] + " (Maestro + Esclavos)",
                "cantidad": num_wireless_modules,
                "precio_unitario": pwr_cable_info["precio"],
                "precio_total": pwr_cable_info["precio"] * num_wireless_modules,
                "tipo": "alimentacion"
            })
    
    return cables_needed

def process_families_data_new(df):
    """Procesa los datos de familias del nuevo formato Excel - CORREGIDO"""
    df.columns = df.columns.astype(str).str.strip()
    
    # Buscar filas clave por contenido, no por posición fija
    familia_row_idx = None
    max_modulos_row_idx = None
    protocolo_row_idx = None
    
    for idx, row in df.iterrows():
        row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)]).upper()
        if 'FAMILIA' in row_str and familia_row_idx is None:
            familia_row_idx = idx
        elif 'MAX' in row_str and 'MODUL' in row_str and max_modulos_row_idx is None:
            max_modulos_row_idx = idx
        elif 'PROTOCOL' in row_str and protocolo_row_idx is None:
            protocolo_row_idx = idx
    
    # Si no encuentra las filas, usar valores por defecto
    if familia_row_idx is None:
        familia_row_idx = 0
    
    fam_limits = {}
    fam_protocols = {}
    
    # Procesar cada columna (cada familia)
    for col_idx in range(1, len(df.columns)):  # Empezar desde columna 1
        try:
            # Extraer familia
            familia = str(df.iloc[familia_row_idx, col_idx]).strip()
            if pd.isna(df.iloc[familia_row_idx, col_idx]) or familia == 'nan' or len(familia) < 2:
                continue
                
            # Extraer max módulos
            if max_modulos_row_idx is not None:
                try:
                    max_modulos_val = df.iloc[max_modulos_row_idx, col_idx]
                    if pd.notna(max_modulos_val):
                        max_modulos = int(float(max_modulos_val))
                    else:
                        max_modulos = 8  # valor por defecto
                except (ValueError, TypeError):
                    max_modulos = 8
            else:
                max_modulos = 8
                
            # Extraer protocolos - CORREGIDO
            if protocolo_row_idx is not None:
                try:
                    protocolo_val = df.iloc[protocolo_row_idx, col_idx]
                    if pd.notna(protocolo_val):
                        protocolo_str = str(protocolo_val).strip()
                        # Limpiar y dividir protocolos
                        if protocolo_str and protocolo_str != 'nan':
                            # Reemplazar diferentes separadores por comas
                            for sep in [';', '|', '/', '\n', '+']:
                                protocolo_str = protocolo_str.replace(sep, ',')
                            
                            # Dividir y limpiar
                            protocolos = []
                            for p in protocolo_str.split(','):
                                p_clean = p.strip()
                                if p_clean and p_clean not in protocolos:
                                    protocolos.append(p_clean)
                        else:
                            protocolos = ["Sin especificar"]
                    else:
                        protocolos = ["Sin especificar"]
                except (IndexError, ValueError):
                    protocolos = ["Sin especificar"]
            else:
                # Protocolos por defecto según familia
                if 'EX260' in familia:
                    protocolos = ["IO-Link"]
                elif 'EX600' in familia:
                    protocolos = ["EtherCAT", "Profinet", "EthernetIP", "Powerlink"]
                elif 'EXW1' in familia:
                    protocolos = ["IO-Link Wireless"]
                elif 'EX500' in familia:
                    protocolos = ["DeviceNet", "CC-Link"]
                else:
                    protocolos = ["Sin especificar"]
            
            fam_limits[familia] = max_modulos
            fam_protocols[familia] = protocolos
            
        except Exception as e:
            continue
    
    # Valores por defecto si no se encontró nada
    if not fam_limits:
        fam_limits = {
            "EX260": 8, 
            "EX600": 8, 
            "EXW1": 8, 
            "EX500": 8
        }
    
    if not fam_protocols:
        fam_protocols = {
            "EX260": ["IO-Link"],
            "EX600": ["EtherCAT", "Profinet", "EthernetIP", "Powerlink"], 
            "EXW1": ["IO-Link Wireless"],
            "EX500": ["DeviceNet", "CC-Link"]
        }
    
    return fam_limits, fam_protocols

def process_cable_data(df):
    """Procesa los datos de cables del Excel"""
    cable_data = {}
    
    # Buscar filas que contengan información de cables
    for idx, row in df.iterrows():
        if idx < 13:  # Las primeras 13 filas son información de familias
            continue
            
        # Extraer información de cables de las filas 14 en adelante
        referencia = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else ""
        if referencia and referencia != 'nan':
            tipo = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else ""
            try:
                longitud = float(row.iloc[4]) if not pd.isna(row.iloc[4]) else 0
                precio = float(row.iloc[12]) if not pd.isna(row.iloc[12]) else 0
            except (ValueError, IndexError):
                longitud = 0
                precio = 0
                
            if longitud > 0 and precio > 0:
                cable_data[referencia] = {
                    "tipo": tipo.lower(),
                    "longitud": longitud,
                    "precio": precio,
                    "descripcion": f"{tipo} {longitud}m"
                }
    
    return cable_data

def enumerate_solutions_with_cables(req, df, fam_limits, protocolo, cascada=False):
    """
    Enumera todas las soluciones posibles incluyendo el cálculo de cables
    (fusiona enumerate_solutions y añade el cableado).
    """
    familias_disponibles = df["Familia"].unique()
    solutions = []
    rejected_families = []

    for fam in familias_disponibles:
        fam_df = df[df["Familia"] == fam]
        max_mods = fam_limits.get(fam, 9)

        rejection_reason = None

        # Buscar módulo base - si no hay, crear uno virtual
        base = fam_df[fam_df["Tipo"].str.lower() == "base"]
        if base.empty:
            base_price = 200.0
            base_ref = f"{fam}-CPU-BASE"
        else:
            base = base.sort_values("Precio").iloc[0]
            base_price = base["Precio"]
            base_ref = base["Referencia"]

        zone_modules = []
        total_modules_needed = 0
        wireless_modules = []
        has_wireless_zones = False

        for zone in req['zones']:
            zone_id = zone['zone_id']
            di_needed = zone['digital_inputs']
            do_needed = zone['digital_outputs']
            iol_needed = zone['io_link_sensors']
            ai_needed = zone['analog_inputs']
            ao_needed = zone['analog_outputs']

            zone_solution, zone_modules_count, zone_error = calculate_zone_modules(
                fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed
            )

            if zone_error:
                rejection_reason = f"Zona {zone_id}: {zone_error}"
                break

            zone_normal_modules = []
            zone_wireless_modules = []
            for mod, qty in zone_solution:
                if mod['Wireless']:
                    has_wireless_zones = True
                    zone_wireless_modules.append((mod, qty, zone_id))
                    wireless_modules.append((mod, qty, zone_id))
                else:
                    zone_normal_modules.append((mod, qty))

            zone_modules.append({
                'zone_id': zone_id,
                'modules': zone_normal_modules,
                'wireless_modules': zone_wireless_modules,
                'modules_count': (
                    sum(qty for mod, qty in zone_normal_modules) +
                    sum(qty for mod, qty, _ in zone_wireless_modules)
                )
            })
            total_modules_needed += sum(qty for mod, qty in zone_normal_modules)

        if rejection_reason:
            rejected_families.append({
                "Familia": fam,
                "Razon": rejection_reason,
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods
            })
            continue

        if has_wireless_zones:
            wireless_master_modules = 1
            total_modules_needed += wireless_master_modules
        else:
            wireless_master_modules = 0

        if total_modules_needed > max_mods:
            rejection_reason = f"Excede el límite de módulos ({total_modules_needed} > {max_mods})"
            rejected_families.append({
                "Familia": fam,
                "Razon": rejection_reason,
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods
            })
            continue

        if has_wireless_zones:
            wireless_master_ref = f"{fam}-WIRELESS-MASTER"
            wireless_master_price = 300.0
            price = wireless_master_price
            components = [(wireless_master_ref, 1)]
        else:
            num_headers_needed = req['num_zones']
            price = base_price * num_headers_needed
            components = [(base_ref, num_headers_needed)]

        module_totals = {}
        for zone_data in zone_modules:
            for mod, qty in zone_data['modules']:
                ref = mod['Referencia']
                if ref in module_totals:
                    module_totals[ref]['quantity'] += qty
                else:
                    module_totals[ref] = {'module': mod, 'quantity': qty}

        wireless_components = {}
        for mod, qty, zone_id in wireless_modules:
            ref = mod['Referencia']
            if ref in wireless_components:
                wireless_components[ref]['quantity'] += qty
                wireless_components[ref]['zones'].append(zone_id)
            else:
                wireless_components[ref] = {
                    'module': mod,
                    'quantity': qty,
                    'zones': [zone_id]
                }

        for ref, data in module_totals.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += mod['Precio'] * qty

        for ref, data in wireless_components.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += mod['Precio'] * qty

        solution = {
            "Familia": fam,
            "Precio_modulos": round(price, 2),
            "Componentes": components,
            "Modulos_totales": total_modules_needed,
            "Distribucion_zonas": zone_modules,
            "Wireless_modules": wireless_components,
            "Has_wireless": has_wireless_zones
        }

        # Cálculo de cables:
        cables_needed = calculate_cables_needed_corrected(fam, solution, req, protocolo, cascada)
        cables_total_price = sum(cable["precio_total"] for cable in cables_needed)
        solution["Cables"] = cables_needed
        solution["Precio_cables"] = round(cables_total_price, 2)
        solution["Precio_total_con_cables"] = round(price + cables_total_price, 2)
        solution["Configuracion_cascada"] = cascada if fam in ["EX260", "EX600"] else False

        solutions.append(solution)

    solutions.sort(key=lambda s: s["Precio_total_con_cables"])
    return solutions, rejected_families


def check_password():
    # Crear dos columnas: una para la imagen y otra para el contenido
        def password_entered():
            username = st.session_state["username"]
            password = st.session_state["password"]

            if username in VALID_PASSWORDS and VALID_PASSWORDS[username] == password:
                st.session_state["password_correct"] = True
                st.session_state["current_user"] = username
                del st.session_state["password"]

                if 'has_counted_login' not in st.session_state:
                    st.session_state['has_counted_login'] = True
                    visitas = update_counter()
                    st.toast(f"✅ Bienvenido {username}. Esta app se ha usado {visitas} veces.")
            else:
                st.session_state["password_correct"] = False
        if "password_correct" not in st.session_state:
            st.title("🔐 Acceso al Calculador SMC")
            st.text_input("Usuario", key="username")
            st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
            return False
        elif not st.session_state["password_correct"]:
            st.title("🔐 Acceso al Calculador SMC")
            st.text_input("Usuario", key="username")
            st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
            st.error("Usuario o contraseña incorrectos")
            return False
        else:
            return True


@st.cache_data
def load_catalog_with_limits_web(catalog_df, families_df):
    """Versión adaptada para web de la función de carga de catálogo - CORREGIDA"""
    fam_limits, fam_protocols = process_families_data_new(families_df)  # Usar la función corregida
    mod_df = process_module_data(catalog_df)
    return mod_df, fam_limits, fam_protocols

def process_families_data(df):
    """Procesa los datos de familias"""
    df.columns = df.columns.str.strip()

    # Buscar la fila que contiene "Familia"
    familia_row_idx = None
    for idx, row in df.iterrows():
        if any('Familia' in str(cell) for cell in row):
            familia_row_idx = idx
            break

    if familia_row_idx is None:
        familia_row_idx = 0

    # Usar esa fila como nombres de familias
    familia_names = df.iloc[familia_row_idx].fillna('').astype(str).tolist()

    # Buscar la fila que contiene "Max_Modulos"
    max_modulos_row_idx = None
    for idx, row in df.iterrows():
        if any('Max_Modulos' in str(cell) for cell in row):
            max_modulos_row_idx = idx
            break

    # Buscar la fila que contiene información de protocolos
    protocolo_row_idx = None
    for idx, row in df.iterrows():
        if any('Protocolo' in str(cell) for cell in row):
            protocolo_row_idx = idx
            break

    # Procesar límites de módulos
    if max_modulos_row_idx is None:
        fam_limits = {"EX500": 4, "EX600": 9, "EXW1": 9}
    else:
        max_modulos_values = df.iloc[max_modulos_row_idx].fillna(0).tolist()
        fam_limits = {}
        for i, (familia, max_mod) in enumerate(zip(familia_names, max_modulos_values)):
            familia = str(familia).strip()
            if familia and familia != 'Familia' and len(familia) > 2:
                try:
                    max_mod_int = int(float(max_mod))
                    if max_mod_int > 0:
                        fam_limits[familia] = max_mod_int
                except (ValueError, TypeError):
                    continue

    # Procesar protocolos de comunicación
    if protocolo_row_idx is None:
        fam_protocols = {
            "EX500": ["DeviceNet", "CC-Link"],
            "EX600": ["EtherNet/IP", "Profinet", "EtherCAT"],
            "EXW1": ["IO-Link Wireless"]
        }
    else:
        protocolo_values = df.iloc[protocolo_row_idx].fillna('').astype(str).tolist()
        fam_protocols = {}
        for i, (familia, protocolo) in enumerate(zip(familia_names, protocolo_values)):
            familia = str(familia).strip()
            if familia and familia != 'Familia' and len(familia) > 2:
                if protocolo and protocolo.strip():
                    separadores = [',', ';', '|', '/']
                    protocolos_lista = [protocolo.strip()]

                    for sep in separadores:
                        if sep in protocolo:
                            protocolos_lista = [p.strip() for p in protocolo.split(sep) if p.strip()]
                            break

                    fam_protocols[familia] = protocolos_lista
                else:
                    fam_protocols[familia] = ["Sin especificar"]

    if not fam_limits:
        fam_limits = {"EX500": 4, "EX600": 9, "EXW1": 9}

    if not fam_protocols:
        fam_protocols = {
            "EX500": ["DeviceNet", "CC-Link"],
            "EX600": ["EtherNet/IP", "Profinet", "EtherCAT"],
            "EXW1": ["IO-Link Wireless"]
        }

    return fam_limits, fam_protocols

def process_module_data(df):
    """Procesa y limpia los datos de módulos del DataFrame - CORREGIDO"""
    # Crear una copia para no modificar el original
    df_work = df.copy()
    
    # Detectar si los datos están transpuestos
    if df_work.shape[1] > df_work.shape[0] or 'Columna' in df_work.columns:
        df_work = df_work.T
        df_work.columns = df_work.iloc[0]
        df_work = df_work[1:]
        df_work.reset_index(drop=True, inplace=True)
    
    # Mapeo más flexible de columnas
    column_mapping = {}
    for col in df_work.columns:
        col_str = str(col).lower().strip()
        if 'referencia' in col_str or 'ref' in col_str or col_str == 'columna':
            column_mapping[col] = 'Referencia'
        elif 'familia' in col_str:
            column_mapping[col] = 'Familia'
        elif 'tipo' in col_str:
            column_mapping[col] = 'Tipo'
        elif 'entrada' in col_str and 'di' in col_str:
            column_mapping[col] = 'Entradas_DI'
        elif 'salida' in col_str and 'do' in col_str:
            column_mapping[col] = 'Salidas_DO'
        elif 'io' in col_str and 'link' in col_str:
            column_mapping[col] = 'IO_Link_Ports'
        elif 'analog' in col_str and 'in' in col_str:
            column_mapping[col] = 'Analog_In'
        elif 'analog' in col_str and 'out' in col_str:
            column_mapping[col] = 'Analog_Out'
        elif 'conector' in col_str:
            column_mapping[col] = 'Conector'
        elif 'wireless' in col_str:
            column_mapping[col] = 'Wireless'
        elif 'polaridad' in col_str:
            column_mapping[col] = 'Polaridad'
        elif 'precio' in col_str:
            column_mapping[col] = 'Precio'
    
    # Aplicar el mapeo
    df_work.rename(columns=column_mapping, inplace=True)
    
    # Si no hay columna Referencia, usar la primera columna o el índice
    if 'Referencia' not in df_work.columns:
        if len(df_work.columns) > 0:
            df_work['Referencia'] = df_work.iloc[:, 0]
        else:
            df_work['Referencia'] = df_work.index
    
    # Limpiar valores nulos
    df_work = df_work.fillna(0)
    
    # Convertir columnas numéricas con mejor manejo de errores
    numeric_columns = ["Entradas_DI", "Salidas_DO", "IO_Link_Ports", "Analog_In", "Analog_Out", "Precio"]
    for col in numeric_columns:
        if col in df_work.columns:
            # Convertir a string primero para limpiar
            df_work[col] = df_work[col].astype(str).str.replace(',', '.').str.strip()
            # Luego convertir a numérico
            df_work[col] = pd.to_numeric(df_work[col], errors='coerce').fillna(0)
    
    # Convertir columnas booleanas con mejor detección
    if 'Wireless' in df_work.columns:
        df_work['Wireless'] = df_work['Wireless'].astype(str).str.upper().str.strip()
        df_work['Wireless'] = df_work['Wireless'].isin(['TRUE', 'YES', '1', 'SI', 'SÍ', 'VERDADERO'])
    else:
        df_work['Wireless'] = False
    
    # Asegurar que las columnas necesarias existen con valores por defecto
    required_columns = {
        'Referencia': 'MOD-001',
        'Familia': 'EX600', 
        'Tipo': 'DI',
        'Entradas_DI': 0,
        'Salidas_DO': 0, 
        'IO_Link_Ports': 0,
        'Analog_In': 0,
        'Analog_Out': 0,
        'Precio': 100.0,
        'Conector': 'M12',
        'Polaridad': 'PNP',
        'Wireless': False
    }
    
    for col, default_val in required_columns.items():
        if col not in df_work.columns:
            df_work[col] = default_val
    
    # Filtrar filas vacías o inválidas
    df_work = df_work[
        (df_work['Referencia'].astype(str).str.len() > 2) &  # Referencia válida
        (df_work['Precio'] > 0) &  # Precio válido
        (df_work['Familia'].astype(str).str.len() > 2)  # Familia válida
    ]
    
    return df_work

def filter_families_by_protocol(df, fam_limits, fam_protocols, selected_protocol):
    """Filtra las familias según el protocolo seleccionado - CORREGIDO"""
    compatible_families = []
    
    # Normalizar el protocolo seleccionado para comparación
    selected_protocol_norm = selected_protocol.lower().strip()
    
    for familia, protocolos in fam_protocols.items():
        # Normalizar protocolos de la familia para comparación
        protocolos_norm = [p.lower().strip() for p in protocolos]
        
        # Buscar coincidencias exactas o parciales
        for protocolo in protocolos_norm:
            if (selected_protocol_norm == protocolo or 
                selected_protocol_norm in protocolo or 
                protocolo in selected_protocol_norm):
                compatible_families.append(familia)
                break
    
    if not compatible_families:
        st.warning(f"No se encontraron familias compatibles con {selected_protocol}")
        return df, fam_limits, []
    
    # Filtrar el DataFrame de módulos
    filtered_df = df[df["Familia"].isin(compatible_families)]
    
    if filtered_df.empty:
        st.warning(f"No se encontraron módulos para las familias compatibles: {compatible_families}")
        return df, fam_limits, []
    
    # Filtrar los límites de familias
    filtered_limits = {fam: fam_limits[fam] for fam in compatible_families if fam in fam_limits}
    
    return filtered_df, filtered_limits, compatible_families

def calculate_zone_modules(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed):
    """Calcula los módulos necesarios para una zona específica"""
    if di_needed <= 0 and do_needed <= 0 and iol_needed <= 0 and ai_needed <= 0 and ao_needed <= 0:
        return [], 0, None

    def calculate_module_priority(mod):
        priority = 0
        if 'Polaridad' in mod.index:
            if str(mod['Polaridad']).upper() == 'PNP':
                priority += 0
            else:
                priority += 1000
        priority += mod['Precio']
        return priority

    all_mods = fam_df.copy()
    all_mods['priority'] = all_mods.apply(calculate_module_priority, axis=1)
    all_mods = all_mods.sort_values('priority')

    best_solution = None
    best_cost = float('inf')
    best_modules_count = float('inf')

    # Estrategia con módulos mixtos
    mixed_solutions = []

    for _, mod in all_mods.iterrows():
        di_cap = mod['Entradas_DI']
        do_cap = mod['Salidas_DO']
        iol_cap = mod['IO_Link_Ports']
        ai_cap = mod['Analog_In']
        ao_cap = mod['Analog_Out']

        if di_cap <= 0 and do_cap <= 0 and iol_cap <= 0 and ai_cap <= 0 and ao_cap <= 0:
            continue

        # Calcular cobertura para módulos con múltiples capacidades
        capabilities = []
        if di_cap > 0:
            capabilities.append(('di', di_needed, di_cap))
        if do_cap > 0:
            capabilities.append(('do', do_needed, do_cap))
        if ai_cap > 0:
            capabilities.append(('ai', ai_needed, ai_cap))
        if ao_cap > 0:
            capabilities.append(('ao', ao_needed, ao_cap))

        if len(capabilities) > 1:  # Módulo mixto
            needed_quantities = []
            for cap_type, needed, capacity in capabilities:
                if needed > 0:
                    needed_quantities.append(ceil(needed / capacity))
                else:
                    needed_quantities.append(0)
            
            needed_mixed = max(needed_quantities) if needed_quantities else 0

            if needed_mixed > 0:
                di_covered = min(di_needed, needed_mixed * di_cap)
                do_covered = min(do_needed, needed_mixed * do_cap)
                ai_covered = min(ai_needed, needed_mixed * ai_cap)
                ao_covered = min(ao_needed, needed_mixed * ao_cap)

                remaining_di = max(0, di_needed - di_covered)
                remaining_do = max(0, do_needed - do_covered)
                remaining_iol = iol_needed
                remaining_ai = max(0, ai_needed - ai_covered)
                remaining_ao = max(0, ao_needed - ao_covered)

                mixed_solutions.append({
                    'modules': [(mod, needed_mixed)],
                    'remaining_di': remaining_di,
                    'remaining_do': remaining_do,
                    'remaining_iol': remaining_iol,
                    'remaining_ai': remaining_ai,
                    'remaining_ao': remaining_ao,
                    'cost': mod['Precio'] * needed_mixed,
                    'count': needed_mixed
                })

    # Evaluar soluciones mixtas y completar
    for mix_sol in mixed_solutions:
        total_modules = mix_sol['modules'].copy()
        total_cost = mix_sol['cost']
        total_count = mix_sol['count']

        # Completar DI restantes
        if mix_sol['remaining_di'] > 0:
            di_mods = all_mods[all_mods['Entradas_DI'] > 0]
            for _, mod in di_mods.iterrows():
                needed = ceil(mix_sol['remaining_di'] / mod['Entradas_DI'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar DO restantes
        if mix_sol['remaining_do'] > 0:
            do_mods = all_mods[all_mods['Salidas_DO'] > 0]
            for _, mod in do_mods.iterrows():
                needed = ceil(mix_sol['remaining_do'] / mod['Salidas_DO'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar IO-Link
        if mix_sol['remaining_iol'] > 0:
            iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
            for _, mod in iol_mods.iterrows():
                needed = ceil(mix_sol['remaining_iol'] / mod['IO_Link_Ports'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar AI restantes
        if mix_sol['remaining_ai'] > 0:
            ai_mods = all_mods[all_mods['Analog_In'] > 0]
            for _, mod in ai_mods.iterrows():
                needed = ceil(mix_sol['remaining_ai'] / mod['Analog_In'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar AO restantes
        if mix_sol['remaining_ao'] > 0:
            ao_mods = all_mods[all_mods['Analog_Out'] > 0]
            for _, mod in ao_mods.iterrows():
                needed = ceil(mix_sol['remaining_ao'] / mod['Analog_Out'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Evaluar si esta solución es mejor
        if (total_count < best_modules_count or
            (total_count == best_modules_count and total_cost < best_cost)):
            best_solution = total_modules
            best_cost = total_cost
            best_modules_count = total_count

    # Estrategia con módulos separados (como respaldo)
    separate_modules = []
    separate_cost = 0
    separate_count = 0

    # DI separados
    if di_needed > 0:
        di_mods = all_mods[all_mods['Entradas_DI'] > 0]
        if not di_mods.empty:
            best_di = di_mods.iloc[0]
            needed = ceil(di_needed / best_di['Entradas_DI'])
            separate_modules.append((best_di, needed))
            separate_cost += best_di['Precio'] * needed
            separate_count += needed

    # DO separados
    if do_needed > 0:
        do_mods = all_mods[all_mods['Salidas_DO'] > 0]
        if not do_mods.empty:
            best_do = do_mods.iloc[0]
            needed = ceil(do_needed / best_do['Salidas_DO'])
            separate_modules.append((best_do, needed))
            separate_cost += best_do['Precio'] * needed
            separate_count += needed

    # IO-Link separados
    if iol_needed > 0:
        iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
        if not iol_mods.empty:
            best_iol = iol_mods.iloc[0]
            needed = ceil(iol_needed / best_iol['IO_Link_Ports'])
            separate_modules.append((best_iol, needed))
            separate_cost += best_iol['Precio'] * needed
            separate_count += needed

    # AI separados
    if ai_needed > 0:
        ai_mods = all_mods[all_mods['Analog_In'] > 0]
        if not ai_mods.empty:
            best_ai = ai_mods.iloc[0]
            needed = ceil(ai_needed / best_ai['Analog_In'])
            separate_modules.append((best_ai, needed))
            separate_cost += best_ai['Precio'] * needed
            separate_count += needed

    # AO separados
    if ao_needed > 0:
        ao_mods = all_mods[all_mods['Analog_Out'] > 0]
        if not ao_mods.empty:
            best_ao = ao_mods.iloc[0]
            needed = ceil(ao_needed / best_ao['Analog_Out'])
            separate_modules.append((best_ao, needed))
            separate_cost += best_ao['Precio'] * needed
            separate_count += needed

    # Comparar solución separada con la mejor mixta
    if (separate_count < best_modules_count or
        (separate_count == best_modules_count and separate_cost < best_cost)):
        best_solution = separate_modules
        best_cost = separate_cost
        best_modules_count = separate_count

    if best_solution is None:
        return [], 0, "No se encontraron módulos compatibles"

    # Verificar cobertura total
    total_di_covered = sum(mod['Entradas_DI'] * qty for mod, qty in best_solution)
    total_do_covered = sum(mod['Salidas_DO'] * qty for mod, qty in best_solution)
    total_iol_covered = sum(mod['IO_Link_Ports'] * qty for mod, qty in best_solution)
    total_ai_covered = sum(mod['Analog_In'] * qty for mod, qty in best_solution)
    total_ao_covered = sum(mod['Analog_Out'] * qty for mod, qty in best_solution)

    # Verificar que la solución cubre los requerimientos
    if (total_di_covered < di_needed or
        total_do_covered < do_needed or
        total_iol_covered < iol_needed or
        total_ai_covered < ai_needed or
        total_ao_covered < ao_needed):
        return [], 0, f"No se puede cubrir los requerimientos (DI: {total_di_covered}/{di_needed}, DO: {total_do_covered}/{do_needed}, IO-Link: {total_iol_covered}/{iol_needed}, AI: {total_ai_covered}/{ai_needed}, AO: {total_ao_covered}/{ao_needed})"

    return best_solution, best_modules_count, None

def generate_solution_report(req, solution, protocol):
    """Genera un reporte detallado de la solución"""
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("REPORTE DE SOLUCIÓN SMC")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Información general
    report_lines.append("INFORMACIÓN GENERAL:")
    report_lines.append(f"  Familia: {solution['Familia']}")
    report_lines.append(f"  Protocolo: {protocol}")
    report_lines.append(f"  Precio Total: {solution['Precio_total']}€")
    report_lines.append(f"  Módulos Totales: {solution['Modulos_totales']}")
    if solution.get('Has_wireless', False):
        report_lines.append(f"  Configuración Wireless: SÍ (1 cabecera maestra)")
    else:
        report_lines.append(f"  Cabeceras necesarias: {req['num_zones']} (una por zona)")
    report_lines.append("")

    # Configuración de zonas
    report_lines.append("CONFIGURACIÓN DE ZONAS:")
    report_lines.append(f"  Número de zonas: {req['num_zones']}")
    report_lines.append(f"  Distancia máxima: {req['distance_m']} m")
    report_lines.append("")

    for zone in req['zones']:
        zone_id = zone['zone_id']
        report_lines.append(f"  Zona {zone_id}:")
        report_lines.append(f"    - Entradas digitales: {zone['digital_inputs']}")
        report_lines.append(f"    - Salidas digitales: {zone['digital_outputs']}")
        report_lines.append(f"    - Sensores IO-Link: {zone['io_link_sensors']}")
        report_lines.append(f"    - Entradas analógicas: {zone['analog_inputs']}")
        report_lines.append(f"    - Salidas analógicas: {zone['analog_outputs']}")

    report_lines.append("")

    # Lista de componentes
    report_lines.append("LISTA DE COMPONENTES:")
    
    # Separar componentes por tipo
    base_components = []
    normal_components = []
    wireless_components = []
    
    for ref, qty in solution['Componentes']:
        if ref.endswith("-CPU-BASE"):
            base_components.append((ref, qty, 200.0))
        elif "WIRELESS-MASTER" in ref:
            base_components.append((ref, qty, 300.0))
        elif "PASTILLA" in ref:
            wireless_components.append((ref, qty, 0.0))  # Precio se calculará después
        else:
            normal_components.append((ref, qty, 0.0))  # Precio se calculará después

    # Mostrar componentes base
    report_lines.append("  COMPONENTES BASE:")
    for ref, qty, price in base_components:
        subtotal = price * qty
        report_lines.append(f"    {ref:<28} x{qty:>3} = {subtotal:>8.2f}€")

    # Mostrar módulos normales
    if normal_components:
        report_lines.append("  MÓDULOS NORMALES:")
        for ref, qty, _ in normal_components:
            # Aquí deberías obtener el precio real del módulo
            subtotal = 0.0  # Calcular precio real
            report_lines.append(f"    {ref:<28} x{qty:>3} = {subtotal:>8.2f}€")

    # Mostrar módulos wireless
    if wireless_components:
        report_lines.append("  MÓDULOS WIRELESS:")
        for ref, data in wireless_components.items():
            qty = data['quantity']
            zones = data['zones']
            zone_list = ", ".join([f"Z{z}" for z in zones])
            subtotal = data['module']['Precio'] * qty
            report_lines.append(f"    {ref:<28} x{qty:>3} = {subtotal:>8.2f}€ ({zone_list})")

    report_lines.append("-" * 50)
    report_lines.append(f"{'TOTAL:':<37} {solution['Precio_total']:>8.2f}€")
    report_lines.append("")

    if len(req['zones']) > 1:
        report_lines.append("DISTRIBUCIÓN POR ZONAS:")
        for zone_data in solution['Distribucion_zonas']:
            zone_id = zone_data['zone_id']
            zone_modules = zone_data['modules']
            zone_wireless = zone_data.get('wireless_modules', [])
            
            # Contar módulos normales + wireless
            normal_count = sum(qty for mod, qty in zone_modules)
            wireless_count = sum(qty for mod, qty, _ in zone_wireless) if zone_wireless else 0
            total_zone_count = normal_count + wireless_count

            report_lines.append(f"  Zona {zone_id} ({total_zone_count} módulos totales):")
            
            # Módulos normales
            if zone_modules:
                for mod, qty in zone_modules:
                    report_lines.append(f"    - {mod['Referencia']} x{qty}")
            
            # Módulos wireless
            if zone_wireless:
                for mod, qty, _ in zone_wireless:
                    report_lines.append(f"    - {mod['Referencia']} x{qty}")
            
            # Si no hay módulos en la zona
            if not zone_modules and not zone_wireless:
                report_lines.append(f"    Sin módulos asignados")

        report_lines.append("")

    # Información adicional sobre wireless
    if solution.get('Has_wireless', False):
        report_lines.append("CONFIGURACIÓN WIRELESS:")
        report_lines.append("  - Una cabecera maestra controla todas las pastillas")
        report_lines.append("  - Las pastillas están distribuidas por zonas")
        report_lines.append("")

    # Pie de página
    report_lines.append("=" * 60)
    report_lines.append("Reporte generado por Calculador SMC")
    report_lines.append("=" * 60)

    return "\n".join(report_lines)
def update_counter(file_path="counter.txt"):
    import os
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                count = int(f.read().strip())
            except ValueError:
                count = 0
    else:
        count = 0

    count += 1

    with open(file_path, "w") as f:
        f.write(str(count))

    return count

def main():
    # Inicialización de variables de sesión
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = ""
    if "logout_triggered" not in st.session_state:
        st.session_state.logout_triggered = False
    if "login_success" not in st.session_state:
        st.session_state.login_success = False

    # Si no está autenticado, mostrar login
    if not st.session_state.authenticated:
        login()
        if st.session_state.login_success:
            st.session_state.login_success = False
            
        return  # Detener ejecución aquí si no está autenticado

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Conectado como: {st.session_state.current_user}")

    # Botón de cerrar sesión
    if st.sidebar.button("🔓 Cerrar sesión", key="logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.session_state.logout_triggered = True

    # Mostrar la sección seleccionada
    if menu == "Configurador":
        mostrar_configurador()
    elif menu == "Conversor":
        mostrar_conversor()
    elif menu == "Tiempo de Ciclo":
        mostrar_tiempo_ciclo()
    elif menu == "Cálculo de Fuerzas":
        mostrar_fuerzas()

    # Ejecutar rerun fuera del callback del botón
    if st.session_state.logout_triggered:
        st.session_state.logout_triggered = False
       
def mostrar_configurador():
    if not check_password():
        return

    st.title("🔧 Calculador de Soluciones SMC")

    st.header("1. Cargar Archivos de Configuración")
    col1, col2 = st.columns(2)
    catalog_file = col1.file_uploader("Catálogo de Módulos", type=["xlsx"])
    families_file = col2.file_uploader("Configuración de Familias", type=["xlsx"])

    if catalog_file and families_file:
        try:
            catalog_df = pd.read_excel(catalog_file)
            families_df = pd.read_excel(families_file)
            df, fam_limits, fam_protocols = load_catalog_with_limits_web(catalog_df, families_df)
            st.success("✅ Archivos cargados correctamente.")

            st.header("2. Seleccionar Protocolo de Comunicación")
            all_protocols = sorted({p for protos in fam_protocols.values() for p in protos})
            selected_protocol = st.selectbox("Protocolo:", all_protocols)

            df, fam_limits, compatible_families = filter_families_by_protocol(df, fam_limits, fam_protocols, selected_protocol)
            if df.empty:
                st.error("❌ No hay módulos compatibles.")
                return

            st.header("3. Tipo de Conexión")
            cascada_option = st.selectbox("Tipo de conexión:", ["Cascada (PSPS)", "Individual al PLC"])
            cascada = cascada_option == "Cascada (PSPS)"

            st.header("4. Configuración de Zonas")
            num_zones = st.number_input("Número de zonas:", min_value=1, value=1)
            zones_equal = st.checkbox("¿Zonas iguales?")
            zones = []

            if zones_equal:
                colz = st.columns(5)
                di = colz[0].number_input("DI:", min_value=0)
                do = colz[1].number_input("DO:", min_value=0)
                iol = colz[2].number_input("IO-Link:", min_value=0)
                ai = colz[3].number_input("AI:", min_value=0)
                ao = colz[4].number_input("AO:", min_value=0)
                for i in range(num_zones):
                    zones.append({
                        'zone_id': i+1, 'digital_inputs': di, 'digital_outputs': do,
                        'io_link_sensors': iol, 'analog_inputs': ai, 'analog_outputs': ao
                    })
            else:
                for i in range(num_zones):
                    st.subheader(f"Zona {i+1}")
                    colz = st.columns(5)
                    zones.append({
                        'zone_id': i+1,
                        'digital_inputs': colz[0].number_input("DI:", min_value=0, key=f"di{i}"),
                        'digital_outputs': colz[1].number_input("DO:", min_value=0, key=f"do{i}"),
                        'io_link_sensors': colz[2].number_input("IO-Link:", min_value=0, key=f"iol{i}"),
                        'analog_inputs': colz[3].number_input("AI:", min_value=0, key=f"ai{i}"),
                        'analog_outputs': colz[4].number_input("AO:", min_value=0, key=f"ao{i}"),
                    })

            st.header("5. Parámetros Adicionales")
            distance = st.number_input("Distancia (m):", min_value=0.0, value=10.0)

            req = {
                'zones': zones,
                'num_zones': num_zones,
                'zones_equal': zones_equal,
                'distance_m': distance,
                'connector_type': '',
                'total_digital_inputs': sum(z['digital_inputs'] for z in zones),
                'total_digital_outputs': sum(z['digital_outputs'] for z in zones),
                'total_io_link_sensors': sum(z['io_link_sensors'] for z in zones),
                'total_analog_inputs': sum(z['analog_inputs'] for z in zones),
                'total_analog_outputs': sum(z['analog_outputs'] for z in zones),
            }
            req['total_inputs'] = req['total_digital_inputs'] + req['total_io_link_sensors'] + req['total_analog_inputs']
            req['total_outputs'] = req['total_digital_outputs'] + req['total_analog_outputs']

            if st.button("🔍 Calcular Soluciones"):
                with st.spinner("Calculando..."):
                    solutions, rejected = enumerate_solutions_with_cables(req, df, fam_limits, selected_protocol, cascada)

                    if not solutions:
                        st.error("❌ No se encontraron soluciones válidas.")
                        return

                    st.header("6. Mejores Soluciones")
                    for i, sol in enumerate(solutions[:3]):
                        with st.expander(f"💡 Solución {i+1}: {sol['Familia']} - {sol['Precio_total_con_cables']}€", expanded=(i==0)):
                            st.write(f"**💰 Módulos:** {sol['Precio_modulos']} €")
                            st.write(f"**🔌 Cables:** {sol['Precio_cables']} €")
                            st.write(f"**🧾 Total:** {sol['Precio_total_con_cables']} €")
                            st.write(f"**🔗 Tipo conexión:** {'Cascada' if sol['Configuracion_cascada'] else 'Individual'}")

                            st.markdown("### 📦 Distribución por zonas")
                            for zona in sol['Distribucion_zonas']:
                                st.markdown(f"**Zona {zona['zone_id']}**")
                                for mod, qty in zona['modules']:
                                    st.write(f"- {mod['Referencia']} ({mod['Tipo']}): {qty} uds")
                                for mod, qty, _ in zona['wireless_modules']:
                                    st.write(f"- {mod['Referencia']} (Wireless): {qty} uds")

                            if sol['Wireless_modules']:
                                st.markdown("### 📡 Módulos Wireless")
                                for ref, data in sol['Wireless_modules'].items():
                                    zonas = ', '.join(str(z) for z in data['zones'])
                                    st.write(f"- {ref}: {data['quantity']} uds (zonas {zonas})")

                            st.markdown("### 🔌 Cables incluidos")
                            for cable in sol['Cables']:
                                st.write(f"- {cable['referencia']} ({cable['tipo']}): {cable['cantidad']} uds - {cable['precio_total']} €")

        except Exception as e:
            st.error(f"❌ Error al procesar archivos: {str(e)}")
    else:
        st.info("📄 Carga ambos archivos para comenzar.")



if "logged_in" not in st.session_state:
    st.session_state.logged_in = False



def login():
    st.title("Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if username == "admin" and password == "1234":
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.session_state.login_success = True  # Nueva bandera
        else:
            st.error("Credenciales incorrectas")


st.sidebar.title("Menú de Navegación")
menu = st.sidebar.selectbox("Selecciona una sección:", ["Configurador", "Conversor", "Tiempo de Ciclo","Cálculo de Fuerzas"])


def mostrar_conversor():
    st.title("🔄 Conversor Fuerza-Par")

    st.subheader("Conversión Fuerza → Par")
    M = st.number_input("Par de entrada (Nm)", value=2.28)
    p = st.number_input("Paso (mm)", value=3.3)
    eta = st.number_input("Rendimiento mecánico", value=0.9)
    F = ((2 * 3.1416 * eta * M) / p)*1000
    st.write(f"Fuerza disponible: {F:.1f} N")

    st.subheader("Conversión Par → Fuerza")
    F2 = st.number_input("Fuerza (N)", value=800)
    p2 = st.number_input("Paso (mm)", value=4.0)
    eta2 = st.number_input("Rendimiento mecánico", value=0.8)
    M2 = (p2 * F2) / (2 * 3.1416 * eta2*1000)
    st.write(f"Par necesario: {M2:.3f} Nm")

def calcular_tc():
    vel = st.number_input("Velocidad máxima (mm/s)", value=3000)
    accel = st.number_input("Aceleración (mm/s²)", value=2400)
    total_distance = st.number_input("Recorrido total (mm)", value=1000)
    t_estab = st.number_input("Tiempo estabilizado (s)", value=0.05)
    # Cálculo alternativo del tiempo de aceleración
    if 0.5 * accel * (vel / accel)**2 > total_distance / 2:
        # Perfil triangular
        t_accel = math.sqrt(total_distance / accel)
        d_accel = total_distance / 2
        t_max_speed = 0
        d_max_speed = 0
        perfil = "Triangular"
        
    else:
        # Perfil trapezoidal
        t_accel = vel / accel
        d_accel = 0.5 * vel**2 / accel
        d_max_speed = total_distance - 2 * d_accel
        t_max_speed = d_max_speed / vel
        perfil = "Trapezoidal"
        

    
    t_cycle = 2 * t_accel + t_max_speed + t_estab

    return t_cycle, perfil, t_accel, d_accel, t_max_speed, d_max_speed
    


def mostrar_tiempo_ciclo():
    st.title("⏱️ Tiempo de Ciclo")

    t_cycle, perfil, t_accel, d_accel, t_max_speed, d_max_speed = calcular_tc()

    st.subheader("Resultados")
    st.write(f"**Tipo de perfil:** {perfil}")
    st.write(f"Tiempo de aceleración o frenada: `{t_accel:.4f}` s")
    st.write(f"Recorrido en aceleración o frenada: `{d_accel:.3f}` mm")
    st.write(f"Tiempo a velocidad máxima: `{t_max_speed:.4f}` s")
    st.write(f"Recorrido a velocidad máxima: `{d_max_speed:.3f}` mm")
    st.write(f"### Tiempo de Ciclo calculado: `{t_cycle:.4f}` segundos")

def mostrar_fuerzas():
    st.title("⚙️ Cálculo de Fuerzas e Inercias")

    # --- Parámetros de entrada para Fuerzas ---
    st.subheader("Parámetros de entrada - Fuerzas")
    masa_f = st.number_input("Masa a transportar (kg)", value=34.0, key="masa_f")
    inclinacion_f = st.number_input("Inclinación del movimiento (°)", value=85.0, key="inclinacion_f")
    rozamiento_f = st.number_input("Coeficiente de rozamiento", value=0.1, key="rozamiento_f")
    aceleracion_f = st.number_input("Aceleración necesaria (mm/s²)", value=13498.0, key="aceleracion_f")

    # --- Parámetros del sistema para Fuerzas ---
    st.subheader("Parámetros del sistema - Fuerzas")
    potencia_motor_f = st.number_input("Potencia del motor (W)", value=100.0, key="potencia_motor_f")
    paso_husillo_f = st.number_input("Paso del husillo (mm)", value=3.0, key="paso_husillo_f")
    rendimiento_f = st.number_input("Rendimiento", value=0.9, key="rendimiento_f")

    # --- Cálculo de Fuerza ---
    st.subheader("Cálculo de Fuerza")
    fuerza_necesaria = (
        rozamiento_f * masa_f * 9.81 * math.cos(math.radians(inclinacion_f)) +
        masa_f * 9.81 * math.sin(math.radians(inclinacion_f)) +
        masa_f * aceleracion_f / 1000
    )
    fuerza_disponible = (
        (191 * math.pi * potencia_motor_f) /
        ((paso_husillo_f * 30)) * rendimiento_f
    )

    st.metric("Fuerza Necesaria", f"{fuerza_necesaria:.0f} N")
    st.metric("Fuerza Disponible", f"{fuerza_disponible:.0f} N")
    st.metric("Coeficiente de Seguridad", f"{fuerza_disponible / fuerza_necesaria:.2f}")

    # --- Parámetros para Inercia ---
    st.subheader("Parámetros del sistema - Inercia")
    masa_i = st.number_input("Masa a transportar (kg)", value=34.0, key="masa_i")
    paso_husillo_i = st.number_input("Paso del husillo (mm)", value=3.0, key="paso_husillo_i")
    rendimiento_i = st.number_input("Rendimiento", value=0.9, key="rendimiento_i")
    diametro_i = st.number_input("Diámetro del husillo (mm)", value=20.0, key="diametro_i")
    carrera_i = st.number_input("Carrera (mm)", value=100.0, key="carrera_i")
    inercia_motor_i = st.number_input("Inercia del motor (kg·cm²)", value=0.672, key="inercia_motor_i")

    # --- Cálculo de Inercia ---
    ratio_inercia = (
        (masa_i * ((paso_husillo_i * 1e-3) / (2 * math.pi))**2 * 10000) +
        ((3.925 * math.pi * (carrera_i + 200) * (diametro_i / 2000)**4 * 10000) / rendimiento_i)
    ) / inercia_motor_i

    st.metric("Ratio de Inercia", f"{ratio_inercia:.2f}")


# Ejecutar la aplicación
if __name__ == "__main__":
    main()
       