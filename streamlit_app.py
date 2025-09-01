
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
import matplotlib.pyplot as plt

CABLES_DB = [
# === EJEMPLOS PRE-CARGADOS (ajusta/añade los tuyos) ===
# Comunicación
{"ref": "EX9-AC020EN-PSRJ", "families": ["EX600", "EXW1", "EX500"], "protocols": ["ETHERNET/IP", "ETHERCAT", "PROFINET"], "kind": "COM", "end_code": "PSRJ", "price": 85.69},
{"ref": "EX9-AC02EN-PSPS", "families": ["EX600", "EXW1", "EX260"], "protocols": ["ETHERNET/IP", "ETHERCAT", "PROFINET"], "kind": "COM", "end_code": "PSPS", "price": 74.34},
{"ref": "EX9-AC005-SSPS", "families": ["EX600", "EX260", "EXW1", "EX500"], "protocols": ["IO-LINK"], "kind": "COM", "end_code": "SSPS", "price": 44.48},


# Alimentación
{"ref": "PCA-141600", "families": ["EX500"], "protocols": ["ETHERNET/IP"], "kind": "ALIM", "end_code": "N/A", "price": 42.22},
{"ref": "PCA-1558810", "families": ["EX500", "EX600", "EXW1"], "protocols": ["PROFINET"], "kind": "ALIM", "end_code": "N/A", "price": 69.52},
{"ref": "EX500-AP050-S", "families": ["EX260"], "protocols": ["ANY"], "kind": "ALIM", "end_code": "N/A", "price": 28.63},


# Derivación (EX500)
{"ref": "EX500-AC030-SSPS", "families": ["EX500"], "protocols": ["ANY"], "kind": "DERIV", "end_code": "SSPS", "price": 38.18},


# === FIN DE EJEMPLOS ===
]

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

def check_password():
    """Sistema de autenticación mejorado"""
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

def load_family_data(file) -> dict:
    """Carga datos de familias desde archivo Excel, soportando múltiples protocolos por familia"""
    import pandas as pd

    df = pd.read_excel(file, header=None)

    # Localizar filas clave
    row_familia   = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("familia")][0]
    row_ref       = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("referencia")][0]
    row_protocol  = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("protocol")][0]
    row_precio    = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("precio")][0]
    row_maxmods   = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("max_modulos")][0]
    row_distancia = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("distancia")][0]
    # NUEVAS FILAS PARA EXW1 Y EX500
    try:
        row_maxremotos = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("max_remotos")][0]
    except:
        row_maxremotos = None
    
    try:
        row_senales_rama = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("señales_por_rama") | 
                                   df.iloc[:, 0].astype(str).str.lower().str.contains("senales_por_rama")][0]
    except:
        row_senales_rama = None

    familias_data = {}

    # Recorrer columnas desde la 2ª (índice 1)
    for col in range(1, df.shape[1]):
        familia   = str(df.iloc[row_familia, col]).strip()
        referencia= str(df.iloc[row_ref, col]).strip()
        protocolo = str(df.iloc[row_protocol, col]).strip()
        
        try:
            precio = float(df.iloc[row_precio, col])
        except:
            precio = 200.0

        try:
            max_modulos = int(df.iloc[row_maxmods, col])
        except:
            max_modulos = 8

        # NUEVOS CAMPOS
        try:
            max_remotos = int(df.iloc[row_maxremotos, col]) if row_maxremotos is not None else 0
        except:
            max_remotos = 0
            
        try:
            senales_por_rama = int(df.iloc[row_senales_rama, col]) if row_senales_rama is not None else 0
        except:
            senales_por_rama = 0

        try:
            distancia_admitida = float(df.iloc[row_distancia, col]) if row_distancia is not None else float('inf')
        except:
            distancia_admitida = float('inf')

        if familia and familia.lower() not in ["nan", "none", ""]:
            if familia not in familias_data:
                familias_data[familia] = {
                    "protocolos": [],
                    "cabeceras": [],
                    "max_modulos": max_modulos,
                    "max_remotos": max_remotos,
                    "senales_por_rama": senales_por_rama
                }

            # Añadir protocolo a la lista si no está
            if protocolo not in familias_data[familia]["protocolos"]:
                familias_data[familia]["protocolos"].append(protocolo)

            # Añadir cabecera
            familias_data[familia]["cabeceras"].append({
                "referencia": referencia,
                "precio": precio,
                "protocolo": protocolo
            })

    return familias_data

@st.cache_data
def load_catalog_with_limits_web(catalog_file, families_file):
    """Carga catálogo y familias"""
    familias_info = load_family_data(families_file)
    catalog_df = pd.read_excel(catalog_file, sheet_name=0)
    mod_df = process_module_data(catalog_df)
    return mod_df, familias_info

def process_module_data(df):
    """
    Procesa el archivo de catálogo horizontal (Configs.xlsx)
    y lo convierte en un DataFrame tabular estándar.
    Cada fila será un módulo, con columnas limpias.
    """

    # Detectar si está en formato horizontal
    if df.iloc[0, 0] == "Familia" or "Columna" in df.columns:
        # Transponer
        df = df.T
        df.columns = df.iloc[0]   # la primera fila transpuesta son los nombres de columnas
        df = df.drop(df.index[0]) # eliminar esa fila de nombres
        df.reset_index(drop=True, inplace=True)

    # Normalizar nombres de columnas
    column_mapping = {
        "Familia": "Familia",
        "Referencia": "Referencia",
        "Tipo": "Tipo",
        "Entradas_DI": "Entradas_DI",
        "Salidas_DO": "Salidas_DO",
        "IO_Link_Ports": "IO_Link_Ports",
        "Analog_In": "Analog_In",
        "Analog_Out": "Analog_Out",
        "Conector": "Conector",
        "Wireless": "Wireless",
        "Polaridad": "Polaridad",
        "Precio": "Precio"
    }

    df = df.rename(columns=column_mapping)

    # Asegurar columnas necesarias
    required = ["Referencia", "Familia", "Tipo", "Entradas_DI", "Salidas_DO", 
                "IO_Link_Ports", "Analog_In", "Analog_Out", "Precio", "Wireless", "Polaridad"]

    for col in required:
        if col not in df.columns:
            if col in ["Familia"]: 
                df[col] = "EX600"
            elif col in ["Tipo"]: 
                df[col] = "DI"
            elif col in ["Wireless"]: 
                df[col] = False
            elif col in ["Polaridad"]:
                df[col] = "NPN"
            elif col in ["Referencia"]:
                df[col] = f"MOD_{df.index}"
            else: 
                df[col] = 0

    # Convertir numéricos con mejor manejo de errores
    numeric_cols = ["Entradas_DI", "Salidas_DO", "IO_Link_Ports", "Analog_In", "Analog_Out", "Precio"]
    for col in numeric_cols:
        if col in df.columns:
            # Convertir a string primero para limpiar
            df[col] = df[col].astype(str).str.strip()
            # Reemplazar valores vacíos o 'nan' con '0'
            df[col] = df[col].replace(['', 'nan', 'None', 'NaN', 'null'], '0')
            # Convertir a numérico
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            # Asegurar que son enteros para todo excepto Precio
            if col != "Precio":
                df[col] = df[col].astype(int)
            else:
                # Para precio, asegurar que sea float positivo
                df[col] = df[col].astype(float)
                df[col] = df[col].abs()  # Asegurar valores positivos

    # Convertir Wireless a booleano con mejor manejo
    if "Wireless" in df.columns:
        df["Wireless"] = df["Wireless"].astype(str).str.strip().str.upper()
        df["Wireless"] = df["Wireless"].isin(["TRUE", "YES", "1", "SI", "SÍ"])
    else:
        df["Wireless"] = False

    # Limpiar columna Polaridad
    if "Polaridad" in df.columns:
        df["Polaridad"] = df["Polaridad"].astype(str).str.strip().str.upper()
        # Reemplazar valores vacíos con NPN por defecto
        df["Polaridad"] = df["Polaridad"].replace(['', 'NAN', 'NONE', 'NULL'], 'NPN')
    else:
        df["Polaridad"] = "NPN"

    # Limpiar columna Referencia
    if "Referencia" in df.columns:
        df["Referencia"] = df["Referencia"].astype(str).str.strip()
        # Reemplazar referencias vacías
        mask_empty_ref = df["Referencia"].isin(['', 'nan', 'None', 'NaN', 'null'])
        df.loc[mask_empty_ref, "Referencia"] = df.loc[mask_empty_ref].apply(
            lambda row: f"MOD_{row.name}", axis=1
        )

    # Limpiar columna Familia
    if "Familia" in df.columns:
        df["Familia"] = df["Familia"].astype(str).str.strip()
        df["Familia"] = df["Familia"].replace(['', 'nan', 'None', 'NaN', 'null'], 'EX600')

    # Eliminar filas completamente vacías o inválidas
    df = df.dropna(how='all')
    
    # Resetear índices después de la limpieza
    df = df.reset_index(drop=True)

    return df


    """Formatea un resumen de los cables para mostrar"""
    summary = []
    for cable_req in cables_needed:
        cable = cable_req["cable"]
        quantity = cable_req["quantity"]
        description = cable_req["description"]
        
        # Determinar tipo de cable
        tipo_cable = {
            "COM": "Comunicación",
            "ALIM": "Alimentación", 
            "DERIV": "Derivación"
        }.get(cable["kind"], cable["kind"])
        
        summary.append({
            "referencia": cable["ref"],
            "tipo": tipo_cable,
            "cantidad": quantity,
            "precio_unitario": cable["price"],
            "precio_total": cable["price"] * quantity,
            "descripcion": description
        })
    
    return summary

def filter_families_by_protocol(df, familias_info, fam_protocols, selected_protocol):
    """Filtra las familias según el protocolo seleccionado"""
    compatible_families = []

    for familia, info in familias_info.items():
        protocolos = info["protocolos"]
        if selected_protocol in protocolos:
            compatible_families.append(familia)

    if not compatible_families:
        return df, {}, []

    # Filtrar el DataFrame de módulos
    filtered_df = df[df["Familia"].isin(compatible_families)]

    # Filtrar los límites de familias
    filtered_limits = {}
    for fam in compatible_families:
        if fam in familias_info:
            filtered_limits[fam] = familias_info[fam]["max_modulos"]

    return filtered_df, filtered_limits, compatible_families

def safe_get(mod, key, default=0):
    """Acceso seguro a propiedades de un módulo sin romper si el tipo no es compatible"""
    try:
        # Caso 1: diccionario normal
        if isinstance(mod, dict):
            return mod.get(key, default)

        # Caso 2: fila de DataFrame (Series)
        elif isinstance(mod, pd.Series):
            if key in mod.index:
                value = mod[key]
                if pd.isna(value):
                    return default
                return value
            return default

        # Caso 3: evitar tipos primitivos directamente
        elif isinstance(mod, (int, float, str, bool, type(None))):
            return default

        # Caso 4: objetos indexables (listas, arrays, etc.)
        elif hasattr(mod, "__getitem__"):
            try:
                if key in mod:
                    value = mod[key]
                    if pd.isna(value):
                        return default
                    return value
            except Exception:
                return default

        # Caso 5: cualquier otro tipo raro
        else:
            return default

    except Exception as e:
        print(f"ERROR en safe_get con key '{key}': {e}, tipo: {type(mod)} - valor: {mod}")
        return default

def calculate_zone_modules(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed, familia_info, familia_name):
    """Calcula los módulos/remotos/ramas necesarios para una zona específica"""
    if di_needed <= 0 and do_needed <= 0 and iol_needed <= 0 and ai_needed <= 0 and ao_needed <= 0:
        return [], 0, None

    # DETERMINAR TIPO DE FAMILIA
    max_modulos = familia_info.get("max_modulos", 0)
    max_remotos = familia_info.get("max_remotos", 0)
    senales_por_rama = familia_info.get("senales_por_rama", 0)

    # FAMILIA EXW1 (WIRELESS - REMOTOS)
    if max_remotos > 0 and max_modulos == 0:
        return calculate_wireless_remotos(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed, max_remotos)
    
    # FAMILIA EX500 (RAMAS)
    elif senales_por_rama > 0 and max_modulos == 0:
        return calculate_ramas(di_needed, do_needed, iol_needed, ai_needed, ao_needed, senales_por_rama)
    
    # FAMILIAS TRADICIONALES (MÓDULOS)
    else:
        return calculate_traditional_modules(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed)

def calculate_wireless_remotos(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed, max_remotos):
    """Calcula remotos necesarios para EXW1"""
    
    def calculate_module_priority(mod):
        try:
            priority = 0
            polaridad = safe_get(mod, 'Polaridad', '')
            if str(polaridad).upper() == 'PNP':
                priority += 0
            else:
                priority += 1000
            
            precio = safe_get(mod, 'Precio', 1000)
            if precio is None or pd.isna(precio):
                precio = 1000
            
            priority += float(precio)
            return priority
        except Exception as e:
            return 2000

    all_mods = fam_df.copy()
    all_mods['priority'] = all_mods.apply(calculate_module_priority, axis=1)
    all_mods = all_mods.sort_values('priority')

    best_solution = None
    best_cost = float('inf')
    best_remotos_count = float('inf')

    # Probar diferentes combinaciones de remotos
    for _, mod in all_mods.iterrows():
        di_cap = safe_get(mod, 'Entradas_DI')
        do_cap = safe_get(mod, 'Salidas_DO')
        iol_cap = safe_get(mod, 'IO_Link_Ports')
        ai_cap = safe_get(mod, 'Analog_In')
        ao_cap = safe_get(mod, 'Analog_Out')

        if di_cap <= 0 and do_cap <= 0 and iol_cap <= 0 and ai_cap <= 0 and ao_cap <= 0:
            continue

        # Calcular cuántos remotos de este tipo necesitamos
        remotos_needed = []
        
        if di_needed > 0 and di_cap > 0:
            remotos_needed.append(math.ceil(di_needed / di_cap))
        if do_needed > 0 and do_cap > 0:
            remotos_needed.append(math.ceil(do_needed / do_cap))
        if iol_needed > 0 and iol_cap > 0:
            remotos_needed.append(math.ceil(iol_needed / iol_cap))
        if ai_needed > 0 and ai_cap > 0:
            remotos_needed.append(math.ceil(ai_needed / ai_cap))
        if ao_needed > 0 and ao_cap > 0:
            remotos_needed.append(math.ceil(ao_needed / ao_cap))

        if not remotos_needed:
            continue

        needed = max(remotos_needed)
        
        if needed > max_remotos:
            continue

        # Verificar si este remoto puede cubrir todas las necesidades
        total_di_covered = needed * di_cap
        total_do_covered = needed * do_cap
        total_iol_covered = needed * iol_cap
        total_ai_covered = needed * ai_cap
        total_ao_covered = needed * ao_cap

        if (total_di_covered >= di_needed and
            total_do_covered >= do_needed and
            total_iol_covered >= iol_needed and
            total_ai_covered >= ai_needed and
            total_ao_covered >= ao_needed):
            
            precio_mod = safe_get(mod, 'Precio')
            total_cost = precio_mod * needed
            
            if needed < best_remotos_count or (needed == best_remotos_count and total_cost < best_cost):
                best_solution = [(mod, needed)]
                best_cost = total_cost
                best_remotos_count = needed

    if best_solution is None:
        return [], 0, "No se encontraron remotos compatibles para EXW1"

    return best_solution, best_remotos_count, None

def calculate_ramas(di_needed, do_needed, iol_needed, ai_needed, ao_needed, senales_por_rama):
    """Calcula ramas necesarias para EX500"""
    
    # Calcular señales totales necesarias
    total_senales = di_needed + do_needed + iol_needed + ai_needed + ao_needed
    
    if total_senales <= 0:
        return [], 0, None
    
    # Calcular número de ramas necesarias
    ramas_necesarias = math.ceil(total_senales / senales_por_rama)
    
    # Para EX500, devolvemos un "módulo virtual" que representa las ramas
    rama_virtual = {
        'Referencia': 'EX500-RAMA',
        'Precio': 50.0,  # Precio estimado por rama
        'Tipo': 'Rama',
        'Entradas_DI': senales_por_rama,
        'Salidas_DO': 0,
        'IO_Link_Ports': 0,
        'Analog_In': 0,
        'Analog_Out': 0
    }
    
    return [(rama_virtual, ramas_necesarias)], ramas_necesarias, None

def calculate_traditional_modules(fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed):
    """Lógica original para familias tradicionales con módulos"""
    
    def calculate_module_priority(mod):
        try:
            priority = 0
            polaridad = safe_get(mod, 'Polaridad', '')
            if str(polaridad).upper() == 'PNP':
                priority += 0
            else:
                priority += 1000
            
            precio = safe_get(mod, 'Precio', 1000)
            if precio is None or pd.isna(precio):
                precio = 1000
            
            priority += float(precio)
            return priority
        except Exception as e:
            print(f"Error calculando prioridad: {e}")
            return 2000

    all_mods = fam_df.copy()
    all_mods['priority'] = all_mods.apply(calculate_module_priority, axis=1)
    all_mods = all_mods.sort_values('priority')

    best_solution = None
    best_cost = float('inf')
    best_modules_count = float('inf')

    # Estrategia con módulos mixtos
    mixed_solutions = []

    for _, mod in all_mods.iterrows():
        di_cap = safe_get(mod, 'Entradas_DI')
        do_cap = safe_get(mod, 'Salidas_DO')
        iol_cap = safe_get(mod, 'IO_Link_Ports')
        ai_cap = safe_get(mod, 'Analog_In')
        ao_cap = safe_get(mod, 'Analog_Out')

        if di_cap <= 0 and do_cap <= 0 and iol_cap <= 0 and ai_cap <= 0 and ao_cap <= 0:
            continue

        # capacidades mixtas
        capabilities = []
        if di_cap > 0: capabilities.append(('di', di_needed, di_cap))
        if do_cap > 0: capabilities.append(('do', do_needed, do_cap))
        if ai_cap > 0: capabilities.append(('ai', ai_needed, ai_cap))
        if ao_cap > 0: capabilities.append(('ao', ao_needed, ao_cap))

        if len(capabilities) > 1:
            needed_quantities = [ceil(needed / capacity) for cap_type, needed, capacity in capabilities if needed > 0]
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

                precio_mod = safe_get(mod, 'Precio')

                mixed_solutions.append({
                    'modules': [(mod, needed_mixed)],
                    'remaining_di': remaining_di,
                    'remaining_do': remaining_do,
                    'remaining_iol': remaining_iol,
                    'remaining_ai': remaining_ai,
                    'remaining_ao': remaining_ao,
                    'cost': precio_mod * needed_mixed,
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
            if not di_mods.empty:
                best_di = di_mods.iloc[0]
                di_capacity = safe_get(best_di, 'Entradas_DI')
                needed = ceil(mix_sol['remaining_di'] / di_capacity)
                precio_mod = safe_get(best_di, 'Precio')
                total_modules.append((best_di, needed))
                total_cost += precio_mod * needed
                total_count += needed

        # Completar DO restantes
        if mix_sol['remaining_do'] > 0:
            do_mods = all_mods[all_mods['Salidas_DO'] > 0]
            if not do_mods.empty:
                best_do = do_mods.iloc[0]
                do_capacity = safe_get(best_do, 'Salidas_DO')
                needed = ceil(mix_sol['remaining_do'] / do_capacity)
                precio_mod = safe_get(best_do, 'Precio')
                total_modules.append((best_do, needed))
                total_cost += precio_mod * needed
                total_count += needed

        # Completar IO-Link
        if mix_sol['remaining_iol'] > 0:
            iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
            if not iol_mods.empty:
                best_iol = iol_mods.iloc[0]
                iol_capacity = safe_get(best_iol, 'IO_Link_Ports')
                needed = ceil(mix_sol['remaining_iol'] / iol_capacity)
                precio_mod = safe_get(best_iol, 'Precio')
                total_modules.append((best_iol, needed))
                total_cost += precio_mod * needed
                total_count += needed

        # Completar AI restantes
        if mix_sol['remaining_ai'] > 0:
            ai_mods = all_mods[all_mods['Analog_In'] > 0]
            if not ai_mods.empty:
                best_ai = ai_mods.iloc[0]
                ai_capacity = safe_get(best_ai, 'Analog_In')
                needed = ceil(mix_sol['remaining_ai'] / ai_capacity)
                precio_mod = safe_get(best_ai, 'Precio')
                total_modules.append((best_ai, needed))
                total_cost += precio_mod * needed
                total_count += needed

        # Completar AO restantes
        if mix_sol['remaining_ao'] > 0:
            ao_mods = all_mods[all_mods['Analog_Out'] > 0]
            if not ao_mods.empty:
                best_ao = ao_mods.iloc[0]
                ao_capacity = safe_get(best_ao, 'Analog_Out')
                needed = ceil(mix_sol['remaining_ao'] / ao_capacity)
                precio_mod = safe_get(best_ao, 'Precio')
                total_modules.append((best_ao, needed))
                total_cost += precio_mod * needed
                total_count += needed

        # Evaluar si esta solución es mejor
        if (total_count < best_modules_count or
            (total_count == best_modules_count and total_cost < best_cost)):
            best_solution = total_modules
            best_cost = total_cost
            best_modules_count = total_count

    # Estrategia con módulos separados (respaldo)
    separate_modules = []
    separate_cost = 0
    separate_count = 0

    # DI separados
    if di_needed > 0:
        di_mods = all_mods[all_mods['Entradas_DI'] > 0]
        if not di_mods.empty:
            best_di = di_mods.iloc[0]
            di_capacity = safe_get(best_di, 'Entradas_DI')
            needed = ceil(di_needed / di_capacity)
            precio_mod = safe_get(best_di, 'Precio')
            separate_modules.append((best_di, needed))
            separate_cost += precio_mod * needed
            separate_count += needed

    # DO separados
    if do_needed > 0:
        do_mods = all_mods[all_mods['Salidas_DO'] > 0]
        if not do_mods.empty:
            best_do = do_mods.iloc[0]
            do_capacity = safe_get(best_do, 'Salidas_DO')
            needed = ceil(do_needed / do_capacity)
            precio_mod = safe_get(best_do, 'Precio')
            separate_modules.append((best_do, needed))
            separate_cost += precio_mod * needed
            separate_count += needed

    # IO-Link separados
    if iol_needed > 0:
        iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
        if not iol_mods.empty:
            best_iol = iol_mods.iloc[0]
            iol_capacity = safe_get(best_iol, 'IO_Link_Ports')
            needed = ceil(iol_needed / iol_capacity)
            precio_mod = safe_get(best_iol, 'Precio')
            separate_modules.append((best_iol, needed))
            separate_cost += precio_mod * needed
            separate_count += needed

    # AI separados
    if ai_needed > 0:
        ai_mods = all_mods[all_mods['Analog_In'] > 0]
        if not ai_mods.empty:
            best_ai = ai_mods.iloc[0]
            ai_capacity = safe_get(best_ai, 'Analog_In')
            needed = ceil(ai_needed / ai_capacity)
            precio_mod = safe_get(best_ai, 'Precio')
            separate_modules.append((best_ai, needed))
            separate_cost += precio_mod * needed
            separate_count += needed

    # AO separados
    if ao_needed > 0:
        ao_mods = all_mods[all_mods['Analog_Out'] > 0]
        if not ao_mods.empty:
            best_ao = ao_mods.iloc[0]
            ao_capacity = safe_get(best_ao, 'Analog_Out')
            needed = ceil(ao_needed / ao_capacity)
            precio_mod = safe_get(best_ao, 'Precio')
            separate_modules.append((best_ao, needed))
            separate_cost += precio_mod * needed
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
    total_di_covered = sum(safe_get(mod, 'Entradas_DI') * qty for mod, qty in best_solution)
    total_do_covered = sum(safe_get(mod, 'Salidas_DO') * qty for mod, qty in best_solution)
    total_iol_covered = sum(safe_get(mod, 'IO_Link_Ports') * qty for mod, qty in best_solution)
    total_ai_covered = sum(safe_get(mod, 'Analog_In') * qty for mod, qty in best_solution)
    total_ao_covered = sum(safe_get(mod, 'Analog_Out') * qty for mod, qty in best_solution)

    if (total_di_covered < di_needed or
        total_do_covered < do_needed or
        total_iol_covered < iol_needed or
        total_ai_covered < ai_needed or
        total_ao_covered < ao_needed):
        return [], 0, (
            f"No se puede cubrir los requerimientos "
            f"(DI: {total_di_covered}/{di_needed}, "
            f"DO: {total_do_covered}/{do_needed}, "
            f"IO-Link: {total_iol_covered}/{iol_needed}, "
            f"AI: {total_ai_covered}/{ai_needed}, "
            f"AO: {total_ao_covered}/{ao_needed})"
        )

    return best_solution, best_modules_count, None

def calculate_cables_needed(familia, protocol, num_zones, num_remotos=0, total_modules=0):
    """
    Calcula los cables necesarios según la familia y configuración
    Parámetro adicional: total_modules para EXW1
    """
    cables_needed = []
    
    # Buscar cables por tipo para la familia
    com_cable = None
    alim_cable = None
    deriv_cable = None
    
    for cable in CABLES_DB:
        if familia in cable["families"]:
            if cable["kind"] == "COM" and com_cable is None:
                com_cable = cable
            elif cable["kind"] == "ALIM" and alim_cable is None:
                alim_cable = cable
            elif cable["kind"] == "DERIV" and deriv_cable is None:
                deriv_cable = cable
    
    if familia in ["EX600", "EX260"]:
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": num_zones,
                "description": f"Cable comunicación para {num_zones} cabecera(s)"
            })
        if alim_cable:
            cables_needed.append({
                "cable": alim_cable,
                "quantity": num_zones,
                "description": f"Cable alimentación para {num_zones} cabecera(s)"
            })
    
    elif familia == "EX500":
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": 1,
                "description": "Cable comunicación para gateway EX500"
            })
        if alim_cable:
            cables_needed.append({
                "cable": alim_cable,
                "quantity": 1,
                "description": "Cable alimentación para gateway EX500"
            })
        if deriv_cable:
            cables_needed.append({
                "cable": deriv_cable,
                "quantity": num_zones,
                "description": f"Cable derivación para {num_zones} zona(s)"
            })
    
    elif familia == "EXW1":
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": 1,
                "description": "Cable comunicación para maestro EXW1"
            })
        if alim_cable:
            # Para EXW1: 1 maestro + total de módulos remotos
            total_alim_needed = 1 + total_modules  # 1 maestro + todos los módulos como remotos
            cables_needed.append({
                "cable": alim_cable,
                "quantity": total_alim_needed,
                "description": f"Cable alimentación para maestro + {total_modules} remoto(s)"
            })
    
    return cables_needed

def calculate_cables_needed_simple(familia, protocol, num_zones, num_remotos=0):
    """Versión simplificada para debug"""
    cables_needed = []
    
    # Buscar cualquier cable COM para la familia
    com_cable = None
    alim_cable = None
    deriv_cable = None
    
    for cable in CABLES_DB:
        if familia in cable["families"]:
            if cable["kind"] == "COM" and com_cable is None:
                com_cable = cable
            elif cable["kind"] == "ALIM" and alim_cable is None:
                alim_cable = cable
            elif cable["kind"] == "DERIV" and deriv_cable is None:
                deriv_cable = cable
    
    # Aplicar lógica según familia
    if familia in ["EX600", "EX260"]:
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": num_zones,
                "description": f"Cable comunicación para {num_zones} cabecera(s)"
            })
        if alim_cable:
            cables_needed.append({
                "cable": alim_cable,
                "quantity": num_zones,
                "description": f"Cable alimentación para {num_zones} cabecera(s)"
            })
    
    elif familia == "EX500":
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": 1,
                "description": "Cable comunicación para gateway EX500"
            })
        if alim_cable:
            cables_needed.append({
                "cable": alim_cable,
                "quantity": 1,
                "description": "Cable alimentación para gateway EX500"
            })
        if deriv_cable:
            cables_needed.append({
                "cable": deriv_cable,
                "quantity": num_zones,
                "description": f"Cable derivación para {num_zones} zona(s)"
            })
    
    elif familia == "EXW1":
        if com_cable:
            cables_needed.append({
                "cable": com_cable,
                "quantity": 1,
                "description": "Cable comunicación para maestro EXW1"
            })
        if alim_cable:
            total_alim_needed = 1 + num_remotos
            cables_needed.append({
                "cable": alim_cable,
                "quantity": total_alim_needed,
                "description": f"Cable alimentación para maestro + {num_remotos} remoto(s)"
            })
    
    return cables_needed

def format_cables_summary(cables_needed):
    """Formatea un resumen de los cables para mostrar"""
    if not cables_needed:
        return []
        
    summary = []
    for cable_req in cables_needed:
        cable = cable_req["cable"]
        quantity = cable_req["quantity"]
        description = cable_req["description"]
        
        # Determinar tipo de cable
        tipo_cable = {
            "COM": "Comunicación",
            "ALIM": "Alimentación", 
            "DERIV": "Derivación"
        }.get(cable["kind"], cable["kind"])
        
        summary.append({
            "referencia": cable["ref"],
            "tipo": tipo_cable,
            "cantidad": quantity,
            "precio_unitario": cable["price"],
            "precio_total": cable["price"] * quantity,
            "descripcion": description
        })
    
    return summary

def enumerate_solutions_with_cables(req, df, familias_info, selected_protocol):
    """Enumera todas las soluciones posibles incluyendo cables necesarios"""
    familias_disponibles = df["Familia"].unique()
    solutions = []
    rejected_families = []

    for fam in familias_disponibles:
        fam_df = df[df["Familia"] == fam]
        
        # OBTENER INFORMACIÓN COMPLETA DE LA FAMILIA
        familia_info = familias_info.get(fam, {})
        max_mods = familia_info.get("max_modulos", 9)
        max_remotos = familia_info.get("max_remotos", 0)
        senales_por_rama = familia_info.get("senales_por_rama", 0)
        distancia_admitida = familia_info.get("distancia_admitida", float('inf'))

        rejection_reason = None
        
        if req.get('distance_m', 0) > distancia_admitida:
            rejected_families.append({
                "Familia": fam,
                "Razon": f"Distancia excede el límite ({req['distance_m']}m > {distancia_admitida}m)",
                "Modulos_necesarios": 0,
                "Limite_familia": max_mods if max_remotos == 0 else max_remotos,
                "Distancia_limite": distancia_admitida
            })
            continue
        # Buscar cabecera según protocolo
        cabecera = None
        for c in familia_info.get("cabeceras", []):
            if c["protocolo"].strip().lower() == selected_protocol.strip().lower():
                cabecera = c
                break

        if not cabecera:
            rejected_families.append({
                "Familia": fam,
                "Razon": f"No disponible para protocolo {selected_protocol}",
                "Modulos_necesarios": 0,
                "Limite_familia": max_mods
            })
            continue

        base_price = cabecera["precio"]
        base_ref   = cabecera["referencia"]

        # Calcular módulos/remotos/ramas necesarios para cada zona
        zone_modules = []
        total_modules_needed = 0
        wireless_modules = []
        has_wireless_zones = False
        total_remotos = 0  # Para contar remotos en EXW1

        for zone in req['zones']:
            zone_id = zone['zone_id']
            di_needed = zone['digital_inputs']
            do_needed = zone['digital_outputs']
            iol_needed = zone['io_link_sensors']
            ai_needed = zone['analog_inputs']
            ao_needed = zone['analog_outputs']

            zone_solution, zone_modules_count, zone_error = calculate_zone_modules(
                fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed, familia_info, fam
            )

            if zone_error:
                rejection_reason = f"Zona {zone_id}: {zone_error}"
                break

            # Separar wireless de normales y contar remotos
            zone_normal_modules = []
            zone_wireless_modules = []
            
            for mod, qty in zone_solution:
                ref = safe_get(mod, "Referencia", "")

                if str(ref).startswith("EX500") or str(ref).startswith("EXW1") or str(ref).endswith("RAMA") or str(ref).endswith("GATEWAY"):
                    zone_normal_modules.append((mod, qty))
                elif safe_get(mod, "Wireless", False):
                    has_wireless_zones = True
                    zone_wireless_modules.append((mod, qty, zone_id))
                    wireless_modules.append((mod, qty, zone_id))
                    total_remotos += qty  # Contar remotos para EXW1
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
                "Limite_familia": max_mods,
                "Distancia_limite": distancia_admitida})
            continue

        # VERIFICAR LÍMITES SEGÚN TIPO DE FAMILIA
        limite_excedido = False
        limite_descripcion = ""
        
        if max_remotos > 0:  # EXW1 - límite por remotos
            if total_modules_needed > max_remotos:
                limite_excedido = True
                limite_descripcion = f"remotos ({total_modules_needed} > {max_remotos})"
        elif senales_por_rama > 0:  # EX500 - límite por ramas
            pass
        else:  # Familias tradicionales - límite por módulos
            if total_modules_needed > max_mods:
                limite_excedido = True
                limite_descripcion = f"módulos ({total_modules_needed} > {max_mods})"

        if limite_excedido:
            rejected_families.append({
                "Familia": fam,
                "Razon": f"Excede el límite de {limite_descripcion}",
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods if max_remotos == 0 else max_remotos
            })
            continue

        # CALCULAR CABLES NECESARIOS
        # CALCULAR CABLES NECESARIOS
        cables_needed = calculate_cables_needed(fam, selected_protocol, req['num_zones'], total_remotos, total_modules_needed)
        cables_summary = format_cables_summary(cables_needed)
        cables_total_price = sum(item["precio_total"] for item in cables_summary)

        # Wireless: añadir cabecera maestra
        if has_wireless_zones:
            wireless_master_modules = 1
            total_modules_needed += wireless_master_modules
        else:
            wireless_master_modules = 0

        # Calcular precio total y componentes (INCLUYENDO CABLES)
        if has_wireless_zones:
            wireless_master_ref = f"{fam}-GATEWAY"
            wireless_master_price = base_price
            price = wireless_master_price
            components = [(base_ref, 1)]
        else:
            if senales_por_rama > 0 or max_remotos > 0:
                num_headers_needed = 1
            else:
                num_headers_needed = req['num_zones']
            
            price = base_price * num_headers_needed
            components = [(base_ref, num_headers_needed)]

        # Agregar módulos/remotos/ramas normales
        module_totals = {}
        for zone_data in zone_modules:
            for mod, qty in zone_data['modules']:
                ref = safe_get(mod, 'Referencia')
                if ref in module_totals:
                    module_totals[ref]['quantity'] += qty
                else:
                    module_totals[ref] = {
                        'module': mod,
                        'quantity': qty
                    }

        # Agregar wireless
        wireless_components = {}
        for mod, qty, zone_id in wireless_modules:
            ref = safe_get(mod, 'Referencia')
            if ref in wireless_components:
                wireless_components[ref]['quantity'] += qty
                wireless_components[ref]['zones'].append(zone_id)
            else:
                wireless_components[ref] = {
                    'module': mod,
                    'quantity': qty,
                    'zones': [zone_id]
                }

        # Sumar precios de módulos
        for ref, data in module_totals.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += safe_get(mod, 'Precio') * qty

        for ref, data in wireless_components.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += safe_get(mod, 'Precio') * qty

        # AÑADIR CABLES A COMPONENTES Y PRECIO
        for cable_item in cables_summary:
            components.append((cable_item["referencia"], cable_item["cantidad"]))
        
        price += cables_total_price

        solutions.append({
            "Familia": fam,
            "Precio_total": round(price, 2),
            "Precio_modulos": round(price - cables_total_price, 2),
            "Precio_cables": round(cables_total_price, 2),
            "Componentes": components,
            "Cables_detalle": cables_summary,
            "Modulos_totales": total_modules_needed,
            "Distribucion_zonas": zone_modules,
            "Wireless_modules": wireless_components,
            "Has_wireless": has_wireless_zones,
            "Tipo_familia": "Remotos" if max_remotos > 0 else ("Ramas" if senales_por_rama > 0 else "Módulos"),
            "Distancia_admitida": distancia_admitida
        })

    solutions.sort(key=lambda s: s["Precio_total"])
    return solutions, rejected_families

def enumerate_solutions(req, df, familias_info, selected_protocol):
    """Enumera todas las soluciones posibles para cada familia considerando zonas individuales y el protocolo elegido"""
    familias_disponibles = df["Familia"].unique()
    solutions = []
    rejected_families = []

    for fam in familias_disponibles:
        fam_df = df[df["Familia"] == fam]
        
        # OBTENER INFORMACIÓN COMPLETA DE LA FAMILIA
        familia_info = familias_info.get(fam, {})
        max_mods = familia_info.get("max_modulos", 9)
        max_remotos = familia_info.get("max_remotos", 0)
        senales_por_rama = familia_info.get("senales_por_rama", 0)

        rejection_reason = None

        # Buscar cabecera según protocolo
        cabecera = None
        for c in familia_info.get("cabeceras", []):
            if c["protocolo"].strip().lower() == selected_protocol.strip().lower():
                cabecera = c
                break

        if not cabecera:
            rejected_families.append({
                "Familia": fam,
                "Razon": f"No disponible para protocolo {selected_protocol}",
                "Modulos_necesarios": 0,
                "Limite_familia": max_mods
            })
            continue

        base_price = cabecera["precio"]
        base_ref   = cabecera["referencia"]

        # Calcular módulos/remotos/ramas necesarios para cada zona
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

            # AQUÍ ESTÁ EL CAMBIO PRINCIPAL - PASAR INFORMACIÓN DE FAMILIA
            zone_solution, zone_modules_count, zone_error = calculate_zone_modules(
                fam_df, di_needed, do_needed, iol_needed, ai_needed, ao_needed, familia_info, fam
            )

            if zone_error:
                rejection_reason = f"Zona {zone_id}: {zone_error}"
                break

            # Separar wireless de normales
            zone_normal_modules = []
            zone_wireless_modules = []
            
            for mod, qty in zone_solution:
                ref = safe_get(mod, "Referencia", "")

                # Si es un módulo "virtual" de EX500 o EXW1 lo tratamos como normal
                if str(ref).startswith("EX500") or str(ref).startswith("EXW1") or str(ref).endswith("RAMA") or str(ref).endswith("GATEWAY"):
                    zone_normal_modules.append((mod, qty))
                elif safe_get(mod, "Wireless", False):
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

        # VERIFICAR LÍMITES SEGÚN TIPO DE FAMILIA
        limite_excedido = False
        limite_descripcion = ""
        
        if max_remotos > 0:  # EXW1 - límite por remotos
            if total_modules_needed > max_remotos:
                limite_excedido = True
                limite_descripcion = f"remotos ({total_modules_needed} > {max_remotos})"
        elif senales_por_rama > 0:  # EX500 - límite por ramas (implícito en el cálculo)
            # Para EX500 el límite se maneja dentro de calculate_ramas
            pass
        else:  # Familias tradicionales - límite por módulos
            if total_modules_needed > max_mods:
                limite_excedido = True
                limite_descripcion = f"módulos ({total_modules_needed} > {max_mods})"

        if limite_excedido:
            rejected_families.append({
                "Familia": fam,
                "Razon": f"Excede el límite de {limite_descripcion}",
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods if max_remotos == 0 else max_remotos
            })
            continue

        # Wireless: añadir cabecera maestra
        if has_wireless_zones:
            wireless_master_modules = 1
            total_modules_needed += wireless_master_modules
        else:
            wireless_master_modules = 0

        # Calcular precio total y componentes
        if has_wireless_zones:
            # PARA EXW1: Una cabecera maestra + los remotos reales
            wireless_master_ref = f"{fam}-GATEWAY"  # Cambiar nombre
            wireless_master_price = base_price  # Usar precio de cabecera real
            price = wireless_master_price
            components = [(base_ref, 1)]  # Usar referencia real de cabecera, no ficticia
        else:
            # PARA EX500 Y OTRAS FAMILIAS
            if senales_por_rama > 0 or max_remotos > 0:
                # Una sola cabecera para toda la instalación
                num_headers_needed = 1
            else:
                # Familias tradicionales: una cabecera por zona
                num_headers_needed = req['num_zones']
            
            price = base_price * num_headers_needed
            components = [(base_ref, num_headers_needed)]

        # Agregar módulos/remotos/ramas normales
        module_totals = {}
        for zone_data in zone_modules:
            for mod, qty in zone_data['modules']:
                ref = safe_get(mod, 'Referencia')
                if ref in module_totals:
                    module_totals[ref]['quantity'] += qty
                else:
                    module_totals[ref] = {
                        'module': mod,
                        'quantity': qty
                    }

        # Agregar wireless
        wireless_components = {}
        for mod, qty, zone_id in wireless_modules:
            ref = safe_get(mod, 'Referencia')
            if ref in wireless_components:
                wireless_components[ref]['quantity'] += qty
                wireless_components[ref]['zones'].append(zone_id)
            else:
                wireless_components[ref] = {
                    'module': mod,
                    'quantity': qty,
                    'zones': [zone_id]
                }

        # Sumar precios
        for ref, data in module_totals.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += safe_get(mod, 'Precio') * qty

        for ref, data in wireless_components.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += safe_get(mod, 'Precio') * qty

        solutions.append({
            "Familia": fam,
            "Precio_total": round(price, 2),
            "Componentes": components,
            "Modulos_totales": total_modules_needed,
            "Distribucion_zonas": zone_modules,
            "Wireless_modules": wireless_components,
            "Has_wireless": has_wireless_zones,
            "Tipo_familia": "Remotos" if max_remotos > 0 else ("Ramas" if senales_por_rama > 0 else "Módulos")
        })

    solutions.sort(key=lambda s: s["Precio_total"])
    return solutions, rejected_families

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
        report_lines.append(f"  Configuración Wireless: Sí (1 cabecera maestra)")
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
    for ref, qty in solution['Componentes']:
        report_lines.append(f"    {ref:<28} x{qty:>3}")

    report_lines.append("")
    report_lines.append("-" * 50)
    report_lines.append(f"{'TOTAL:':<37} {solution['Precio_total']:>8.2f}€")
    report_lines.append("")

    if len(req['zones']) > 1:
        report_lines.append("DISTRIBUCIÓN POR ZONAS:")
        for zone_data in solution['Distribucion_zonas']:
            zone_id = zone_data['zone_id']
            zone_modules = zone_data['modules']
            zone_wireless = zone_data.get('wireless_modules', [])
            
            normal_count = sum(qty for mod, qty in zone_modules)
            wireless_count = sum(qty for mod, qty, _ in zone_wireless) if zone_wireless else 0
            total_zone_count = normal_count + wireless_count

            report_lines.append(f"  Zona {zone_id} ({total_zone_count} módulos totales):")
            
            if zone_modules:
                for mod, qty in zone_modules:
                    report_lines.append(f"    - {mod['Referencia']} x{qty}")
            
            if zone_wireless:
                for mod, qty, _ in zone_wireless:
                    report_lines.append(f"    - {mod['Referencia']} x{qty}")
            
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

def get_counter(file_path="counter.txt"):
    """Lee el contador actual sin incrementarlo"""
    import os
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                count = int(f.read().strip())
            except ValueError:
                count = 0
    else:
        count = 0
    return count

def update_counter(file_path="counter.txt"):
    """Actualiza el contador de visitas"""
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

def show_footer():
    """Muestra el pie de página con el contador de visitas"""
    st.markdown("---")
    
    # Obtener el contador actual
    total_visits = get_counter()
    
    # Mostrar el pie de página
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; font-size: 12px; padding: 10px;'>
            <p>Calculador SMC - Visitas totales: {total_visits}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

def login():
    st.title("🔐 Acceso al Calculador SMC")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar", type="primary"):
            # Usar el sistema de autenticación original con múltiples usuarios
            if username in VALID_PASSWORDS and VALID_PASSWORDS[username] == password:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.session_state.login_success = True
                
                # Contar visita si es la primera vez en esta sesión
                if 'has_counted_login' not in st.session_state:
                    st.session_state['has_counted_login'] = True
                    visitas = update_counter()
                    st.success(f"✅ Bienvenido {username}. Esta app se ha usado {visitas} veces.")
                else:
                    st.success(f"¡Bienvenido {username}!")
            else:
                st.error("Usuario o contraseña incorrectos")
            show_footer()


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
            st.rerun()  # Forzar recarga de la página después del login exitoso
        return  # Detener ejecución aquí si no está autenticado

    # Sidebar con menú de navegación
    st.sidebar.title("Menú de Navegación")
    menu = st.sidebar.selectbox("Selecciona una sección:", ["Configurador", "Conversor", "Tiempo de Ciclo"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Conectado como: {st.session_state.current_user}")

    # Botón de cerrar sesión
    if st.sidebar.button("🔒 Cerrar sesión", key="logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.session_state.logout_triggered = True

    st.sidebar.markdown("---")
    if st.session_state.current_user in ["JR"]:  # Solo ciertos usuarios
        if st.sidebar.button("🔄 Resetear Contador", key="reset_counter"):
            reset_counter()
            st.sidebar.success("Contador reseteado a 0")
            st.rerun()

    # Mostrar la sección seleccionada
    if menu == "Configurador":
        mostrar_configurador()
    elif menu == "Conversor":
        mostrar_conversor()
    elif menu == "Tiempo de Ciclo":
        mostrar_tiempo_ciclo()

    # Ejecutar rerun fuera del callback del botón
    if st.session_state.logout_triggered:
        st.session_state.logout_triggered = False
        st.rerun()
    

def mostrar_configurador():

    if not check_password():
        return

    # Mostrar usuario actual
    st.sidebar.success(f"Conectado como: {st.session_state['current_user']}")

    st.title("🔧 Calculador de Soluciones SMC")
    st.markdown("**Calculador de módulos SMC con configuración por zonas**")
    
    # Subida de archivos
    st.header("1. Cargar Archivos de Configuración")

    col1, col2 = st.columns(2)

    with col1:
        catalog_file = st.file_uploader(
            "Catálogo de Módulos (Configs.xlsx)",
            type=['xlsx', 'xls'],
            help="Archivo con la información de los módulos SMC"
        )

    with col2:
        families_file = st.file_uploader(
            "Configuración de Familias (Familias.xlsx)",
            type=['xlsx', 'xls'],
            help="Archivo con los límites y protocolos de las familias"
        )

    if catalog_file and families_file:
        try:
            df, familias_info = load_catalog_with_limits_web(catalog_file, families_file)

            st.success(f"✅ Archivos cargados correctamente: {len(df)} módulos, {len(familias_info)} familias")

            # Selección de protocolo
            st.header("2. Seleccionar Protocolo de Comunicación")

            all_protocols = set()
            for familia, info in familias_info.items():
                all_protocols.update(info["protocolos"])

            selected_protocol = st.selectbox(
                "Protocolo de comunicación:",
                sorted(list(all_protocols)),
                help="Selecciona el protocolo que necesitas"
            )

            # Filtrar por protocolo
            # Crear diccionario de protocolos por familia
            fam_protocols = {familia: info["protocolos"] for familia, info in familias_info.items()}

            # Filtrar por protocolo
            df, familias_limits, compatible_families = filter_families_by_protocol(
                df, familias_info, fam_protocols, selected_protocol
            )

            if df.empty:
                st.error("❌ No hay módulos compatibles con el protocolo seleccionado")
                return

            st.info(f"✅ Familias compatibles: {', '.join(compatible_families)}")

            # Configuración de zonas
            st.header("3. Configuración de Zonas")

            num_zones = st.number_input("Número de zonas:", min_value=1, max_value=20, value=1)
            zones_equal = st.checkbox("¿Todas las zonas son iguales?")

            zones = []

            if zones_equal:
                st.subheader("Configuración para todas las zonas (iguales)")
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    di = st.number_input("Entradas digitales:", min_value=0, value=0, key="di_all")
                with col2:
                    do = st.number_input("Salidas digitales:", min_value=0, value=0, key="do_all")
                with col3:
                    iol = st.number_input("Sensores IO-Link:", min_value=0, value=0, key="iol_all")
                with col4:
                    ai = st.number_input("Entradas analógicas:", min_value=0, value=0, key="ai_all")
                with col5:
                    ao = st.number_input("Salidas analógicas:", min_value=0, value=0, key="ao_all")

                for i in range(num_zones):
                    zones.append({
                        'zone_id': i + 1,
                        'digital_inputs': di,
                        'digital_outputs': do,
                        'io_link_sensors': iol,
                        'analog_inputs': ai,
                        'analog_outputs': ao
                    })

            else:
                st.subheader("Configuración individual por zona")

                for i in range(num_zones):
                    st.write(f"**Zona {i+1}**")
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        di = st.number_input("DI:", min_value=0, value=0, key=f"di_{i}")
                    with col2:
                        do = st.number_input("DO:", min_value=0, value=0, key=f"do_{i}")
                    with col3:
                        iol = st.number_input("IO-Link:", min_value=0, value=0, key=f"iol_{i}")
                    with col4:
                        ai = st.number_input("AI:", min_value=0, value=0, key=f"ai_{i}")
                    with col5:
                        ao = st.number_input("AO:", min_value=0, value=0, key=f"ao_{i}")

                    zones.append({
                        'zone_id': i + 1,
                        'digital_inputs': di,
                        'digital_outputs': do,
                        'io_link_sensors': iol,
                        'analog_inputs': ai,
                        'analog_outputs': ao
                    })

            # Parámetros adicionales
            st.header("4. Parámetros Adicionales")

            col1, col2 = st.columns(2)
            with col1:
                distance_m = st.number_input("Distancia máxima entre zonas (m):", min_value=0.0, value=10.0)
            with col2:
                connector_type = st.selectbox(
                    "Tipo de conector:",
                    ["", "M8", "M12", "mixto"],
                    help="Deja vacío si es indiferente"
                )

            # Preparar requerimientos
            req = {
                "zones": zones,
                "num_zones": num_zones,
                "zones_equal": zones_equal,
                "distance_m": distance_m,
                "connector_type": connector_type,
                "total_digital_inputs": sum(zone['digital_inputs'] for zone in zones),
                "total_digital_outputs": sum(zone['digital_outputs'] for zone in zones),
                "total_io_link_sensors": sum(zone['io_link_sensors'] for zone in zones),
                "total_analog_inputs": sum(zone['analog_inputs'] for zone in zones),
                "total_analog_outputs": sum(zone['analog_outputs'] for zone in zones),
            }

            req["total_inputs"] = req["total_digital_inputs"] + req["total_io_link_sensors"] + req["total_analog_inputs"]
            req["total_outputs"] = req["total_digital_outputs"] + req["total_analog_outputs"]

            # Mostrar resumen
            st.header("5. Resumen de Configuración")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Configuración de Zonas:**")
                st.write(f"- Número de zonas: {req['num_zones']}")
                st.write(f"- Zonas iguales: {'Sí' if req['zones_equal'] else 'No'}")
                st.write(f"- Distancia máxima: {req['distance_m']} m")
                if connector_type:
                    st.write(f"- Tipo de conector: {connector_type}")

            with col2:
                st.write("**Totales:**")
                st.write(f"- Entradas digitales: {req['total_digital_inputs']}")
                st.write(f"- Salidas digitales: {req['total_digital_outputs']}")
                st.write(f"- Sensores IO-Link: {req['total_io_link_sensors']}")
                st.write(f"- Entradas analógicas: {req['total_analog_inputs']}")
                st.write(f"- Salidas analógicas: {req['total_analog_outputs']}")

            # Detalles por zona si hay más de una
            if req['num_zones'] > 1:
                st.write("**Detalle por zona:**")
                zone_data = []
                for zone in zones:
                    zone_data.append({
                        "Zona": zone['zone_id'],
                        "DI": zone['digital_inputs'],
                        "DO": zone['digital_outputs'],
                        "IO-Link": zone['io_link_sensors'],
                        "AI": zone['analog_inputs'],
                        "AO": zone['analog_outputs']
                    })
                st.dataframe(pd.DataFrame(zone_data), hide_index=True)

            # Botón para calcular
            if st.button("🔍 Calcular Soluciones", type="primary"):
                # Verificar que hay algo que calcular
                if req["total_inputs"] == 0 and req["total_outputs"] == 0:
                    st.warning("⚠️ Debes especificar al menos una entrada o salida para calcular")
                    return

                with st.spinner("Calculando soluciones..."):
                    # Enumerar soluciones con protocolo seleccionado
                    solutions, rejected_families = enumerate_solutions_with_cables(req, df, familias_info, selected_protocol)

                    if not solutions:
                        st.error("❌ No se encontraron soluciones válidas")


                # Mostrar resultados
                st.header("6. Soluciones Encontradas")
                st.success(f"✅ Se encontraron {len(solutions)} solución(es)")

                # Mostrar las mejores 3 soluciones
                for i, sol in enumerate(solutions[:3]):
                    with st.expander(f"Solución {i+1}: {sol['Familia']} - {sol['Precio_total']}€", expanded=(i==0)):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Información General:**")
                            st.write(f"- Familia: {sol['Familia']}")
                            st.write(f"- Precio Total: {sol['Precio_total']}€")
                            st.write(f"  - Módulos: {sol['Precio_modulos']}€")
                            st.write(f"  - Cables: {sol['Precio_cables']}€")
                            st.write(f"- Módulos Totales: {sol['Modulos_totales']}")
                            st.write(f"- Protocolo: {selected_protocol}")

                        with col2:
                            st.write("**Componentes:**")
                            for ref, qty in sol['Componentes']:
                                st.write(f"- {ref} x{qty}")

                        if sol['Cables_detalle']:
                            st.write("**Detalle de Cables:**")
                            cables_df = pd.DataFrame(sol['Cables_detalle'])
                            st.dataframe(cables_df, hide_index=True)

                        # Distribución por zonas si hay más de una
                        if req['num_zones'] > 1:
                            st.write("**Distribución por zonas:**")
                            for zone_data in sol['Distribucion_zonas']:
                                zone_id = zone_data['zone_id']
                                zone_modules = zone_data['modules']
                                zone_count = zone_data['modules_count']

                                st.write(f"Zona {zone_id} ({zone_count} módulos):")
                                for mod, qty in zone_modules:
                                    st.write(f"  - {mod['Referencia']} x{qty}")

                        # Botón para generar reporte
                        if st.button(f"📄 Generar Reporte", key=f"report_{i}"):
                            report = generate_solution_report(req, sol, selected_protocol)

                            # Crear archivo de descarga
                            report_bytes = report.encode('utf-8')
                            filename = f"smc_solution_{sol['Familia'].lower()}_{int(sol['Precio_total'])}.txt"

                            st.download_button(
                                label="💾 Descargar Reporte",
                                data=report_bytes,
                                file_name=filename,
                                mime="text/plain",
                                key=f"download_{i}"
                            )

                # Mostrar familias rechazadas si las hay
                if rejected_families:
                    st.subheader("Familias descartadas:")
                    rejected_df = pd.DataFrame(rejected_families)
                    st.dataframe(rejected_df, hide_index=True)

        except Exception as e:
            st.error(f"❌ Error al procesar los archivos: {str(e)}")
            st.write("Por favor, verifica que los archivos tienen el formato correcto.")

    else:
        st.info("👆 Por favor, carga ambos archivos (Catálogo de Módulos y Configuración de Familias) para continuar.")

    show_footer()

def mostrar_conversor():
    st.title("🔄 Conversor Fuerza-Par")

    st.subheader("Conversión Fuerza → Par")
    M = st.number_input("Par de entrada (Nm)", value=2.28)
    p = st.number_input("Paso (mm)", value=3.3)
    eta = st.number_input("Rendimiento mecánico", value=0.9)
    F = (2 * 3.1416 * eta * M) / p
    st.write(f"Fuerza disponible: {F:.1f} N")

    st.subheader("Conversión Par → Fuerza")
    F2 = st.number_input("Fuerza (N)", value=800)
    p2 = st.number_input("Paso (mm)", value=4.0)
    eta2 = st.number_input("Rendimiento mecánico", value=0.8)
    M2 = (p2 * F2) / (2 * 3.1416 * eta2)
    st.write(f"Par necesario: {M2:.3f} Nm")
    show_footer()

def calcular_tc(v, a, recorrido, t_est):
    t_acc = v / a
    d_acc = 0.5 * a * t_acc**2
    if 2 * d_acc >= recorrido:
        t_acc = (recorrido / 2 / a)**0.5
        tc = 2 * t_acc + t_est
    else:
        d_const = recorrido - 2 * d_acc
        t_const = d_const / v
        tc = 2 * t_acc + t_const + t_est
    return tc

def reset_counter(file_path="counter.txt"):
    """Resetea el contador a 0"""
    with open(file_path, "w") as f:
        f.write("0")
    return 0

def mostrar_tiempo_ciclo():
    st.title("⏱️ Tiempo de Ciclo")

    # Parámetros comunes
    st.subheader("Parámetros Comunes")
    col1, col2 = st.columns(2)
    
    with col1:
        recorrido = st.number_input("Recorrido (mm)", value=1000.0)
    with col2:
        t_est = st.number_input("Tiempo estabilizado (s)", value=0.05)

    st.markdown("---")
    st.subheader("Cálculos de Tiempo de Ciclo")

    # Crear 3 columnas para diferentes cálculos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Cálculo 1**")
        velocidad1 = st.number_input("Velocidad (mm/s)", value=1500.0, key="v1")
        aceleracion1 = st.number_input("Aceleración (mm/s²)", value=2500.0, key="a1")
        tc1 = calcular_tc(velocidad1, aceleracion1, recorrido, t_est)
        st.metric("Tiempo de Ciclo", f"{tc1:.4f} s")

    with col2:
        st.markdown("**Cálculo 2**")
        velocidad2 = st.number_input("Velocidad (mm/s)", value=2000.0, key="v2")
        aceleracion2 = st.number_input("Aceleración (mm/s²)", value=3000.0, key="a2")
        tc2 = calcular_tc(velocidad2, aceleracion2, recorrido, t_est)
        st.metric("Tiempo de Ciclo", f"{tc2:.4f} s")

    with col3:
        st.markdown("**Cálculo 3**")
        velocidad3 = st.number_input("Velocidad (mm/s)", value=2500.0, key="v3")
        aceleracion3 = st.number_input("Aceleración (mm/s²)", value=4000.0, key="a3")
        tc3 = calcular_tc(velocidad3, aceleracion3, recorrido, t_est)
        st.metric("Tiempo de Ciclo", f"{tc3:.4f} s")

    # Mostrar comparación
    st.markdown("---")
    st.subheader("Comparación de Resultados")
    
    # Crear DataFrame para mostrar comparación
    comparison_data = {
        "Cálculo": ["Cálculo 1", "Cálculo 2", "Cálculo 3"],
        "Velocidad (mm/s)": [velocidad1, velocidad2, velocidad3],
        "Aceleración (mm/s²)": [aceleracion1, aceleracion2, aceleracion3],
        "Tiempo de Ciclo (s)": [f"{tc1:.4f}", f"{tc2:.4f}", f"{tc3:.4f}"]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, hide_index=True)
    
    # Mostrar el mejor resultado
    tiempos = [tc1, tc2, tc3]
    mejor_idx = tiempos.index(min(tiempos))
    st.success(f"🏆 Mejor resultado: {comparison_data['Cálculo'][mejor_idx]} con {min(tiempos):.4f} segundos")
    
    st.markdown("---")
    st.subheader("📈 Perfiles de Recorrido")
    
    fig, ax = plt.subplots()
    for v, a, label in [(velocidad1, aceleracion1, "Cálculo 1"),
                        (velocidad2, aceleracion2, "Cálculo 2"),
                        (velocidad3, aceleracion3, "Cálculo 3")]:
        t, pos = generar_perfil(recorrido, v, a)
        ax.plot(t, pos, label=label)
    
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Recorrido (mm)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
    

    show_footer()

def generar_perfil(recorrido, velocidad_max, aceleracion):  
    """
    Genera el perfil de velocidad trapezoidal o triangular (velocidad vs tiempo)
    """
    t_acc = velocidad_max / aceleracion
    d_acc = 0.5 * aceleracion * t_acc**2

    if 2 * d_acc >= recorrido:
        # Perfil triangular
        t_acc = np.sqrt(recorrido / aceleracion)
        t_total = 2 * t_acc
        v_peak = aceleracion * t_acc

        t = np.linspace(0, t_total, 300)
        vel = np.zeros_like(t)

        for i, ti in enumerate(t):
            if ti <= t_acc:
                vel[i] = aceleracion * ti
            else:
                vel[i] = v_peak - aceleracion * (ti - t_acc)
    else:
        # Perfil trapezoidal
        d_const = recorrido - 2 * d_acc
        t_const = d_const / velocidad_max
        t_total = 2 * t_acc + t_const
        t = np.linspace(0, t_total, 300)
        vel = np.zeros_like(t)

        for i, ti in enumerate(t):
            if ti <= t_acc:
                vel[i] = aceleracion * ti
            elif ti <= t_acc + t_const:
                vel[i] = velocidad_max
            else:
                vel[i] = velocidad_max - aceleracion * (ti - t_acc - t_const)

    return t, vel



if __name__ == "__main__":
    main()
       